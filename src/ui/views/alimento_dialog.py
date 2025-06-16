# src/ui/views/alimento_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QAbstractItemView, QHeaderView, QMessageBox, QDialogButtonBox,
    QLineEdit, QLabel, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Slot, Qt
from typing import Optional

# Tenta importar de forma relativa primeiro
try:
    from ..models.alimento_table_model import AlimentoTableModel # Criaremos este modelo
    from ...core.repositories import AlimentoRepository
    from ...core.models import Alimento
    # Importar diálogo de cadastro/edição de alimento (a ser criado)
    from .cadastro_alimento_dialog import CadastroAlimentoDialog 
except ImportError:
    # Fallback
    from src.ui.models.alimento_table_model import AlimentoTableModel
    from src.core.repositories import AlimentoRepository
    from src.core.models import Alimento
    from src.ui.views.cadastro_alimento_dialog import CadastroAlimentoDialog

class AlimentoDialog(QDialog):
    """Diálogo para gerenciar o banco de dados de alimentos."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Alimentos")
        self.setMinimumSize(700, 500)

        # --- Camada de Dados --- 
        self.alimento_repo = AlimentoRepository()
        self.table_model = AlimentoTableModel()

        # --- Widgets --- 
        self.search_label = QLabel("Buscar Alimento:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Digite parte do nome...")
        
        self.alimentos_table_view = QTableView()
        self.setup_table_view()

        self.add_button = QPushButton("&Adicionar Novo")
        self.edit_button = QPushButton("&Editar Selecionado")
        self.delete_button = QPushButton("E&xcluir Selecionado")
        self.close_button = QPushButton("&Fechar")

        # --- Layout --- 
        layout = QVBoxLayout(self)
        
        # Layout de busca
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Tabela
        layout.addWidget(self.alimentos_table_view)

        # Layout de botões
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        # --- Conexões --- 
        self.search_edit.textChanged.connect(self._handle_search)
        self.add_button.clicked.connect(self._handle_add)
        self.edit_button.clicked.connect(self._handle_edit)
        self.delete_button.clicked.connect(self._handle_delete)
        self.close_button.clicked.connect(self.accept) # Fecha o diálogo
        self.alimentos_table_view.doubleClicked.connect(self._handle_edit) # Duplo clique para editar
        self.alimentos_table_view.selectionModel().selectionChanged.connect(self._update_button_states)

        # --- Inicialização --- 
        self.alimentos_table_view.setModel(self.table_model)
        self._load_alimentos()
        self._update_button_states() # Estado inicial dos botões

    def setup_table_view(self):
        """Configura a aparência da tabela de alimentos."""
        self.alimentos_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.alimentos_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.alimentos_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.alimentos_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Esticar colunas
        # Ajustar tamanho de colunas específicas se necessário
        # self.alimentos_table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID
        # self.alimentos_table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive) # Nome
        self.alimentos_table_view.verticalHeader().setVisible(False)
        self.alimentos_table_view.setAlternatingRowColors(True)
        self.alimentos_table_view.setSortingEnabled(True) # Habilitar ordenação

    @Slot()
    def _load_alimentos(self, search_term: str = ""):
        """Carrega ou filtra os alimentos do repositório."""
        try:
            if search_term:
                alimentos = self.alimento_repo.search_by_name(search_term)
            else:
                alimentos = self.alimento_repo.get_all()
            self.table_model.setData(alimentos)
            # Restaurar ordenação após resetar modelo
            header = self.alimentos_table_view.horizontalHeader()
            self.table_model.sort(header.sortIndicatorSection(), header.sortIndicatorOrder())
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar os alimentos:\n{e}")

    @Slot(str)
    def _handle_search(self, text: str):
        """Filtra a lista de alimentos conforme o texto digitado."""
        self._load_alimentos(search_term=text.strip())

    @Slot()
    def _update_button_states(self):
        """Atualiza o estado (habilitado/desabilitado) dos botões Editar/Excluir."""
        has_selection = bool(self.alimentos_table_view.selectionModel().selectedRows())
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_alimento(self) -> Optional[Alimento]:
        """Retorna o objeto Alimento selecionado na tabela."""
        selected_rows = self.alimentos_table_view.selectionModel().selectedRows()
        if not selected_rows:
            return None
        selected_row_index = selected_rows[0].row()
        # Mapear índice da view para índice do modelo (considerando ordenação/filtragem)
        source_index = self.alimentos_table_view.model().index(selected_row_index, 0) 
        # Se estiver usando QSortFilterProxyModel, precisaria mapear para a fonte:
        # source_index = self.proxy_model.mapToSource(source_index)
        # row = source_index.row()
        # return self.table_model.getAlimentoAtRow(row)
        return self.table_model.getAlimentoAtRow(selected_row_index) # Simplificado sem proxy

    @Slot()
    def _handle_add(self):
        """Abre o diálogo para adicionar um novo alimento."""
        dialog = CadastroAlimentoDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            novo_alimento_data = dialog.get_data()
            alimento = Alimento(**novo_alimento_data)
            try:
                alimento_id = self.alimento_repo.add(alimento)
                if alimento_id:
                    self._load_alimentos(self.search_edit.text().strip()) # Recarrega com filtro atual
                    QMessageBox.information(self, "Sucesso", "Novo alimento adicionado com sucesso!")
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível adicionar o alimento (verifique se o nome já existe).")
            except Exception as e:
                 QMessageBox.critical(self, "Erro Crítico", f"Erro ao adicionar alimento:\n{e}")

    @Slot()
    def _handle_edit(self):
        """Abre o diálogo para editar o alimento selecionado."""
        alimento_selecionado = self._get_selected_alimento()
        if not alimento_selecionado:
            QMessageBox.warning(self, "Atenção", "Selecione um alimento para editar.")
            return

        dialog = CadastroAlimentoDialog(alimento=alimento_selecionado, parent=self)
        if dialog.exec() == QDialog.Accepted:
            dados_atualizados = dialog.get_data()
            alimento_atualizado = Alimento(id=alimento_selecionado.id, **dados_atualizados)
            try:
                if self.alimento_repo.update(alimento_atualizado):
                    self._load_alimentos(self.search_edit.text().strip()) # Recarrega com filtro atual
                    QMessageBox.information(self, "Sucesso", "Alimento atualizado com sucesso!")
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível atualizar o alimento (verifique se o nome já existe).")
            except Exception as e:
                 QMessageBox.critical(self, "Erro Crítico", f"Erro ao atualizar alimento:\n{e}")

    @Slot()
    def _handle_delete(self):
        """Exclui o alimento selecionado após confirmação."""
        alimento_selecionado = self._get_selected_alimento()
        if not alimento_selecionado or alimento_selecionado.id is None:
            QMessageBox.warning(self, "Atenção", "Selecione um alimento para excluir.")
            return

        confirm = QMessageBox.question(self, "Confirmar Exclusão", 
                                       f"Tem certeza que deseja excluir o alimento \"{alimento_selecionado.nome}\"?\n\nAVISO: A exclusão falhará se este alimento estiver sendo usado em algum plano alimentar.",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if confirm == QMessageBox.Yes:
            try:
                if self.alimento_repo.delete(alimento_selecionado.id):
                    self._load_alimentos(self.search_edit.text().strip()) # Recarrega com filtro atual
                    QMessageBox.information(self, "Sucesso", "Alimento excluído com sucesso!")
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível excluir o alimento. Verifique se ele não está sendo usado em planos alimentares.")
            except Exception as e:
                 QMessageBox.critical(self, "Erro Crítico", f"Erro ao excluir alimento:\n{e}")

# Bloco para testar o diálogo isoladamente
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    # Precisa criar os arquivos dependentes vazios ou com mocks
    # ou garantir que o DB seja inicializado
    try:
        # Mock básico para o modelo de tabela
        class MockAlimentoTableModel:
            def __init__(self, data=None):
                self._data = data or []
            def setData(self, data):
                print(f"Setting data: {len(data)} items")
                self._data = data
            def getAlimentoAtRow(self, row):
                return self._data[row] if 0 <= row < len(self._data) else None
            def rowCount(self, parent=None): return len(self._data)
            def columnCount(self, parent=None): return 1 # Dummy
            def data(self, index, role=Qt.DisplayRole): return None
            def headerData(self, section, orientation, role=Qt.DisplayRole): return None
            def sort(self, col, order): pass
            def index(self, row, col, parent=None): return QModelIndex() # Dummy
        
        # Mock para o diálogo de cadastro
        class MockCadastroAlimentoDialog:
            def __init__(self, alimento=None, parent=None): self.alimento = alimento
            def exec(self): return QDialog.Accepted # Simula salvar
            def get_data(self): return {"nome": "Alimento Mock", "kcal_por_unidade": 100} if not self.alimento else {"nome": self.alimento.nome + " Editado", "kcal_por_unidade": 110}
        
        # Substituir as importações reais pelos mocks
        AlimentoTableModel = MockAlimentoTableModel
        CadastroAlimentoDialog = MockCadastroAlimentoDialog
        
        # Inicializar DB se possível
        try:
            from src.core import database
            database.initialize_database()
        except Exception as db_err:
            print(f"WARN: Não foi possível inicializar DB para teste: {db_err}")

    except ImportError as import_err:
        print(f"WARN: Mocks não puderam ser definidos completamente: {import_err}")
        # Sair se não conseguir importar o essencial
        sys.exit(1)

    app = QApplication(sys.argv)
    dialog = AlimentoDialog()
    dialog.show()
    sys.exit(app.exec())

