import pandas as pd
import os
import re

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getcwd()
PASTA_ENTRADA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas', 'Mercado Livre')
PASTA_SAIDA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas')
ARQUIVO_SAIDA = 'mercado_livre_novoon_final.csv'

MESES_MAPA = {
    'janeiro': 'Janeiro', 'fevereiro': 'Fevereiro', 'março': 'Março', 'abril': 'Abril',
    'maio': 'Maio', 'junho': 'Junho', 'julho': 'Julho', 'agosto': 'Agosto',
    'setembro': 'Setembro', 'outubro': 'Outubro', 'novembro': 'Novembro', 'dezembro': 'Dezembro'
}

def extrair_data_ml(data_str):
    """
    Extrai dia, mes, ano de '10 de janeiro de 2025'
    Retorna (dia, mes_nome, ano)
    """
    try:
        # Regex para '10 de janeiro de 2025'
        match = re.search(r'(\d+)\s+de\s+([a-zA-ZçÇ]+)\s+de\s+(\d{4})', str(data_str).lower())
        if match:
            dia = int(match.group(1))
            mes_txt = match.group(2)
            ano = int(match.group(3))
            mes_final = MESES_MAPA.get(mes_txt, 'Desconhecido')
            return dia, mes_final, ano
        return None, None, None
    except:
        return None, None, None

def processar_mercadolivre():
    print("="*80)
    print("PROCESSANDO MERCADO LIVRE NOVOON (REFACTORED)...")
    print("="*80)

    dfs = []
    if os.path.exists(PASTA_ENTRADA):
        arquivos = sorted([f for f in os.listdir(PASTA_ENTRADA) if f.endswith('.xlsx')])
        for file in arquivos:
            caminho = os.path.join(PASTA_ENTRADA, file)
            try:
                # ML usa header na linha 6 (índice 5)
                df = pd.read_excel(caminho, sheet_name=0, header=5)
                df.columns = df.columns.str.strip()
                dfs.append(df)
                print(f'✓ Lido: {file} ({len(df)} linhas)')
            except Exception as e:
                print(f"⚠ Erro em {file}: {e}")

    if not dfs:
        print("❌ Nenhum dado encontrado.")
        return

    df_full = pd.concat(dfs, ignore_index=True)

    # --- FILTRO DE STATUS (CANCELADOS E DEVOLUÇÕES) ---
    # Status que devem ser removidos da análise
    STATUS_REMOVER = [
        'Cancelada pelo comprador',
        'Pacote cancelado pelo Mercado Livre',
        'Você cancelou a venda',
        'Devolução finalizada com reembolso para o comprador',
        'Em devolução',
        'Devolvido'
    ]
    
    if 'Estado' in df_full.columns:
        qtd_antes = len(df_full)
        # Normaliza para string e minúsculo para garantir
        mask_remover = df_full['Estado'].astype(str).str.strip().isin(STATUS_REMOVER)
        df_full = df_full[~mask_remover]
        qtd_depois = len(df_full)
        print(f"ℹ️  Removidos {qtd_antes - qtd_depois} registros por Status (Cancelados/Devoluções).")
    else:
        print("⚠ Coluna 'Estado' não encontrada para filtragem.")

    # --- SELEÇÃO E RENOMEAÇÃO (ALLOWLIST) ---
    # Mapeamento: Nome Original -> Nome Novoon
    # Nota: Estado.1 geralmente é o UF do comprador no relatório do ML
    mapa_colunas = {
        'N.º de venda': 'Id do Pedido Unificado',
        'Título do anúncio': 'Produto',
        'Data da venda': 'Data Venda',
        'Cidade': 'Cidade',
        'Estado.1': 'UF', 
        'CEP': 'CEP',
        'Receita por produtos (BRL)': 'Faturamento',
        'Tarifa de venda e impostos (BRL)': 'Comissões',
        'Receita por envio (BRL)': 'temp_receita_envio',
        'Tarifas de envio (BRL)': 'temp_tarifa_envio',
        'Cancelamentos e reembolsos (BRL)': 'temp_cancelamentos',
        'Total (BRL)': 'temp_total' # Usado para validação
    }

    # Verifica quais colunas existem (para evitar erro se Estado.1 não existir)
    cols_existentes = [c for c in mapa_colunas.keys() if c in df_full.columns]
    
    # Fallback para UF se Estado.1 não existir
    if 'Estado.1' not in cols_existentes and 'Estado' in df_full.columns:
        mapa_colunas['Estado'] = 'UF'
        cols_existentes.append('Estado')

    df_clean = df_full[cols_existentes].copy()
    df_clean.rename(columns=mapa_colunas, inplace=True)

    # Preencher colunas numéricas com 0.0
    cols_num = ['Faturamento', 'Comissões', 'temp_receita_envio', 'temp_tarifa_envio', 'temp_cancelamentos', 'temp_total']
    for col in cols_num:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)
        else:
            df_clean[col] = 0.0

    # --- CÁLCULOS ---
    # Frete = Receita Envio + Tarifa Envio (Geralmente Tarifa é negativa e maior que receita)
    # Vamos manter o sinal original da soma (que deve ser negativo para custo)
    # Mas o padrão Novoon para 'Frete' costuma ser o valor do custo (negativo)
    df_clean['Frete'] = df_clean['temp_receita_envio'] + df_clean['temp_tarifa_envio']

    # Lucro Bruto = Faturamento + Comissões + Frete + Cancelamentos
    # (Lembrando que Comissões, Frete e Cancelamentos já vêm negativos do ML geralmente)
    # Vamos verificar o sinal. 
    # No ML: Receita (+), Tarifa (-), Receita Envio (+), Tarifa Envio (-).
    # Então a soma direta deve dar o lucro.
    df_clean['Lucro Bruto'] = (
        df_clean['Faturamento'] + 
        df_clean['Comissões'] + 
        df_clean['Frete'] + 
        df_clean['temp_cancelamentos']
    )

    # Custo Operacional = Lucro - Faturamento
    df_clean['Custo Operacional'] = df_clean['Lucro Bruto'] - df_clean['Faturamento']

    # --- FILTRAGEM DE CANCELADOS (LUCRO ZERO OU COLUNA CANCELAMENTOS) ---
    # 1. Se tem valor em 'temp_cancelamentos' (diferente de 0), remove.
    # 2. Se Lucro Bruto é 0, remove.
    
    qtd_antes = len(df_clean)
    
    # Filtro 1: Cancelamentos != 0
    df_clean = df_clean[df_clean['temp_cancelamentos'] == 0.0]
    
    # Filtro 2: Lucro Bruto != 0
    df_clean = df_clean[df_clean['Lucro Bruto'] != 0.0]
    
    qtd_depois = len(df_clean)
    print(f"  - Removidos {qtd_antes - qtd_depois} registros (Cancelamentos != 0 ou Lucro zerado).")

    # --- DATAS ---
    datas = df_clean['Data Venda'].apply(extrair_data_ml)
    df_clean['dia'] = [d[0] for d in datas]
    df_clean['mes'] = [d[1] for d in datas]
    df_clean['ano'] = [d[2] for d in datas]

    # --- LIMPEZA FINAL ---
    df_clean.drop(columns=['temp_receita_envio', 'temp_tarifa_envio', 'temp_cancelamentos', 'temp_total', 'Data Venda'], errors='ignore', inplace=True)

    # Reordenar
    cols_ordem = [
        'Id do Pedido Unificado', 'Produto', 'dia', 'mes', 'ano',
        'Cidade', 'UF', 'CEP',
        'Faturamento', 'Frete', 'Comissões', 'Custo Operacional', 'Lucro Bruto'
    ]
    cols_finais = [c for c in cols_ordem if c in df_clean.columns]
    df_clean = df_clean[cols_finais]

    # Salvar
    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)
    path_saida = os.path.join(PASTA_SAIDA, ARQUIVO_SAIDA)
    df_clean.to_csv(path_saida, index=False, encoding='utf-8-sig')

    print("\n" + "="*80)
    print("RESULTADO MERCADO LIVRE FINAL:")
    print(f"Arquivo salvo em: {path_saida}")
    print(f"Total de Linhas: {len(df_clean)}")
    print(f"Faturamento Total: R$ {df_clean['Faturamento'].sum():,.2f}")
    print(f"Lucro Bruto Total: R$ {df_clean['Lucro Bruto'].sum():,.2f}")
    print("="*80)

if __name__ == "__main__":
    processar_mercadolivre()
