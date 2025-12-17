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
import logging

# Configura logger local
logger = logging.getLogger(__name__)

router = APIRouter()

# --- SQL QUERY HELPER ---

def get_filtered_query(company='animoshop', start_date=None, end_date=None, source=None, marketplace=None):
    """
    Constrói uma query SQL (UNION ALL) filtrada para evitar carregar tudo no Pandas.
    Retorna: (query_string, conn)
    """
    company = company.lower()
    try:
        conn = get_db_connection(company)
    except Exception as e:
        logger.error(f"Erro ao conectar banco {company}: {e}")
        return None, None

    # 1. Descobre tabelas relevantes via SQLAlchemy Engine
    from sqlalchemy import inspect
    
    try:
        # Pega a engine da conexão (se for objeto de conexão SA)
        if hasattr(conn, 'engine'):
            engine = conn.engine
        else:
            # Fallback se for sqlite3 raw (não deveria acontecer com novo database.py)
            engine = conn 

        inspector = inspect(engine)
        tables_in_db = inspector.get_table_names()
    except Exception as e:
        logger.error(f"Erro ao listar tabelas no banco '{company}': {e}")
        try:
            conn.close()
        except:
            pass
        return None, None

    # Lógica de prioridade (Geral > Individuais)
    has_consolidado_geral = 'novoon_consolidado_geral' in tables_in_db
    has_conciliado_geral = 'novoon_conciliado_geral' in tables_in_db
    
    target_tables = []
    
    for table in tables_in_db:
        # Check standard names
        is_limpa = table.endswith('_consolidado') or table.endswith('_novoon') or table == 'novoon_consolidado_geral'
        is_atom = table.endswith('_conciliado') or table == 'novoon_conciliado_geral'
        
        # Pular individuais se tivermos a geral
        if company == 'novoon':
            if has_consolidado_geral and is_limpa and table != 'novoon_consolidado_geral':
                continue
            if has_conciliado_geral and is_atom and table != 'novoon_conciliado_geral':
                continue
        
        if is_limpa or is_atom:
            # Filtro de Fonte (Atom vs Limpas) na seleção de tabelas
            table_source = 'atom' if is_atom else 'limpas'
            if source and source != table_source:
                continue
            
            # Adiciona tupla (nome_tabela, fonte)
            target_tables.append((table, table_source))

    if not target_tables:
        logger.warning(f"Nenhuma tabela encontrada para {company} com os filtros atuais.")
        try:
            conn.close()
        except:
            pass
        return None, None

    # 2. Constrói a CTE (Common Table Expression) com UNION ALL
    selects = []
    for table, src in target_tables:
        part = f"SELECT *, '{src}' as fonte_dados FROM {table}"
        selects.append(part)
        
    union_query = " UNION ALL ".join(selects)
    base_query = f"WITH all_sales AS ({union_query}) SELECT * FROM all_sales WHERE 1=1"
    
    # 3. Aplica Filtros (WHERE)
    params = []
    where_clauses = ""
    
    if marketplace:
        # Case insensitive query
        where_clauses += f" AND LOWER(MarketPlace) = LOWER('{marketplace}')"
        
    if start_date and end_date:
        # Filtro de data otimizado
        where_clauses += f" AND data_filtro BETWEEN '{start_date}' AND '{end_date}'"
        
    final_query = base_query + where_clauses
    return final_query, conn


# --- ENDPOINTS REFACTORADOS PARA SQL ---

@router.get("/resumo")
def get_resumo_geral(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    try:
        from datetime import datetime, timedelta

        # 1. Query Principal
        base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
        if not base_query:
             return {"faturamento_total": 0, "comparisons": {}}

        # Agregação SQL
        agg_query = f"""
            SELECT 
                SUM(faturamento) as faturamento_total,
                SUM(lucro_liquido) as lucro_liquido_total,
                SUM(CASE WHEN frete IS NOT NULL THEN ABS(frete) ELSE 0 END) as frete_total,
                SUM(CASE WHEN comissoes IS NOT NULL THEN ABS(comissoes) ELSE 0 END) as comissoes_total,
                SUM(contagem_pedidos) as total_pedidos
            FROM ({base_query})
        """
        
        df_agg = pd.read_sql_query(agg_query, conn)
        
        curr_metrics = df_agg.iloc[0].to_dict()
        # Tratamento de NULL
        for k, v in curr_metrics.items():
            if v is None: curr_metrics[k] = 0.0
            
        curr_metrics['ticket_medio'] = curr_metrics['faturamento_total'] / curr_metrics['total_pedidos'] if curr_metrics['total_pedidos'] > 0 else 0.0
        curr_metrics['custo_total'] = curr_metrics['faturamento_total'] - curr_metrics['lucro_liquido_total']


        # 2. Comparação (Período Anterior)
        comparisons = {}
        if start_date and end_date:
            try:
                fmt = "%Y-%m-%d"
                s_date = datetime.strptime(start_date, fmt)
                e_date = datetime.strptime(end_date, fmt)
                duration = e_date - s_date
                prev_end = s_date - timedelta(days=1)
                prev_start = prev_end - duration
                
                p_start = prev_start.strftime(fmt)
                p_end = prev_end.strftime(fmt)
                
                prev_query, _ = get_filtered_query(company, p_start, p_end, source, marketplace)
                if prev_query:
                    prev_agg_query = f"""
                        SELECT 
                            SUM(faturamento) as faturamento_total,
                            SUM(lucro_liquido) as lucro_liquido_total,
                            SUM(contagem_pedidos) as total_pedidos
                        FROM ({prev_query})
                    """
                    df_prev = pd.read_sql_query(prev_agg_query, conn)
                    prev_metrics = df_prev.iloc[0].to_dict()
                    
                    # Helper %
                    def calc_pct(curr, prev):
                        prev = prev or 0.0
                        curr = curr or 0.0
                        if prev == 0: return 0.0 if curr == 0 else 100.0
                        return ((curr - prev) / prev) * 100.0

                    comparisons = {
                        "faturamento_pct": calc_pct(curr_metrics["faturamento_total"], prev_metrics.get("faturamento_total")),
                        "lucro_pct": calc_pct(curr_metrics["lucro_liquido_total"], prev_metrics.get("lucro_liquido_total")),
                        "pedidos_pct": calc_pct(curr_metrics["total_pedidos"], prev_metrics.get("total_pedidos")),
                        "periodo_anterior": f"{prev_start.strftime('%d/%m')} a {prev_end.strftime('%d/%m')}"
                    }
            except Exception as e:
                logger.warning(f"Erro calculo comparacao: {e}")
            
        conn.close()
        return {**curr_metrics, "comparisons": comparisons}

    except Exception as e:
        logger.exception("Erro critico em get_resumo_geral")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/marketplace")
def get_resumo_marketplace(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
    if not base_query: return []
    
    query = f"""
        SELECT 
            MarketPlace,
            SUM(faturamento) as faturamento,
            SUM(lucro_liquido) as lucro_liquido,
            SUM(contagem_pedidos) as contagem_pedidos
        FROM ({base_query})
        GROUP BY MarketPlace
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')

@router.get("/mensal")
def get_evolucao_mensal(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
    if not base_query: return []
    
    # Agrupa por Ano, MesNum (Ordenação) e Mes (Nome)
    query = f"""
        SELECT 
            ano, 
            mes_num_filtro as mes_num,
            mes,
            SUM(faturamento) as faturamento,
            SUM(lucro_liquido) as lucro_liquido,
            SUM(ABS(frete)) as frete,
            SUM(ABS(comissoes)) as comissoes
        FROM ({base_query})
        GROUP BY ano, mes_num_filtro, mes
        ORDER BY ano, mes_num_filtro
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')

@router.get("/pagamentos")
def get_metodos_pagamento(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
    if not base_query: return []
    
    possible_cols = ['metodo_de_pagamento', 'forma_pagamento', 'payment_method']
    col_found = 'metodo_de_pagamento' # Fallback default
    
    try:
        sample = pd.read_sql_query(f"SELECT * FROM ({base_query}) LIMIT 1", conn)
        for cand in possible_cols:
            if cand in sample.columns:
                col_found = cand
                break
    except:
        pass

    query = f"""
        SELECT 
            "{col_found}" as metodo,
            SUM(faturamento) as faturamento,
            SUM(contagem_pedidos) as contagem_pedidos
        FROM ({base_query})
        GROUP BY "{col_found}"
        ORDER BY faturamento DESC
    """
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict(orient='records')
    except Exception as e:
        conn.close()
        logger.error(f"Erro pagamentos sql: {e}")
        return []

@router.get("/diario")
def get_evolucao_diaria(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
    if not base_query: return []

    query = f"""
        SELECT 
            data_filtro,
            dia,
            mes,
            ano,
            SUM(faturamento) as faturamento,
            SUM(lucro_liquido) as lucro_liquido,
            SUM(contagem_pedidos) as contagem_pedidos
        FROM ({base_query})
        GROUP BY data_filtro
        ORDER BY data_filtro
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty and 'data_filtro' in df.columns:
        df['data_iso'] = pd.to_datetime(df['data_filtro']).dt.strftime('%Y-%m-%d')
    return df.to_dict(orient='records')

@router.get("/semanal")
def get_evolucao_semanal(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
    if not base_query: return []

    query = f"SELECT data_filtro, faturamento, lucro_liquido FROM ({base_query})"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty: return []
    
    df['data_filtro'] = pd.to_datetime(df['data_filtro'])
    df['semana'] = df['data_filtro'].dt.isocalendar().week
    df['ano_iso'] = df['data_filtro'].dt.isocalendar().year
    
    grupo = df.groupby(['ano_iso', 'semana'])[['faturamento', 'lucro_liquido']].sum().reset_index()
    grupo['label'] = grupo.apply(lambda x: f"S{x['semana']}/{x['ano_iso']}", axis=1)
    
    return grupo.to_dict(orient='records')

@router.get("/anual")
def get_evolucao_anual(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
    if not base_query: return []
    
    query = f"""
        SELECT ano, SUM(faturamento) as faturamento, SUM(lucro_liquido) as lucro_liquido
        FROM ({base_query})
        GROUP BY ano
        ORDER BY ano
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')

@router.get("/produtos/top")
def get_top_produtos(limit: int = 10, start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, sort_by: str = 'faturamento', company: str = 'animoshop'):
    base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
    if not base_query: return []
    
    order_col = 'faturamento' if sort_by == 'faturamento' else 'contagem_pedidos'
    
    query = f"""
        SELECT 
            produto,
            SUM(faturamento) as faturamento,
            SUM(contagem_pedidos) as contagem_pedidos
        FROM ({base_query})
        GROUP BY produto
        ORDER BY {order_col} DESC
        LIMIT {limit}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')

@router.get("/geo")
def get_vendas_geo(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
    if not base_query: return []
    
    query = f"""
        SELECT 
            uf_norm as uf,
            SUM(faturamento) as faturamento,
            SUM(contagem_pedidos) as contagem_pedidos,
            SUM(ABS(frete)) as frete_abs
        FROM ({base_query})
        WHERE length(uf_norm) = 2
        GROUP BY uf_norm
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df['frete_medio'] = df['frete_abs'] / df['contagem_pedidos']
        df['frete_medio'] = df['frete_medio'].fillna(0)
    
    return df.to_dict(orient='records')


# --- OUTROS ENDPOINTS (AI) ---

def get_df_for_ml(company, months=12):
    base_query, conn = get_filtered_query(company) # Traz tudo
    if not base_query: return pd.DataFrame()
    df = pd.read_sql_query(base_query, conn)
    conn.close()
    return df

@router.get("/forecast/sales")
def get_sales_forecast(months: int = 6, company: str = 'animoshop'):
    try:
        return generate_forecast(company, months) 
    except Exception as e:
        logger.error(f"Erro forecast: {e}")
        return []

@router.get("/analysis/clustering")
def get_product_clustering(start_date: str = None, end_date: str = None, source: str = None, marketplace: str = None, company: str = 'animoshop'):
    try:
        base_query, conn = get_filtered_query(company, start_date, end_date, source, marketplace)
        if not base_query: return []
        
        query = f"""
            SELECT 
                produto,
                SUM(faturamento) as faturamento,
                SUM(lucro_liquido) as lucro,
                SUM(contagem_pedidos) as quantidade
            FROM ({base_query})
            GROUP BY produto
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        from .clustering import perform_clustering_from_df
        return perform_clustering_from_df(df)
        
    except Exception as e:
        logger.error(f"Erro clustering: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/bundles")
def get_bundle_suggestions(min_lift: float = 1.1, min_confidence: float = 0.3, company: str = 'animoshop'):
    try:
        results = calculate_bundles(company, min_lift, min_confidence)
        return results
    except Exception as e:
        logger.exception("Erro em bundles")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/elasticity")
def get_price_elasticity(product_name: str, company: str = 'animoshop'):
    return calculate_elasticity(product_name, company)

# --- ETL ---

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_etl_process(company='animoshop'):
    try:
        logger.info(f"Iniciando ETL via API para {company}...")
        if company == 'animoshop':
            import etl_pipeline_as as etl
        elif company == 'novoon':
            import etl_pipeline_nv as etl
        else:
            return
        etl.main()
        logger.info(f"ETL finalizado com sucesso ({company}).")
    except Exception as e:
        logger.exception(f"Erro crítico no ETL ({company})")

@router.post("/processar")
def trigger_etl(background_tasks: BackgroundTasks, company: str = 'animoshop'):
    background_tasks.add_task(run_etl_process, company)
    return {"message": f"Processamento iniciado para {company}."}
