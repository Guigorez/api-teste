from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .logger import setup_logging
from .routes import router

# Inicializa logs
setup_logging()

app = FastAPI(
    title="AnimoShop Dashboard API",
    description="API para servir dados do Data Warehouse AnimoShop",
    version="1.0.0"
)

# Configuração CORS (Permite acesso do frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique a origem do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "API AnimoShop Online! Acesse /docs para documentação."}
