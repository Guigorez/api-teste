import pandas as pd
from sqlalchemy import create_engine
import os

# --- CONFIGURAÇÃO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Se quiser Postgres, pasta mudar esta string ou usar env vars no futuro
CAMINHO_DB = os.path.join(BASE_DIR, 'vendas_animoshop.db')
CONNECTION_STRING = f"sqlite:///{CAMINHO_DB}"

DIRETORIOS = {
    'CONSOLIDADO': os.path.join(BASE_DIR, 'Dados', 'AnimoShop', 'planilhas limpas'),
    'CONCILIADO':  os.path.join(BASE_DIR, 'Dados', 'AnimoShop', 'planilhas atom')
}

def limpar_nome_tabela(nome_arquivo):
    """
    Transforma 'mercado_livre_consolidado_final.csv' em 'mercado_livre_consolidado'
    Remove extensão e sufixos desnecessários para o nome da tabela SQL.
    """
    nome = nome_arquivo.lower().replace('.csv', '')
    nome = nome.replace('_final', '') # Remove o sufixo _final para ficar mais limpo
    return nome

def criar_banco_dados():
    print("="*80)
    print("CRIANDO BANCO DE DADOS SQL (MASTER) - VIA SQLALCHEMY")
    print(f"Connection String: {CONNECTION_STRING}")
    print("="*80)

    # Cria engine
    try:
        engine = create_engine(CONNECTION_STRING)
        # Testa conexao
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"Erro ao conectar banco: {e}")
        return

    total_tabelas = 0
    total_linhas = 0

    for tipo_dado, pasta in DIRETORIOS.items():
        print(f"\n📂 Processando pasta: {tipo_dado} ...")
        
        if not os.path.exists(pasta):
            print(f"   ⚠️ Pasta não encontrada: {pasta}")
            continue

        arquivos = [f for f in os.listdir(pasta) if f.endswith('.csv')]
        
        for arquivo in arquivos:
            caminho_completo = os.path.join(pasta, arquivo)
            nome_tabela = limpar_nome_tabela(arquivo)

            try:
                # Lê o CSV
                # DICA DE OURO: dtype=str garante que o ID do ML não perca precisão no SQL
                df = pd.read_csv(caminho_completo, dtype={'Id do Pedido Unificado': str})
                
                # Limpa nomes de colunas (SQL não gosta de espaços)
                # Ex: "Lucro Líquido" vira "lucro_liquido"
                df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

                # Salva no SQL usando SQLAlchemy Engine
                # if_exists='replace' -> Se rodar de novo, ele atualiza a tabela inteira
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