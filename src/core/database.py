# src/core/database.py

import sqlite3
import logging
import os # Importar os para usar no initialize_database

# Adiciona o diretório src ao sys.path para permitir importações relativas
# Isso pode ser necessário se este módulo for executado diretamente ou importado de forma complexa
# import sys
# src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), \'..\'))
# sys.path.insert(0, src_path)

# Tenta importar de forma relativa primeiro, depois absoluta se falhar (para flexibilidade)
try:
    from .config import DATABASE_PATH
except ImportError:
    from config import DATABASE_PATH # Fallback para execução direta ou testes

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def create_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = None
    try:
        # Garante que o diretório pai do banco de dados exista
        db_dir = os.path.dirname(DATABASE_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logging.info(f"Diretório do banco de dados criado em: {db_dir}")
            
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        logging.info(f"Conexão com SQLite DB em {DATABASE_PATH} bem-sucedida.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Erro ao conectar ao banco de dados SQLite: {e}")
        return None

def close_connection(conn):
    """Fecha a conexão com o banco de dados."""
    if conn:
        conn.close()
        # logging.info("Conexão SQLite fechada.") # Log menos verboso

def execute_query(query, params=(), is_script=False):
    """Executa uma query SQL (INSERT, UPDATE, DELETE, CREATE). Retorna True em sucesso, False em falha."""
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        if is_script:
            cursor.executescript(query)
        else:
            cursor.execute(query, params)
        conn.commit()
        # logging.info(f"Query executada com sucesso: {query[:50]}...") # Log menos verboso
        return True
    except sqlite3.Error as e:
        logging.error(f"Erro ao executar query: {e}\nQuery: {query}\nParams: {params}")
        conn.rollback()
        return False
    finally:
        close_connection(conn)

def fetch_one(query, params=()):
    """Executa uma query SELECT e retorna uma única linha."""
    conn = create_connection()
    if conn is None:
        return None
    # Configurar para retornar dicionários pode ser útil, mas vamos manter tuplas por enquanto
    # conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        # logging.info(f"Fetch one executado com sucesso: {query[:50]}...") # Log menos verboso
        return result
    except sqlite3.Error as e:
        logging.error(f"Erro ao executar fetch_one: {e}\nQuery: {query}\nParams: {params}")
        return None
    finally:
        close_connection(conn)

def fetch_all(query, params=()):
    """Executa uma query SELECT e retorna todas as linhas."""
    conn = create_connection()
    if conn is None:
        return None
    # conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        # logging.info(f"Fetch all executado com sucesso: {query[:50]}...") # Log menos verboso
        return results
    except sqlite3.Error as e:
        logging.error(f"Erro ao executar fetch_all: {e}\nQuery: {query}\nParams: {params}")
        return None
    finally:
        close_connection(conn)

def initialize_database():
    """Cria as tabelas do banco de dados se elas não existirem."""
    
    sql_statements = []

    # Tabela Pacientes
    sql_statements.append("""
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_completo TEXT NOT NULL,
        data_nascimento TEXT NOT NULL, -- Formato YYYY-MM-DD
        sexo TEXT,
        telefone TEXT,
        email TEXT UNIQUE,
        endereco TEXT,
        objetivo_consulta TEXT,
        historico_clinico TEXT,
        observacoes TEXT,
        data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabela Avaliacoes
    sql_statements.append("""
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        data_avaliacao TEXT DEFAULT CURRENT_TIMESTAMP,
        peso REAL,
        altura REAL,
        circunferencia_cintura REAL,
        circunferencia_quadril REAL,
        anamnese_resumo TEXT,
        exames_resumo TEXT,
        observacoes TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
    );
    """)

    # Tabela Alimentos
    sql_statements.append("""
    CREATE TABLE IF NOT EXISTS alimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        grupo TEXT,
        unidade_padrao TEXT DEFAULT \'g\',
        kcal_por_unidade REAL,
        cho_por_unidade REAL,
        ptn_por_unidade REAL,
        lip_por_unidade REAL,
        fonte_dados TEXT
    );
    """)

    # Tabela Planos Alimentares
    sql_statements.append("""
    CREATE TABLE IF NOT EXISTS planos_alimentares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        nome_plano TEXT NOT NULL,
        data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
        objetivo TEXT,
        meta_kcal REAL,
        meta_cho_perc REAL,
        meta_ptn_perc REAL,
        meta_lip_perc REAL,
        observacoes_gerais TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
    );
    """)

    # Tabela Itens do Plano Alimentar
    sql_statements.append("""
    CREATE TABLE IF NOT EXISTS itens_plano_alimentar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plano_alimentar_id INTEGER NOT NULL,
        refeicao TEXT NOT NULL,
        alimento_id INTEGER NOT NULL,
        quantidade REAL NOT NULL,
        unidade_medida TEXT NOT NULL,
        FOREIGN KEY (plano_alimentar_id) REFERENCES planos_alimentares (id) ON DELETE CASCADE,
        FOREIGN KEY (alimento_id) REFERENCES alimentos (id) ON DELETE RESTRICT -- Evita deletar alimento usado em plano
    );
    """)

    logging.info("Inicializando/Verificando tabelas do banco de dados...")
    all_success = True
    for i, statement in enumerate(sql_statements):
        if not execute_query(statement, is_script=True):
            logging.error(f"Falha ao verificar/criar tabela (Statement {i+1}).")
            all_success = False
            
    if all_success:
        logging.info("Banco de dados inicializado/verificado com sucesso.")
    else:
        logging.error("Ocorreram erros durante a inicialização do banco de dados.")
    return all_success

# Não chamar initialize_database() automaticamente na importação.
# Deve ser chamado explicitamente no ponto de entrada da aplicação (main.py).

if __name__ == '__main__':
    # Código para testar o módulo diretamente
    logging.info("Testando módulo database.py...")
    if initialize_database():
        logging.info("Teste de inicialização concluído com sucesso.")
    else:
        logging.error("Teste de inicialização falhou.")

