from sqlalchemy import create_engine
import os

# Determina o diretório raiz do projeto (um nível acima deste arquivo)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Caminhos dos bancos de dados (Relativos ao BASE_DIR)
DB_PATHS = {
    'animoshop': os.path.join(BASE_DIR, 'vendas_animoshop.db'),
    'novoon': os.path.join(BASE_DIR, 'vendas_novoon.db')
}

def get_db_engine(company='animoshop'):
    """
    Retorna uma ENGINE SQLAlchemy sempre apontando para o SQLite local.
    """
    company = company.lower()
    
    db_path = DB_PATHS.get(company)
    if not db_path:
        raise ValueError(f"Empresa desconhecida: {company}")
    
    # SQLite connection string
    db_url = f"sqlite:///{db_path}"

    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        print(f"Erro ao criar engine SQLite para {company}: {e}")
        raise e

def get_db_connection(company='animoshop'):
    """
    Retorna uma conexão bruta (RAW) compatível com API legada.
    Gerada via SQLAlchemy Engine para SQLite.
    """
    engine = get_db_engine(company)
    conn = engine.connect() # SQLAlchemy Connection
    return conn
