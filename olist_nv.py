import pandas as pd
import os

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getcwd()
PASTA_ENTRADA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas', 'Olist')
PASTA_SAIDA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas')
ARQUIVO_SAIDA = 'olist_novoon_final.csv'

MESES_MAPA = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

def limpar_valor(col):
    """Converte coluna de string numérica (PT-BR) para float"""
    return pd.to_numeric(col.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0.0)

def processar_olist():
    print("="*80)
    print("PROCESSANDO OLIST NOVOON (REFACTORED)...")
    print("="*80)

    dfs = []
    if os.path.exists(PASTA_ENTRADA):
        arquivos = sorted([f for f in os.listdir(PASTA_ENTRADA) if f.endswith('.csv') or f.endswith('.xlsx')])
        for file in arquivos:
            caminho = os.path.join(PASTA_ENTRADA, file)
            try:
                if file.endswith('.csv'):
                    try:
                        df = pd.read_csv(caminho, encoding='utf-8', sep=';')
                    except:
                        df = pd.read_csv(caminho, encoding='latin-1', sep=';')
                else:
                    df = pd.read_excel(caminho)
                
                df.columns = df.columns.str.strip().str.lower()
                dfs.append(df)
                print(f'✓ Lido: {file} ({len(df)} linhas)')
            except Exception as e:
                print(f"⚠ Erro em {file}: {e}")

    if not dfs:
        print("❌ Nenhum dado encontrado.")
        return

    df_full = pd.concat(dfs, ignore_index=True)

    # --- FILTRO DE CANCELADOS ---
    if 'status' in df_full.columns:
        total_antes = len(df_full)
        df_full = df_full[df_full['status'] != 'cancelado']
        print(f"ℹ️  Removidos {total_antes - len(df_full)} registros cancelados.")

    # --- SELEÇÃO E RENOMEAÇÃO ---
    mapa_colunas = {
        'código do pedido': 'Id do Pedido Unificado',
        'valor total': 'Faturamento',
        'comissão': 'Comissoes',
        'frete': 'Frete',
        'valor líquido': 'Lucro Bruto',
        'produto': 'Produto',
        'data da compra': 'Data Venda',
        'status': 'Status'
    }

    cols_existentes = [c for c in mapa_colunas.keys() if c in df_full.columns]
    df_clean = df_full[cols_existentes].copy()
    df_clean.rename(columns=mapa_colunas, inplace=True)

    # Adicionar colunas faltantes padrão
    if 'Cidade' not in df_clean.columns: df_clean['Cidade'] = 'Desconhecido'
    if 'UF' not in df_clean.columns: df_clean['UF'] = 'Desconhecido'
    if 'CEP' not in df_clean.columns: df_clean['CEP'] = 'Desconhecido'

    # --- CONVERSÃO NUMÉRICA ---
    cols_num = ['Faturamento', 'Comissoes', 'Frete', 'Lucro Bruto']
    for col in cols_num:
        if col in df_clean.columns:
            df_clean[col] = limpar_valor(df_clean[col])
        else:
            df_clean[col] = 0.0

    # --- CÁLCULOS ---
    # Custo Operacional = Lucro - Faturamento
    df_clean['Custo Operacional'] = df_clean['Lucro Bruto'] - df_clean['Faturamento']

    # --- DATAS ---
    if 'Data Venda' in df_clean.columns:
        datas = pd.to_datetime(df_clean['Data Venda'], errors='coerce')
        df_clean['dia'] = datas.dt.day.astype('Int64')
        df_clean['ano'] = datas.dt.year.astype('Int64')
        df_clean['mes'] = datas.dt.month.map(MESES_MAPA).fillna('Desconhecido')
    else:
        df_clean['dia'] = pd.NA
        df_clean['mes'] = 'Desconhecido'
        df_clean['ano'] = pd.NA

    # --- LIMPEZA FINAL ---
    if 'Data Venda' in df_clean.columns: df_clean.drop(columns=['Data Venda'], inplace=True)
    if 'Status' in df_clean.columns: df_clean.drop(columns=['Status'], inplace=True)

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
    print("RESULTADO OLIST FINAL:")
    print(f"Arquivo salvo em: {path_saida}")
    print(f"Total de Linhas: {len(df_clean)}")
    print(f"Faturamento Total: R$ {df_clean['Faturamento'].sum():,.2f}")
    print(f"Lucro Bruto Total: R$ {df_clean['Lucro Bruto'].sum():,.2f}")
    print("="*80)

if __name__ == "__main__":
    processar_olist()
