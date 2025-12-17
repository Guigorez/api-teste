import pandas as pd
import os

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getcwd()
PASTA_ENTRADA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas', 'MagaLu')
PASTA_SAIDA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas')
ARQUIVO_SAIDA = 'magalu_novoon_final.csv'

MESES_MAPA = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

def limpar_valor(valor):
    """Converte 'R$ 1.234,56' ou float para float padrão"""
    try:
        if pd.isna(valor) or valor == '':
            return 0.0
        s = str(valor).strip()
        s = s.replace('R$', '').strip()
        # Magalu usa ponto como milhar e virgula como decimal? Ou padrão US?
        # No csv raw visto: "R$ 557.93". Parece ponto como decimal.
        # Mas vamos garantir removendo 'R$' e espaços.
        return float(s)
    except:
        return 0.0

def extrair_data(data_str):
    """Extrai dia, mes, ano de 'dd/mm/yyyy hh:mm:ss'"""
    try:
        d = str(data_str).split(' ')[0]
        dd, mm, yy = d.split('/')
        return int(dd), int(mm), int(yy)
    except:
        return None, None, None

def processar_magalu():
    print("="*80)
    print("PROCESSANDO MAGALU NOVOON (REFACTORED)...")
    print("="*80)

    dfs = []
    if os.path.exists(PASTA_ENTRADA):
        arquivos = sorted([f for f in os.listdir(PASTA_ENTRADA) if f.endswith('.csv')])
        for file in arquivos:
            caminho = os.path.join(PASTA_ENTRADA, file)
            try:
                # Tenta ler com separador ',' (padrão visto no raw)
                try:
                    df = pd.read_csv(caminho, encoding='utf-8', sep=',')
                except:
                    df = pd.read_csv(caminho, encoding='latin-1', sep=';')
                
                df.columns = df.columns.str.strip()
                dfs.append(df)
                print(f'✓ Lido: {file} ({len(df)} linhas)')
            except Exception as e:
                print(f"⚠ Erro em {file}: {e}")

    if not dfs:
        print("❌ Nenhum dado encontrado.")
        return

    df_full = pd.concat(dfs, ignore_index=True)

    # --- SELEÇÃO E RENOMEAÇÃO (ALLOWLIST) ---
    # Mapeamento: Nome Original -> Nome Novoon
    mapa_colunas = {
        'Número do pedido': 'Id do Pedido Unificado',
        'Título do produto': 'Produto',
        'Data do Pedido': 'Data Venda',
        'Valor bruto do pedido': 'Faturamento',
        'Valor líquido estimado a receber': 'Lucro Bruto',
        'Coparticipação de Fretes estimada': 'Frete',
        # Comissões será calculado somando colunas, mas pegamos as bases
        'Serviços do marketplace (1+2+3)': 'temp_servicos',
        'Tarifa fixa': 'temp_tarifa'
    }

    # Verifica quais colunas existem
    cols_existentes = [c for c in mapa_colunas.keys() if c in df_full.columns]
    df_clean = df_full[cols_existentes].copy()
    df_clean.rename(columns=mapa_colunas, inplace=True)

    # Adicionar colunas faltantes padrão Novoon se não existirem
    cols_padrao = ['Cidade', 'UF', 'CEP']
    for c in cols_padrao:
        df_clean[c] = 'Desconhecido' # Magalu não fornece endereço no relatório financeiro padrão

    # --- CONVERSÃO DE VALORES ---
    cols_financeiras = ['Faturamento', 'Lucro Bruto', 'Frete', 'temp_servicos', 'temp_tarifa']
    for col in cols_financeiras:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(limpar_valor)
        else:
            df_clean[col] = 0.0

    # --- FILTRAGEM DE CANCELADOS ---
    # Se Lucro Bruto é 0, a venda foi cancelada/não concretizada
    qtd_antes = len(df_clean)
    df_clean = df_clean[df_clean['Lucro Bruto'] != 0.0]
    qtd_depois = len(df_clean)
    print(f"  - Removidos {qtd_antes - qtd_depois} registros com Lucro Bruto zerado (Cancelados).")

    # --- CÁLCULOS ---
    # Comissões = Serviços + Tarifa
    df_clean['Comissões'] = df_clean['temp_servicos'] + df_clean['temp_tarifa']

    # Custo Operacional = Lucro Bruto - Faturamento
    # (Garante que a conta feche: Faturamento + Custo = Lucro)
    df_clean['Custo Operacional'] = df_clean['Lucro Bruto'] - df_clean['Faturamento']

    # --- DATAS ---
    datas = df_clean['Data Venda'].apply(lambda x: extrair_data(x))
    df_clean['dia'] = [d[0] for d in datas]
    df_clean['mes'] = [MESES_MAPA.get(d[1], 'Desconhecido') for d in datas]
    df_clean['ano'] = [d[2] for d in datas]

    # --- LIMPEZA FINAL ---
    # Remover colunas temporárias
    df_clean.drop(columns=['temp_servicos', 'temp_tarifa'], errors='ignore', inplace=True)

    # Reordenar para ficar bonito (opcional, mas bom para debug)
    cols_ordem = [
        'Id do Pedido Unificado', 'Produto', 'dia', 'mes', 'ano',
        'Cidade', 'UF', 'CEP',
        'Faturamento', 'Frete', 'Comissões', 'Custo Operacional', 'Lucro Bruto'
    ]
    # Garante que só usa colunas que realmente existem
    cols_finais = [c for c in cols_ordem if c in df_clean.columns]
    df_clean = df_clean[cols_finais]

    # Salvar
    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)
    path_saida = os.path.join(PASTA_SAIDA, ARQUIVO_SAIDA)
    df_clean.to_csv(path_saida, index=False, encoding='utf-8-sig')

    print("\n" + "="*80)
    print("RESULTADO MAGALU FINAL:")
    print(f"Arquivo salvo em: {path_saida}")
    print(f"Total de Linhas: {len(df_clean)}")
    print(f"Faturamento Total: R$ {df_clean['Faturamento'].sum():,.2f}")
    print(f"Lucro Bruto Total: R$ {df_clean['Lucro Bruto'].sum():,.2f}")
    print("="*80)

if __name__ == "__main__":
    processar_magalu()
