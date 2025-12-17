import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configura o sistema de log da aplicação.
    - Console: Nível INFO (stdout)
    - Arquivo: Nível INFO (api.log), rotativo (5MB x 3 arquivos)
    """
    
    # Nome do arquivo de log na raiz do projeto ou pasta api
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'api.log')
    log_file_path = os.path.normpath(log_file_path)

    # Root Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Evita duplicidade de handlers se a função for chamada 2x
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # 1. Console Handler (Stream)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # 2. File Handler (Rotating)
    try:
        file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Erro ao criar arquivo de log: {e}")

    # Silencia loggers muito verbosos de terceiros se necessário
    logging.getLogger("multipart").setLevel(logging.WARNING)
    
    logger.info(f"Logging configurado via api/logger.py. Arquivo: {log_file_path}")

# Executa setup ao importar (opcional, ou chamar no main)
setup_logging()
