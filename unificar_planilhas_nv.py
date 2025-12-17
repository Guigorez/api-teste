import pandas as pd
import os

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getcwd()
PASTA_ENTRADA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas')
PASTA_SAIDA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas')
ARQUIVO_FINAL = 'novoon_consolidado_geral.csv'

# Marketplaces e seus arquivos
MARKETPLACES = {
    'magalu_novoon_final.csv': 'Magalu',
    'amazon_novoon_final.csv': 'Amazon',
    'shopee_novoon_final.csv': 'Shopee',
    'mercado_livre_novoon_final.csv': 'Mercado Livre',
    'madeira_novoon_final.csv': 'MadeiraMadeira',
    'olist_novoon_final.csv': 'Olist'
}

# Colunas padrão esperadas em todos os arquivos (Title Case)
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
    'Lucro Bruto'
]

def consolidar_marketplaces():
    print("="*80)
    print("CONSOLIDAÇÃO FINAL - TODOS OS MARKETPLACES NOVOON")
    print("="*80 + "\n")

    dfs_consolidados = []
    dfs_info = []

    for arquivo, marketplace in MARKETPLACES.items():
        caminho = os.path.join(PASTA_ENTRADA, arquivo)
        if os.path.exists(caminho):
            try:
                df = pd.read_csv(caminho, encoding='utf-8-sig')
                qtd_linhas = len(df)
                
                # Adiciona coluna do Marketplace
                df['MarketPlace'] = marketplace
                
                # Normaliza colunas se necessário (embora os scripts já devam estar em Title Case)
                # Garante que colunas numéricas sejam float
                cols_num = ['Faturamento', 'Frete', 'Comissões', 'Custo Operacional', 'Lucro Bruto']
                for col in cols_num:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    else:
                        df[col] = 0.0
                
                # Garante colunas de endereço
                cols_addr = ['Cidade', 'UF', 'CEP']
                for col in cols_addr:
                    if col not in df.columns:
                        df[col] = 'Desconhecido'

                # Seleciona apenas colunas padrão
                cols_existentes = [c for c in COLUNAS_PADRAO if c in df.columns]
                df_final = df[cols_existentes].copy()
                
                # Adiciona colunas faltantes como vazio/zero
                for col in COLUNAS_PADRAO:
                    if col not in df_final.columns:
                        if col in cols_num:
                            df_final[col] = 0.0
                        else:
                            df_final[col] = ''
                            
                # Reordena
                df_final = df_final[COLUNAS_PADRAO]

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

    # --- UNIFICAÇÃO DE NOMES DE PRODUTOS ---
    def unificar_nomes_produtos(df):
        # Mapa de unificação (Variations -> Standard)
        # Note: Using lower case for matching to be robust
        mapa_produtos = {
            # 12L
            'fritadeira elétrica air fryer digital novoon 12l - 4 em 1': 'Fritadeira Elétrica Air Fryer Digital Novoon 12l',
            'air fryer digital novoon 12l - fritadeira elétrica sem óleo preta inox com tampa de vidro 127v/220v': 'Fritadeira Elétrica Air Fryer Digital Novoon 12l',
            'fritadeira elétrica forno oven digital novoon 12l 1700w 4 em 1 - frita sem óleo, assa, reaquece e desidrata. air fryer 12 litros silenciosa prepara': 'Fritadeira Elétrica Air Fryer Digital Novoon 12l',
            'fritadeira elétrica forno oven digital novoon 12l 1800w 4 em 1 - frita sem óleo, assa, reaquece e desidrata. air fryer 12 litros silenciosa prepara': 'Fritadeira Elétrica Air Fryer Digital Novoon 12l',
            'fritadeira elétrica digital novoon 12l 4 em 1 - frita sem óleo, assa, reaquece e desidrata. air fryer 12 litros prepara batata f': 'Fritadeira Elétrica Air Fryer Digital Novoon 12l',
            'fritadeira elétrica air fryer digital novoon 12l 4 em 1': 'Fritadeira Elétrica Air Fryer Digital Novoon 12l',
            
            # 4.5L
            'fritadeira elétrica digital novoon 4,5l 3 em 1 - frita sem óleo, assa e reaquece. melhor air fryer 4,5 litros, batata frita, pão': 'Fritadeira Elétrica Digital Novoon 4,5L',
            'fritadeira elétrica digital novoon 4,5l 1400w 3 em 1 - frita sem óleo, assa e reaquece. air fryer 4,5 litros silenciosa prepara batata frita, frango': 'Fritadeira Elétrica Digital Novoon 4,5L',
            'fritadeira air fryer novoon 4,5 litros digital - alta potência 1400w, sem óleo, assa e reaquece 3 em 1': 'Fritadeira Elétrica Digital Novoon 4,5L',
            'fritadeira air fryer novoon 4,5 litros digital alta potência 1400w, sem óleo, assa e reaquece 3 em 1': 'Fritadeira Elétrica Digital Novoon 4,5L',
            'fritadeira elétrica air fryer digital novoon 4,5l 3 em 1': 'Fritadeira Elétrica Digital Novoon 4,5L',
            'fritadeira air fryer digital novoon 4,5l preta - 3 em 1': 'Fritadeira Elétrica Digital Novoon 4,5L'
        }
        
        if 'Produto' in df.columns:
            # Normaliza para minusculo, strip e remove NBSP para comparar
            df['Produto_Norm'] = df['Produto'].astype(str).str.lower().str.replace('\xa0', ' ').str.strip()
            
            # Aplica o mapa
            # Se encontrar no mapa, usa o valor do mapa. Se não, mantém o original (Title Case)
            # Mas para manter o original, precisamos pegar do 'Produto' original, não do Norm.
            
            def get_standard_name(row):
                p_norm = row['Produto_Norm']
                # Tenta match exato
                if p_norm in mapa_produtos:
                    return mapa_produtos[p_norm]
                
                # Tenta partial match se necessário (opcional, mas o usuário deu lista exata)
                # Vamos ficar com match exato primeiro para evitar falsos positivos
                
                # Fallback: Tenta limpar caracteres extras se o match falhar
                # Ex: as vezes vem com espaço extra no meio
                
                return row['Produto'] # Retorna original se não achar

            df['Produto'] = df.apply(get_standard_name, axis=1)
            df.drop(columns=['Produto_Norm'], inplace=True)
            
        return df

    df_total = unificar_nomes_produtos(df_total)

    # Salvar
    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)
    path_saida = os.path.join(PASTA_SAIDA, ARQUIVO_FINAL)
    df_total.to_csv(path_saida, index=False, encoding='utf-8-sig')

    print("\n" + "="*80)
    print("RESUMO DA CONSOLIDAÇÃO:")
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
