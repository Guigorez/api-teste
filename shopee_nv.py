import pandas as pd
import os
import warnings

# Ignora avisos desnecessários
warnings.filterwarnings('ignore')

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getcwd()
PASTA_ENTRADA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas', 'Shopee')
PASTA_SAIDA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas')
ARQUIVO_SAIDA = 'shopee_novoon_final.csv'

MESES_MAPA = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

def processar_shopee():
    print("="*80)
    print("PROCESSANDO SHOPEE NOVOON (REFACTORED)...")
    print("="*80)

    dfs = []
    if os.path.exists(PASTA_ENTRADA):
        arquivos = sorted([f for f in os.listdir(PASTA_ENTRADA) if f.endswith('.xlsx')])
        for file in arquivos:
            caminho = os.path.join(PASTA_ENTRADA, file)
            try:
                # Shopee header=0 padrão
                df = pd.read_excel(caminho, sheet_name=0, header=0)
                df.columns = df.columns.str.strip()
                dfs.append(df)
                print(f'✓ Lido: {file} ({len(df)} linhas)')
            except Exception as e:
                print(f"⚠ Erro em {file}: {e}")

    if not dfs:
        print("❌ Nenhum dado encontrado.")
        return

    df_full = pd.concat(dfs, ignore_index=True)

    # --- FILTRO DE CANCELADOS ---
    if 'Status do pedido' in df_full.columns:
        total_antes = len(df_full)
        # Filtra "Não pago" E "Cancelado"
        mask_nao_pago = df_full['Status do pedido'].astype(str).str.contains('n[ãa]o pago', case=False, na=False)
        mask_cancelado = df_full['Status do pedido'].astype(str).str.contains('cancelado', case=False, na=False)
        
        df_full = df_full[~(mask_nao_pago | mask_cancelado)]
        print(f"ℹ️  Removidos {total_antes - len(df_full)} registros (Cancelado / Não pago).")

    # --- SELEÇÃO E RENOMEAÇÃO (ALLOWLIST) ---
    mapa_colunas = {
        'ID do pedido': 'Id do Pedido Unificado',
        'Nome do Produto': 'Produto',
        'Hora do pagamento do pedido': 'Data Venda',
        'Cidade': 'Cidade',
        'Cidade.1': 'temp_cidade_1', # Possível duplicata ou fallback
        'UF': 'UF',
        'País': 'Pais',
        'CEP': 'CEP',
        'Bairro': 'Bairro',
        'Endereço de entrega': 'Endereço',
        'Total global': 'Faturamento',
        
        # Colunas temporárias para cálculo
        'Valor estimado do frete': 'temp_frete_valor',
        'Desconto de Frete Aproximado': 'temp_frete_desc',
        'Taxa de transação': 'temp_taxa_transacao',
        'Taxa de comissão': 'temp_taxa_comissao',
        'Taxa de serviço': 'temp_taxa_servico',
        'Reembolso Shopee': 'temp_reembolso'
    }

    # Verifica colunas existentes
    cols_existentes = [c for c in mapa_colunas.keys() if c in df_full.columns]
    df_clean = df_full[cols_existentes].copy()
    df_clean.rename(columns=mapa_colunas, inplace=True)

    # Adicionar colunas faltantes padrão
    if 'Cidade' not in df_clean.columns: df_clean['Cidade'] = 'Desconhecido'
    if 'UF' not in df_clean.columns: df_clean['UF'] = 'Desconhecido'
    if 'CEP' not in df_clean.columns: df_clean['CEP'] = 'Desconhecido'
    
    # Fallback Cidade.1 -> Cidade
    if 'temp_cidade_1' in df_clean.columns:
        df_clean['Cidade'] = df_clean['Cidade'].fillna(df_clean['temp_cidade_1'])
        # Se Cidade for string vazia ou espaço, tenta preencher
        mask_vazio = df_clean['Cidade'].astype(str).str.strip() == ''
        df_clean.loc[mask_vazio, 'Cidade'] = df_clean.loc[mask_vazio, 'temp_cidade_1']

    # --- CONVERSÃO NUMÉRICA ---
    cols_num = ['Faturamento', 'temp_frete_valor', 'temp_frete_desc', 'temp_taxa_transacao', 
                'temp_taxa_comissao', 'temp_taxa_servico', 'temp_reembolso']
    
    for col in cols_num:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)
        else:
            df_clean[col] = 0.0

    # --- CÁLCULOS (PADRÃO NOVOON: CUSTOS NEGATIVOS) ---
    
    # Frete = -(Valor - Desconto)
    # Se o desconto for maior que o valor, o frete seria "positivo" (ganho), mas geralmente é custo.
    df_clean['Frete'] = -1 * (df_clean['temp_frete_valor'] - df_clean['temp_frete_desc'])

    # Comissões = -(Taxas - Reembolso)
    taxas_totais = df_clean['temp_taxa_transacao'] + df_clean['temp_taxa_comissao'] + df_clean['temp_taxa_servico']
    df_clean['Comissões'] = -1 * (taxas_totais - df_clean['temp_reembolso'])

    # Lucro Bruto = Faturamento + Frete + Comissões (Soma algébrica)
    df_clean['Lucro Bruto'] = df_clean['Faturamento'] + df_clean['Frete'] + df_clean['Comissões']

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
    cols_temp = [c for c in df_clean.columns if c.startswith('temp_')]
    df_clean.drop(columns=cols_temp, errors='ignore', inplace=True)
    if 'Data Venda' in df_clean.columns: df_clean.drop(columns=['Data Venda'], inplace=True)

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
    print("RESULTADO SHOPEE REFACTORED:")
    print(f"Arquivo salvo em: {path_saida}")
    print(f"Total de Linhas: {len(df_clean)}")
    print(f"Faturamento Total: R$ {df_clean['Faturamento'].sum():,.2f}")
    print(f"Lucro Bruto Total: R$ {df_clean['Lucro Bruto'].sum():,.2f}")
    print("="*80)

if __name__ == "__main__":
    processar_shopee()
