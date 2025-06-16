# config.py

import os

# Define o diretório base da aplicação
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define o caminho para o diretório de dados
DATA_DIR = os.path.join(BASE_DIR, "data")

# Garante que o diretório de dados exista
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Define o caminho completo para o arquivo do banco de dados SQLite
DATABASE_PATH = os.path.join(DATA_DIR, "nutricional.db")

# Outras configurações podem ser adicionadas aqui no futuro
# Ex: DEBUG = True

