import pandas as pd
import os

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getcwd()
PASTA_ENTRADA = os.path.join(BASE_DIR, 'Dados', 'AnimoShop', 'planilhas limpas')
PASTA_SAIDA = os.path.join(BASE_DIR, 'Dados', 'AnimoShop') # Putting it in the main folder for easier access
ARQUIVO_FINAL = 'animoshop_consolidado_geral.csv'

# Marketplaces e seus arquivos
MARKETPLACES = {
    'magalu_consolidado_final.csv': 'Magalu',
    'amazon_consolidado_final.csv': 'Amazon',
    'shopee_consolidado_final.csv': 'Shopee',
    'mercado_livre_consolidado_final.csv': 'Mercado Livre',
    'madeira_consolidado_final.csv': 'MadeiraMadeira',
    'olist_consolidado_final.csv': 'Olist'
}

# Colunas padrão esperadas (Saída)
COLUNAS_PADRAO = [
    'Id do Pedido Unificado',
    'Produto',
    'MarketPlace',
    'dia',
    'mes',
    'ano',
    'Cidade',
    'UF',
    'CEP',
    'Faturamento',
    'Frete',
    'Comissões',
    'Custo Operacional',
    'Lucro Bruto', # Standardizing to Lucro Bruto as per Dashboard
    'contagem_pedidos', # Keeping this as it seems useful
    'Status',
    'mes_num_filtro',
    'data_filtro',
    'uf_norm'
]

# Mapa de renomeação (Entrada -> Saída)
# Padroniza nomes de colunas que podem variar ou estar em minúsculo
MAPA_COLUNAS = {
    'faturamento': 'Faturamento',
    'frete': 'Frete',
    'comissoes': 'Comissões',
    'comissão': 'Comissões',
    'custo_operacional': 'Custo Operacional',
    'lucro_liquido': 'Lucro Bruto', # Mapping lucro_liquido to Lucro Bruto
    'id do pedido unificado': 'Id do Pedido Unificado',
    'produto': 'Produto',
    'marketplace': 'MarketPlace',
    'status': 'Status',
    'cidade': 'Cidade',
    'uf': 'UF',
    'cep': 'CEP'
}

# --- FUNÇÕES DE LIMPEZA ---
ESTADO_PARA_UF = {
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
MESES_ORDEM = {
    'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
    'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
}

def normalize_uf(val):
    val_str = str(val).upper().strip()
    if len(val_str) == 2:
        return val_str
    return ESTADO_PARA_UF.get(val_str, val_str)

def consolidar_marketplaces():
    print("="*80)
    print("CONSOLIDAÇÃO FINAL - TODOS OS MARKETPLACES ANIMOSHOP")
    print("="*80 + "\n")

    dfs_consolidados = []
    dfs_info = []

    if not os.path.exists(PASTA_ENTRADA):
        print(f"❌ Pasta de entrada não encontrada: {PASTA_ENTRADA}")
        return

    for arquivo, marketplace in MARKETPLACES.items():
        caminho = os.path.join(PASTA_ENTRADA, arquivo)
        if os.path.exists(caminho):
            try:
                df = pd.read_csv(caminho, encoding='utf-8-sig')
                qtd_linhas = len(df)
                
                # Adiciona coluna do Marketplace se não existir
                if 'MarketPlace' not in df.columns and 'marketplace' not in df.columns:
                    df['MarketPlace'] = marketplace
                
                # Normaliza nomes das colunas
                df.rename(columns=MAPA_COLUNAS, inplace=True)
                
                # Garante que colunas numéricas sejam float
                cols_num = ['Faturamento', 'Frete', 'Comissões', 'Custo Operacional', 'Lucro Bruto', 'contagem_pedidos']
                for col in cols_num:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    else:
                        df[col] = 0.0
                
                # Adiciona colunas faltantes como vazio
                for col in COLUNAS_PADRAO:
                    if col not in df.columns:
                        df[col] = ''
                            
                # Seleciona e Reordena
                df_final = df[COLUNAS_PADRAO].copy()

                dfs_consolidados.append(df_final)
                
                dfs_info.append({
                    'marketplace': marketplace,
                    'arquivo': arquivo,
                    'linhas': qtd_linhas,
                    'faturamento': df_final['Faturamento'].sum(),
                    'lucro': df_final['Lucro Bruto'].sum()
                })
                print(f"✓ {marketplace}: {qtd_linhas} linhas processadas.")

            except Exception as e:
                print(f"❌ Erro ao processar {marketplace} ({arquivo}): {e}")
        else:
            print(f"⚠ Arquivo não encontrado: {arquivo} (Pular {marketplace})")

    if not dfs_consolidados:
        print("\n❌ Nenhum arquivo foi consolidado.")
        return

    # Concatena tudo
    df_total = pd.concat(dfs_consolidados, ignore_index=True)

    # Convertendo dia/mes/ano para inteiros onde possivel para ficar bonito
    for col in ['dia', 'ano']:
        df_total[col] = pd.to_numeric(df_total[col], errors='coerce').fillna(0).astype(int)

    # Pre-processamento de Datas
    print("... Calculando datas e normalizando UF ...")
    df_total['mes_num_filtro'] = df_total['mes'].map(MESES_ORDEM).fillna(0).astype(int)
    
    # Cria data_filtro (YYYY-MM-DD)
    df_total['data_filtro'] = pd.to_datetime(dict(year=df_total['ano'], month=df_total['mes_num_filtro'], day=df_total['dia']), errors='coerce')
    
    # Normaliza UF
    if 'UF' in df_total.columns:
        df_total['uf_norm'] = df_total['UF'].apply(normalize_uf)
    else:
        df_total['uf_norm'] = ''

    # Salvar
    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)
    path_saida = os.path.join(PASTA_SAIDA, ARQUIVO_FINAL)
    df_total.to_csv(path_saida, index=False, encoding='utf-8-sig')

    print("\n" + "="*80)
    print("RESUMO DA CONSOLIDAÇÃO ANIMOSHOP:")
    print(f"{'Marketplace':<20} | {'Linhas':<10} | {'Faturamento':<20} | {'Lucro Bruto':<20}")
    print("-" * 80)
    
    for info in dfs_info:
        print(f"{info['marketplace']:<20} | {info['linhas']:<10} | R$ {info['faturamento']:<18,.2f} | R$ {info['lucro']:<18,.2f}")
    
    print("-" * 80)
    print(f"{'TOTAL':<20} | {len(df_total):<10} | R$ {df_total['Faturamento'].sum():<18,.2f} | R$ {df_total['Lucro Bruto'].sum():<18,.2f}")
    print("="*80)
    print(f"\nArquivo final gerado em:\n{path_saida}")

if __name__ == "__main__":
    consolidar_marketplaces()
