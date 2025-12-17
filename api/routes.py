from fastapi import APIRouter, HTTPException, BackgroundTasks
from .database import get_db_connection
from .forecast import generate_forecast
from .clustering import perform_clustering
from .elasticity import calculate_elasticity
from .bundles import calculate_bundles
import pandas as pd
import threading
import time
import sys
import os
import traceback

router = APIRouter()

# Lista de tabelas consolidadas (Limpas)
TABLES_LIMPAS = [
    'amazon_consolidado', 
    'shopee_consolidado', 
    'mercado_livre_consolidado', 
    'magalu_consolidado', 
    'madeira_consolidado', 
    'olist_consolidado',
    'amazon_novoon',
    'shopee_novoon',
    'mercado_livre_novoon',
    'magalu_novoon',
    'madeira_novoon',
    'olist_novoon'
]

# Lista de tabelas conciliadas (Atom)
TABLES_ATOM = [
    'amazon_conciliado', 
    'shopee_conciliado', 
    'mercado_livre_conciliado', 
    'magalu_conciliado', 
    'madeira_conciliado', 
    'olist_conciliado'
]

# Cache global simples (Dicionário por empresa)
_cache_dfs = {} # {'animoshop': df, 'novoon': df}
_last_cache_times = {}
_cache_lock = threading.Lock()
CACHE_DURATION = 300  # 5 minutos

def get_all_sales_data(company='animoshop', force_refresh=False):
    """Lê todas as tabelas de vendas e retorna um DataFrame único. Com Cache e Lock por empresa."""
    global _cache_dfs, _last_cache_times
    
    company = company.lower()
    
    # Verificação rápida sem lock
    if not force_refresh and company in _cache_dfs and (time.time() - _last_cache_times.get(company, 0) < CACHE_DURATION):
        return _cache_dfs[company]

    with _cache_lock:
        # Verificação dupla
        if not force_refresh and company in _cache_dfs and (time.time() - _last_cache_times.get(company, 0) < CACHE_DURATION):
            return _cache_dfs[company]

        try:
            conn = get_db_connection(company)
        except Exception as e:
            print(f"Erro ao conectar no banco {company}: {e}")
            traceback.print_exc()
            return pd.DataFrame()

        dfs = []
        
        # Descobre tabelas existentes no banco para não falhar com lista fixa
        try:
            tables_in_db = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)['name'].tolist()
        except Exception as e:
            print(f"Error listing tables: {e}")
            tables_in_db = []

        # Lê tabelas (Tenta ler tudo que parece tabela de vendas)
        # --- LÓGICA DE PRIORIDADE ---
        # Se existir 'novoon_consolidado_geral', usamos ELA e ignoramos as individuais _novoon
        # Se existir 'novoon_conciliado_geral', usamos ELA e ignoramos as individuais _conciliado
        
        has_consolidado_geral = 'novoon_consolidado_geral' in tables_in_db
        has_conciliado_geral = 'novoon_conciliado_geral' in tables_in_db
        
        for table in tables_in_db:
            is_limpa = table.endswith('_consolidado') or table.endswith('_novoon') or table == 'novoon_consolidado_geral'
            is_atom = table.endswith('_conciliado') or table == 'novoon_conciliado_geral'
            
            # Pular individuais se tivermos a geral (para evitar duplicidade)
            if company == 'novoon':
                if has_consolidado_geral and is_limpa and table != 'novoon_consolidado_geral':
                    continue
                if has_conciliado_geral and is_atom and table != 'novoon_conciliado_geral':
                    continue
            
            if is_limpa or is_atom:
                try:
                    query = f"SELECT * FROM {table}"
                    df = pd.read_sql_query(query, conn)
                    
                    # Normaliza MarketPlace
                    if 'MarketPlace' not in df.columns:
                        name_clean = table.replace('_consolidado', '').replace('_novoon', '').replace('_conciliado', '').replace('_geral', '').replace('_', ' ').title()
                        df['MarketPlace'] = name_clean
                    
                    if 'contagem_pedidos' not in df.columns:
                        df['contagem_pedidos'] = 1

                    df['fonte_dados'] = 'atom' if is_atom else 'limpas'
                    dfs.append(df)
                except Exception as e:
                    print(f"Erro ao ler tabela {table}: {e}")
                    continue
                
        conn.close()
        
        if not dfs:
            _cache_dfs[company] = pd.DataFrame()
        else:
            full_df = pd.concat(dfs, ignore_index=True)
            
            # --- OTIMIZAÇÃO: Pré-processamento no carregamento ---
            # 1. Datas para Filtro
            meses_ordem = {
                'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
                'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
            }
            
            if 'dia' in full_df.columns and 'mes' in full_df.columns and 'ano' in full_df.columns:
                try:
                    full_df['mes_num_filtro'] = full_df['mes'].map(meses_ordem).fillna(0).astype(int)
                    full_df['data_filtro'] = pd.to_datetime(dict(year=full_df['ano'], month=full_df['mes_num_filtro'], day=full_df['dia']), errors='coerce')
                except Exception as e:
                    print(f"Error processing dates: {e}")
            else:
                pass # Date columns missing
            
            # 2. Normalização de UF (Geo)
            col_uf = None
            for col in ['UF', 'uf', 'Estado', 'estado']:
                if col in full_df.columns:
                    col_uf = col
                    break
            
            if col_uf:
                # Mapa de Estados para UF
                estado_para_uf = {
                    'ACRE': 'AC', 'ALAGOAS': 'AL', 'AMAZONAS': 'AM', 'AMAPA': 'AP', 'AMAPÁ': 'AP',
                    'BAHIA': 'BA', 'CEARA': 'CE', 'CEARÁ': 'CE', 'DISTRITO FEDERAL': 'DF',
                    'ESPIRITO SANTO': 'ES', 'ESPÍRITO SANTO': 'ES', 'GOIAS': 'GO', 'GOIÁS': 'GO',
                    'MARANHAO': 'MA', 'MARANHÃO': 'MA', 'MATO GROSSO': 'MT', 'MATO GROSSO DO SUL': 'MS',
                    'MINAS GERAIS': 'MG', 'PARA': 'PA', 'PARÁ': 'PA', 'PARAIBA': 'PB', 'PARAÍBA': 'PB',
                    'PARANA': 'PR', 'PARANÁ': 'PR', 'PERNAMBUCO': 'PE', 'PIAUI': 'PI', 'PIAUÍ': 'PI',
                    'RIO DE JANEIRO': 'RJ', 'RIO GRANDE DO NORTE': 'RN', 'RIO GRANDE DO SUL': 'RS',
                    'RONDONIA': 'RO', 'RONDÔNIA': 'RO', 'RORAIMA': 'RR', 'SANTA CATARINA': 'SC',
                    'SAO PAULO': 'SP', 'SÃO PAULO': 'SP', 'SERGIPE': 'SE', 'TOCANTINS': 'TO'
                }
                
                def normalize_uf(val):
                    val_str = str(val).upper().strip()
                    if len(val_str) == 2:
                        return val_str
                    return estado_para_uf.get(val_str, val_str)

                full_df['uf_norm'] = full_df[col_uf].apply(normalize_uf)
            else:
                full_df['uf_norm'] = None

            _cache_dfs[company] = full_df

        _last_cache_times[company] = time.time()
        return _cache_dfs[company]

def filter_data(df, start_date=None, end_date=None, source=None, marketplace=None):
    """Filtra o DataFrame por intervalo de datas, fonte de dados e marketplace."""
    if df.empty:
        return df

    mask = pd.Series(True, index=df.index)

    # Filtro de Fonte (Atom vs Limpas)
    if source:
        mask &= (df['fonte_dados'] == source)

    # Filtro de Marketplace
    if marketplace:
        mask &= (df['MarketPlace'].str.lower() == marketplace.lower())

    # Filtro de Data (Usa colunas pré-processadas)
    if (start_date or end_date) and 'data_filtro' in df.columns:
        if start_date:
            mask &= (df['data_filtro'] >= pd.to_datetime(start_date))
        if end_date:
            mask &= (df['data_filtro'] <= pd.to_datetime(end_date))
        
    return df[mask]

@router.get("/resumo")
def get_resumo_geral(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    try:
        from datetime import datetime, timedelta

        df = get_all_sales_data(company)
        
        # 1. Dados Atuais
        df_current = filter_data(df, start_date, end_date, source, marketplace)
        
        # Helper para métricas
        def calculate_metrics(dframe):
            if dframe.empty:
                return {
                    "faturamento_total": 0.0,
                    "lucro_liquido_total": 0.0,
                    "frete_total": 0.0,
                    "comissoes_total": 0.0,
                    "total_pedidos": 0,
                    "ticket_medio": 0.0,
                    "custo_total": 0.0
                }
            return {
                "faturamento_total": float(dframe['faturamento'].sum()),
                "lucro_liquido_total": float(dframe['lucro_liquido'].sum()),
                "frete_total": abs(float(dframe['frete'].sum())) if 'frete' in dframe.columns else 0.0,
                "comissoes_total": abs(float(dframe['comissoes'].sum())) if 'comissoes' in dframe.columns else 0.0,
                "total_pedidos": int(dframe['contagem_pedidos'].sum()) if 'contagem_pedidos' in dframe.columns else len(dframe),
                "ticket_medio": float(dframe['faturamento'].mean()) if not dframe.empty else 0.0,
                "custo_total": float(dframe['faturamento'].sum() - dframe['lucro_liquido'].sum())
            }

        metrics_current = calculate_metrics(df_current)

        # 2. Dados Anteriores (Comparação)
        comparisons = {}
        if start_date and end_date:
            try:
                fmt = "%Y-%m-%d"
                s_date = datetime.strptime(start_date, fmt)
                e_date = datetime.strptime(end_date, fmt)
                duration = e_date - s_date
                
                # Período anterior: termina 1 dia antes do inicio atual e tem a mesma duração
                prev_end = s_date - timedelta(days=1)
                prev_start = prev_end - duration
                
                prev_start_str = prev_start.strftime(fmt)
                prev_end_str = prev_end.strftime(fmt)
                
                df_prev = filter_data(df, prev_start_str, prev_end_str, source, marketplace)
                metrics_prev = calculate_metrics(df_prev)
                
                # Calcula variação percentual
                def calc_pct(curr, prev):
                    if prev == 0: return 0.0 if curr == 0 else 100.0
                    return ((curr - prev) / prev) * 100.0

                comparisons = {
                    "faturamento_pct": calc_pct(metrics_current["faturamento_total"], metrics_prev["faturamento_total"]),
                    "lucro_pct": calc_pct(metrics_current["lucro_liquido_total"], metrics_prev["lucro_liquido_total"]),
                    "pedidos_pct": calc_pct(metrics_current["total_pedidos"], metrics_prev["total_pedidos"]),
                    "ticket_pct": calc_pct(metrics_current["ticket_medio"], metrics_prev["ticket_medio"]),
                    "periodo_anterior": f"{prev_start.strftime('%d/%m')} a {prev_end.strftime('%d/%m')}"
                }
            except Exception as e:
                print(f"Erro calculo comparacao: {e}")
                comparisons = {}
        
        # Mescla métricas com comparações
        response = {**metrics_current, "comparisons": comparisons}
        return response

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/marketplace")
def get_resumo_marketplace(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    df = get_all_sales_data(company)
    df = filter_data(df, start_date, end_date, source, marketplace)
    
    if df.empty:
        return []
        
    # Agrupa por MarketPlace
    grupo = df.groupby('MarketPlace')[['faturamento', 'lucro_liquido', 'contagem_pedidos']].sum().reset_index()
    return grupo.to_dict(orient='records')

@router.get("/mensal")
def get_evolucao_mensal(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    df = get_all_sales_data(company)
    df = filter_data(df, start_date, end_date, source, marketplace)
    
    if df.empty:
        return []
        
    # Garante ordem dos meses
    meses_ordem = {
        'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
        'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
    }
    
    if 'mes' in df.columns:
        # Se mes_num_filtro já existe (pré-processado), usa ele, senão recalcula (fallback)
        if 'mes_num_filtro' in df.columns:
             df['mes_num'] = df['mes_num_filtro']
        else:
             df['mes_num'] = df['mes'].map(meses_ordem).fillna(0).astype(int)
        
        # Agrupa incluindo frete e comissoes
        cols_agg = ['faturamento', 'lucro_liquido']
        if 'frete' in df.columns: cols_agg.append('frete')
        if 'comissoes' in df.columns: cols_agg.append('comissoes')
            
        grupo = df.groupby(['ano', 'mes_num', 'mes'])[cols_agg].sum().reset_index()
        grupo = grupo.sort_values(['ano', 'mes_num'])
        
        # --- VISUALIZAÇÃO: Converter Frete e Comissões para Positivo ---
        if 'frete' in grupo.columns:
            grupo['frete'] = grupo['frete'].abs()
        if 'comissoes' in grupo.columns:
            grupo['comissoes'] = grupo['comissoes'].abs()
            
        return grupo.to_dict(orient='records')
    
    return []

@router.get("/pagamentos")
def get_metodos_pagamento(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    df = get_all_sales_data(company)
    df = filter_data(df, start_date, end_date, source, marketplace)
    
    if df.empty:
        return []

    # Tenta encontrar coluna de pagamento
    col_pagamento = None
    for col in ['Metodo de pagamento', 'metodo_pagamento', 'forma_pagamento', 'Payment Method']:
        if col in df.columns:
            col_pagamento = col
            break
            
    if not col_pagamento:
        return []

    # Agrupa por método de pagamento
    grupo = df.groupby(col_pagamento)[['faturamento', 'contagem_pedidos']].sum().reset_index()
    grupo = grupo.rename(columns={col_pagamento: 'metodo'})
    grupo = grupo.sort_values('faturamento', ascending=False)
    return grupo.to_dict(orient='records')

@router.get("/diario")
def get_evolucao_diaria(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    df = get_all_sales_data(company)
    df = filter_data(df, start_date, end_date, source, marketplace)
    if df.empty: return []

    if 'data_filtro' in df.columns:
        # Usa a data pré-processada
        grupo = df.groupby(['data_filtro', 'dia', 'mes', 'ano'])[['faturamento', 'lucro_liquido', 'contagem_pedidos']].sum().reset_index()
        grupo = grupo.sort_values('data_filtro')
        grupo['data_iso'] = grupo['data_filtro'].dt.strftime('%Y-%m-%d')
        return grupo.to_dict(orient='records')
    return []

@router.get("/semanal")
def get_evolucao_semanal(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    df = get_all_sales_data(company)
    df = filter_data(df, start_date, end_date, source, marketplace)
    if df.empty: return []

    if 'data_filtro' in df.columns:
        df['semana'] = df['data_filtro'].dt.isocalendar().week
        df['ano_iso'] = df['data_filtro'].dt.isocalendar().year
        
        grupo = df.groupby(['ano_iso', 'semana'])[['faturamento', 'lucro_liquido']].sum().reset_index()
        grupo = grupo.sort_values(['ano_iso', 'semana'])
        grupo['label'] = grupo.apply(lambda x: f"S{x['semana']}/{x['ano_iso']}", axis=1)
        return grupo.to_dict(orient='records')
    return []

@router.get("/anual")
def get_evolucao_anual(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    df = get_all_sales_data(company)
    df = filter_data(df, start_date, end_date, source, marketplace)
    if df.empty: return []

    if 'ano' in df.columns:
        grupo = df.groupby('ano')[['faturamento', 'lucro_liquido']].sum().reset_index()
        grupo = grupo.sort_values('ano')
        return grupo.to_dict(orient='records')
    return []

@router.get("/produtos/top")
def get_top_produtos(limit: int = 10, start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, sort_by: str = 'faturamento', company: str = 'animoshop'):
    df = get_all_sales_data(company)
    df = filter_data(df, start_date, end_date, source, marketplace)
    
    if df.empty:
        return []
        
    if 'produto' in df.columns:
        grupo = df.groupby('produto')[['faturamento', 'contagem_pedidos']].sum().reset_index()
        col_sort = 'faturamento'
        if sort_by == 'quantidade':
            col_sort = 'contagem_pedidos'
        grupo = grupo.sort_values(col_sort, ascending=False).head(limit)
        return grupo.to_dict(orient='records')
    return []

@router.get("/geo")
def get_vendas_geo(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    df = get_all_sales_data(company)
    df = filter_data(df, start_date, end_date, source, marketplace)
    
    if df.empty:
        return []

    # Usa UF normalizada pré-processada
    if 'uf_norm' in df.columns:
        # Prepara colunas para agregação
        cols_agg = {
            'faturamento': 'sum',
            'contagem_pedidos': 'sum'
        }
        
        # Garante que frete existe e é positivo para cálculo de média
        if 'frete' in df.columns:
            df['frete_abs'] = df['frete'].abs()
            cols_agg['frete_abs'] = 'sum' # Somamos o total para depois dividir
            
        grupo = df.groupby('uf_norm').agg(cols_agg).reset_index()
        grupo = grupo.rename(columns={'uf_norm': 'uf'})
        
        # Calcula frete médio
        if 'frete_abs' in grupo.columns:
            grupo['frete_medio'] = grupo['frete_abs'] / grupo['contagem_pedidos']
            grupo['frete_medio'] = grupo['frete_medio'].fillna(0)
        else:
            grupo['frete_medio'] = 0.0

        # Filtra apenas UFs válidas (2 letras)
        grupo = grupo[grupo['uf'].str.len() == 2]
        return grupo.to_dict(orient='records')
    
    return []

@router.get("/forecast/sales")
def get_sales_forecast(months: int = 6, company: str = 'animoshop'):
    """Retorna dados históricos e previsão para os próximos N meses."""
    try:
        return generate_forecast(company, months)
    except Exception as e:
        print(f"Erro no forecast: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/clustering")
def get_product_clustering(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    """Retorna clusterização de produtos (K-Means) baseada em Faturamento vs Lucro."""
    try:
        return perform_clustering(start_date, end_date, source, marketplace, company)
    except Exception as e:
        print(f"Erro no clustering: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/elasticity")
def get_price_elasticity(product_name: str, company: str = 'animoshop'):
    """Calcula elasticidade de preço e preço ótimo para um produto."""
    try:
        result = calculate_elasticity(product_name, company)
        if not result:
             raise HTTPException(status_code=404, detail="Produto não encontrado ou sem dados suficientes.")
        return result
    except Exception as e:
        print(f"Erro na elasticidade: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/bundles")
def get_bundle_suggestions(min_lift: float = 1.1, min_confidence: float = 0.3, company: str = 'animoshop'):
    """Retorna sugestões de kits (Market Basket Analysis)."""
    try:
        results = calculate_bundles(company, min_lift, min_confidence)
        return results
    except ImportError:
        raise HTTPException(status_code=500, detail="Biblioteca 'mlxtend' não instalada. Execute: pip install mlxtend")
    except Exception as e:
        print(f"Erro em bundles: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Adiciona o diretório raiz ao path para importar o etl_pipeline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_etl_process(company='animoshop'):
    """Executa o processo de ETL em background."""
    try:
        print(f">>> Iniciando ETL via API para {company}...")
        
        if company == 'animoshop':
            import etl_pipeline_as as etl
        elif company == 'novoon':
            import etl_pipeline_nv as etl
        else:
            print(f"ETL não configurado para {company}")
            return

        etl.main()
        print(f">>> ETL via API finalizado com sucesso ({company}).")
        
        # Invalida o cache após ETL
        get_all_sales_data(company, force_refresh=True)
        print(f">>> Cache de dados atualizado ({company}).")
        
    except Exception as e:
        print(f"Erro no ETL via API: {e}")

@router.post("/processar")
def trigger_etl(background_tasks: BackgroundTasks, company: str = 'animoshop'):
    """Gatilho para rodar o processamento de planilhas."""
    background_tasks.add_task(run_etl_process, company)
    return {"message": f"Processamento iniciado para {company} em background."}
