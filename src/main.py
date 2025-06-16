# src/main.py

import sys
import logging
from PySide6.QtWidgets import QApplication, QMessageBox

# Configuração básica de logging
log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format)

# Importar componentes principais
try:
    from core import database
    from ui.controllers.main_controller import MainController
    from config import DATABASE_PATH # Importar o caminho do DB
except ImportError as e:
    logging.critical(f"Erro fatal de importação: {e}. Verifique a estrutura do projeto e o PYTHONPATH.")
    try:
        temp_app = QApplication([])
        QMessageBox.critical(None, "Erro Fatal", f"Erro ao iniciar a aplicação:\n{e}\n\nVerifique a instalação e a estrutura de pastas.")
    except Exception:
        print(f"Erro fatal de importação: {e}. Não foi possível mostrar mensagem gráfica.")
    sys.exit(1)

def run_application():
    """Inicializa e executa a aplicação principal."""
    logging.info("Iniciando Sistema de Gestão Nutricional...")

    # 1. Inicializar Banco de Dados
    logging.info(f"Verificando/Inicializando banco de dados em: {DATABASE_PATH}")
    try:
        if not database.initialize_database():
            raise RuntimeError("A função initialize_database() retornou False.")
        logging.info("Banco de dados inicializado com sucesso.")
    except Exception as db_error:
        logging.critical(f"Erro crítico ao inicializar o banco de dados: {db_error}", exc_info=True)
        QMessageBox.critical(None, "Erro de Banco de Dados", 
                             f"Não foi possível inicializar ou conectar ao banco de dados:\n{db_error}\n\nVerifique as permissões e o caminho do arquivo: {DATABASE_PATH}\nA aplicação será encerrada.")
        sys.exit(1)

    # 2. Criar Instância da Aplicação Qt
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        logging.info("Instância QApplication criada.")
    else:
        logging.info("Usando instância QApplication existente.")

    # 3. Instanciar o Controlador Principal
    try:
        controller = MainController() 
        logging.info("MainController instanciado com sucesso.")
    except Exception as controller_error:
        logging.critical(f"Erro crítico ao instanciar o MainController: {controller_error}", exc_info=True)
        QMessageBox.critical(None, "Erro de Inicialização", 
                             f"Ocorreu um erro inesperado ao preparar a aplicação:\n{controller_error}\n\nA aplicação será encerrada.")
        sys.exit(1)

    # 4. Exibir a Janela Principal e Iniciar o Loop de Eventos
    logging.info("Exibindo a janela principal e iniciando o loop de eventos.")
    controller.show_view() 

if __name__ == "__main__":
    run_application()


