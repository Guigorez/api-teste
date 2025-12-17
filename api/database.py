import sqlite3
import os

# Caminhos dos bancos de dados
DB_PATHS = {
    'animoshop': r'C:\Users\MatheusSampaio\Documents\AnimoShop - Python\vendas_animoshop.db',
    'novoon': r'C:\Users\MatheusSampaio\Documents\AnimoShop - Python\vendas_novoon.db'
}

def get_db_connection(company='animoshop'):
    """Retorna uma conexão com o banco de dados SQLite da empresa especificada."""
    company = company.lower()
    db_path = DB_PATHS.get(company)
    
    if not db_path:
        raise ValueError(f"Empresa desconhecida: {company}")

    if not os.path.exists(db_path):
        # Se não existir, tenta criar vazio ou avisa (para evitar crash total se um não tiver rodado ainda)
        # Mas idealmente deve existir. Vamos deixar o erro propagar se não achar, para debug.
        pass 
        # raise FileNotFoundError(f"Banco de dados não encontrado em: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn
