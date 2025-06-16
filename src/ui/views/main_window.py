# src/ui/views/main_window.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QTableView, QAbstractItemView, QHeaderView, QLabel, 
    QStatusBar, QMenuBar, QToolBar
)
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtCore import Qt, QSize

# Importar recursos (ícones) - precisará compilar resources.qrc depois
# try:
#     from . import resources_rc # Tenta import relativo
# except ImportError:
#     import resources_rc # Fallback para execução direta

class MainWindow(QMainWindow):
    """Janela principal da aplicação."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sistema de Gestão Nutricional")
        self.setGeometry(100, 100, 900, 650) # Aumentar tamanho padrão

        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_central_widget()

        # Conexões de ações que não dependem do controller (como Sair)
        self.quit_action.triggered.connect(self.close)

    def _create_actions(self):
        """Cria as ações (itens de menu, botões de toolbar)."""
        # Ícones (usar placeholders ou caminhos diretos por enquanto)
        # Idealmente, usar QIcon(\":/icons/nome_icone.png\") após compilar resources.qrc
        # Criar pasta assets/icons se não existir
        icon_path = "/home/ubuntu/nutriapp_desktop/assets/icons/" 
        # TODO: Criar ícones placeholder ou usar ícones padrão do Qt
        # from PySide6.QtGui import QStyle
        # style = QApplication.style()
        # icon_exit = style.standardIcon(QStyle.SP_DialogCloseButton)
        # icon_add = style.standardIcon(QStyle.SP_FileDialogNewFolder)
        # icon_edit = style.standardIcon(QStyle.SP_DialogApplyButton) # Aproximação
        # icon_delete = style.standardIcon(QStyle.SP_TrashIcon)
        
        # Ações de Arquivo
        self.quit_action = QAction(QIcon(f"{icon_path}exit.png"), "&Sair", self)
        self.quit_action.setShortcut(QKeySequence.Quit) # Ctrl+Q
        self.quit_action.setStatusTip("Fechar a aplicação")

        # Ações de Paciente
        self.new_paciente_action = QAction(QIcon(f"{icon_path}add_user.png"), "&Novo Paciente...", self)
        self.new_paciente_action.setShortcut("Ctrl+N")
        self.new_paciente_action.setStatusTip("Cadastrar um novo paciente")

        self.edit_paciente_action = QAction(QIcon(f"{icon_path}edit_user.png"), "&Editar Paciente...", self)
        self.edit_paciente_action.setShortcut("Ctrl+E")
        self.edit_paciente_action.setStatusTip("Editar o paciente selecionado")
        self.edit_paciente_action.setEnabled(False) # Habilitar quando um paciente for selecionado

        self.delete_paciente_action = QAction(QIcon(f"{icon_path}delete_user.png"), "&Excluir Paciente", self)
        self.delete_paciente_action.setShortcut(QKeySequence.Delete)
        self.delete_paciente_action.setStatusTip("Excluir o paciente selecionado")
        self.delete_paciente_action.setEnabled(False) # Habilitar quando um paciente for selecionado

        # Ações de Avaliação (Adicionado)
        self.new_avaliacao_action = QAction(QIcon(f"{icon_path}add_assessment.png"), "Nova A&valiação...", self)
        self.new_avaliacao_action.setStatusTip("Registrar uma nova avaliação para o paciente selecionado")
        self.new_avaliacao_action.setEnabled(False) # Habilitar quando um paciente for selecionado
        
        self.view_avaliacoes_action = QAction(QIcon(f"{icon_path}view_assessment.png"), "&Ver Avaliações...", self)
        self.view_avaliacoes_action.setStatusTip("Visualizar histórico de avaliações do paciente selecionado")
        self.view_avaliacoes_action.setEnabled(False) # Habilitar quando um paciente for selecionado

        # Ações de Plano Alimentar
        self.new_plano_action = QAction(QIcon(f"{icon_path}add_plan.png"), "Novo &Plano Alimentar...", self)
        self.new_plano_action.setStatusTip("Criar um novo plano alimentar para o paciente selecionado")
        self.new_plano_action.setEnabled(False) # Habilitar quando um paciente for selecionado
        
        self.view_planos_action = QAction(QIcon(f"{icon_path}view_plan.png"), "Ver Pla&nos...", self)
        self.view_planos_action.setStatusTip("Visualizar planos alimentares do paciente selecionado")
        self.view_planos_action.setEnabled(False) # Habilitar quando um paciente for selecionado

        # Ações de Ferramentas (Adicionado)
        self.manage_alimentos_action = QAction(QIcon(f"{icon_path}manage_food.png"), "Gerenciar &Alimentos...", self)
        self.manage_alimentos_action.setStatusTip("Abrir o banco de dados de alimentos")

        # Ações de Ajuda
        self.about_action = QAction("&Sobre...", self)
        self.about_action.setStatusTip("Mostrar informações sobre a aplicação")

    def _create_menu_bar(self):
        """Cria a barra de menus."""
        menu_bar = self.menuBar()

        # Menu Arquivo
        file_menu = menu_bar.addMenu("&Arquivo")
        file_menu.addAction(self.quit_action)

        # Menu Pacientes
        pacientes_menu = menu_bar.addMenu("&Pacientes")
        pacientes_menu.addAction(self.new_paciente_action)
        pacientes_menu.addAction(self.edit_paciente_action)
        pacientes_menu.addAction(self.delete_paciente_action)
        pacientes_menu.addSeparator()
        pacientes_menu.addAction(self.new_avaliacao_action)
        pacientes_menu.addAction(self.view_avaliacoes_action)
        pacientes_menu.addSeparator()
        pacientes_menu.addAction(self.new_plano_action)
        pacientes_menu.addAction(self.view_planos_action)

        # Menu Ferramentas (Adicionado)
        tools_menu = menu_bar.addMenu("&Ferramentas")
        tools_menu.addAction(self.manage_alimentos_action)
        # Adicionar outras ferramentas (Configurações, Backup, etc.) aqui

        # Menu Ajuda
        help_menu = menu_bar.addMenu("A&juda")
        help_menu.addAction(self.about_action)

    def _create_tool_bar(self):
        """Cria a barra de ferramentas."""
        tool_bar = QToolBar("Barra de Ferramentas Principal")
        tool_bar.setIconSize(QSize(24, 24)) # Tamanho dos ícones
        self.addToolBar(Qt.TopToolBarArea, tool_bar)

        tool_bar.addAction(self.new_paciente_action)
        tool_bar.addAction(self.edit_paciente_action)
        tool_bar.addAction(self.delete_paciente_action)
        tool_bar.addSeparator()
        tool_bar.addAction(self.new_avaliacao_action)
        tool_bar.addAction(self.view_avaliacoes_action)
        tool_bar.addSeparator()
        tool_bar.addAction(self.new_plano_action)
        tool_bar.addAction(self.view_planos_action)
        tool_bar.addSeparator()
        tool_bar.addAction(self.manage_alimentos_action)

    def _create_status_bar(self):
        """Cria a barra de status."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto", 3000) # Mensagem inicial

    def _create_central_widget(self):
        """Cria o widget central (área principal com a tabela)."""
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10) # Margens internas

        # Tabela de Pacientes
        self.pacientes_table_view = QTableView()
        layout.addWidget(self.pacientes_table_view)

        # Configurações da Tabela (exemplo)
        self.pacientes_table_view.setSelectionBehavior(QAbstractItemView.SelectRows) # Selecionar linha inteira
        self.pacientes_table_view.setSelectionMode(QAbstractItemView.SingleSelection) # Apenas uma seleção
        self.pacientes_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers) # Não editável diretamente
        self.pacientes_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Colunas esticam
        self.pacientes_table_view.verticalHeader().setVisible(False) # Esconder cabeçalho vertical (números das linhas)
        self.pacientes_table_view.setAlternatingRowColors(True) # Cores alternadas
        self.pacientes_table_view.setSortingEnabled(True) # Habilitar ordenação

        self.setCentralWidget(central_widget)

    # --- Métodos de Atualização da UI (serão chamados pelo Controller) ---

    def set_status_message(self, message: str, timeout: int = 0):
        """Exibe uma mensagem na barra de status."""
        self.status_bar.showMessage(message, timeout)

    def update_paciente_context_actions(self, enabled: bool):
        """Habilita ou desabilita ações que dependem de um paciente selecionado."""
        self.edit_paciente_action.setEnabled(enabled)
        self.delete_paciente_action.setEnabled(enabled)
        self.new_avaliacao_action.setEnabled(enabled)
        self.view_avaliacoes_action.setEnabled(enabled)
        self.new_plano_action.setEnabled(enabled)
        self.view_planos_action.setEnabled(enabled)

# Bloco para testar a janela isoladamente (opcional)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Forçar um estilo visual (opcional, pode variar entre sistemas)
    # app.setStyle(\"Fusion\") 
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())

