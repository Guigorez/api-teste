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
    Retorna uma ENGINE SQLAlchemy.
    Suporta troca para PostgreSQL via variável de ambiente.
    """
    company = company.lower()
    
    # Check env var specific for company, e.g., NOVOON_DATABASE_URL
    env_key = f"{company.upper()}_DATABASE_URL"
    db_url = os.getenv(env_key)
    
    if not db_url:
        # Fallback to SQLite file
        db_path = DB_PATHS.get(company)
        if not db_path:
            raise ValueError(f"Empresa desconhecida: {company}")
        
        # SQLite connection string
        db_url = f"sqlite:///{db_path}"

    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        print(f"Erro ao criar engine para {company}: {e}")
        raise e

def get_db_connection(company='animoshop'):
    """
    Retorna uma conexão bruta (RAW) compatível com API legada.
    Mas agora gerada via SQLAlchemy Engine.
    """
    engine = get_db_engine(company)
    conn = engine.connect() # SQLAlchemy Connection
    return conn
