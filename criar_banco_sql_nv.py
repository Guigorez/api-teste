import pandas as pd
from sqlalchemy import create_engine
import os

# --- CONFIGURAÇÃO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_DB = os.path.join(BASE_DIR, 'vendas_novoon.db')
CONNECTION_STRING = f"sqlite:///{CAMINHO_DB}"

# Novoon gera os arquivos em 'Dados/Novoon/planilhas limpas'
PASTA_CONSOLIDADA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas')
# E também o conciliado em 'Dados/Novoon/planilhas atom'
PASTA_CONCILIADA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas atom')

def limpar_nome_tabela(nome_arquivo):
    """
    Transforma 'mercado_livre_novoon_final.csv' em 'mercado_livre_novoon'
    """
    nome = nome_arquivo.lower().replace('.csv', '')
    nome = nome.replace('_final', '') 
    return nome

def criar_banco_dados():
    print("="*80)
    print("CRIANDO BANCO DE DADOS SQL (NOVOON) - VIA SQLALCHEMY")
    print(f"Connection String: {CONNECTION_STRING}")
    print("="*80)

    try:
        engine = create_engine(CONNECTION_STRING)
    except Exception as e:
        print(f"Erro ao criar engine: {e}")
        return
    
    total_tabelas = 0
    total_linhas = 0

    # 1. Processar Planilhas Limpas
    if os.path.exists(PASTA_CONSOLIDADA):
        arquivos = [f for f in os.listdir(PASTA_CONSOLIDADA) if f.endswith('.csv')]
        for arquivo in arquivos:
            caminho_completo = os.path.join(PASTA_CONSOLIDADA, arquivo)
            nome_tabela = limpar_nome_tabela(arquivo)

            try:
                # Lê o CSV
                df = pd.read_csv(caminho_completo, dtype={'Id do Pedido Unificado': str})
                
                # Limpa nomes das colunas (strip)
                df.columns = df.columns.str.strip()
                
                # --- NORMALIZAÇÃO PARA API (Snake Case) ---
                mapa_api = {
                    'Faturamento': 'faturamento',
                    'Lucro Bruto': 'lucro_liquido',
                    'Frete': 'frete',
                    'Comissões': 'comissoes',
                    'Custo Operacional': 'custo_operacional',
                    'Produto': 'produto',
                    'Cidade': 'cidade',
                    'UF': 'uf',
                    'CEP': 'cep',
                    'Id do Pedido Unificado': 'id_pedido',
                    'MarketPlace': 'MarketPlace'
                }
                
                df.rename(columns=mapa_api, inplace=True)
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]

                # Salva no SQL
                df.to_sql(nome_tabela, engine, if_exists='replace', index=False)
                
                qtd = len(df)
                print(f"   ✅ Tabela criada: {nome_tabela:<30} ({qtd} registros)")
                
                total_tabelas += 1
                total_linhas += qtd

            except Exception as e:
                print(f"   ❌ Erro ao processar {arquivo}: {e}")
    else:
        print(f"⚠️ Pasta não encontrada: {PASTA_CONSOLIDADA}")

    # 2. Processar Planilhas Atom (Conciliadas)
    if os.path.exists(PASTA_CONCILIADA):
        arquivos = [f for f in os.listdir(PASTA_CONCILIADA) if f.endswith('.csv')]
        for arquivo in arquivos:
            caminho_completo = os.path.join(PASTA_CONCILIADA, arquivo)
            nome_tabela = arquivo.lower().replace('.csv', '')

            try:
                df = pd.read_csv(caminho_completo, dtype={'Id do Pedido Unificado': str})
                df.columns = df.columns.str.strip()
                
                # --- NORMALIZAÇÃO PARA API (Snake Case) ---
                mapa_api = {
                    'Faturamento': 'faturamento',
                    'Lucro Bruto': 'lucro_liquido',
                    'Frete': 'frete',
                    'Comissões': 'comissoes',
                    'Custo Operacional': 'custo_operacional',
                    'Produto': 'produto',
                    'Cidade': 'cidade',
                    'UF': 'uf',
                    'CEP': 'cep',
                    'Id do Pedido Unificado': 'id_pedido',
                    'MarketPlace': 'MarketPlace'
                }
                df.rename(columns=mapa_api, inplace=True)
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]

                df.to_sql(nome_tabela, engine, if_exists='replace', index=False)
                qtd = len(df)
                print(f"   ✅ Tabela criada: {nome_tabela:<30} ({qtd} registros)")
                total_tabelas += 1
                total_linhas += qtd
            except Exception as e:
                print(f"   ❌ Erro ao processar {arquivo}: {e}")

    print("\n" + "="*80)
    print("PROCESSO FINALIZADO COM SUCESSO!")
    print(f"   - Tabelas criadas: {total_tabelas}")
    print(f"   - Total de linhas importadas: {total_linhas:,}")
    print(f"   - Banco salvo em: {CAMINHO_DB}")
    print("="*80)

if __name__ == "__main__":
    criar_banco_dados()
