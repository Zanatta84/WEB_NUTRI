# src/ui/views/view_planos_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QDialogButtonBox, QMessageBox, QLabel, QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Slot, Qt, QDateTime, QAbstractTableModel, QModelIndex
from typing import List, Optional, Any
import logging

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import Paciente, PlanoAlimentar
    from ...core.repositories import PlanoAlimentarRepository
except ImportError:
    # Fallback
    from src.core.models import Paciente, PlanoAlimentar
    from src.core.repositories import PlanoAlimentarRepository

# --- Modelo de Tabela para Planos Alimentares ---
class PlanoAlimentarTableModel(QAbstractTableModel):
    HEADERS = ["Nome do Plano", "Objetivo", "Meta Kcal", "Data Criação"]

    def __init__(self, data: List[PlanoAlimentar] = None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        plano = self._data[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0: return plano.nome_plano
            if column == 1: return plano.objetivo or "-"
            if column == 2: return f"{plano.meta_kcal:.0f} kcal" if plano.meta_kcal is not None else "-"
            if column == 3:
                try:
                    dt_obj = QDateTime.fromString(plano.data_criacao, Qt.ISODate)
                    return dt_obj.toString("dd/MM/yyyy HH:mm") if dt_obj.isValid() else plano.data_criacao
                except:
                    return plano.data_criacao

        elif role == Qt.TextAlignmentRole:
            if column == 2: # Meta Kcal
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def setData(self, data: List[PlanoAlimentar]):
        self.beginResetModel()
        self._data = data if data is not None else []
        self.endResetModel()

    def getPlanoAtRow(self, row: int) -> Optional[PlanoAlimentar]:
        if 0 <= row < self.rowCount():
            return self._data[row]
        return None

# --- Diálogo de Visualização --- 
class ViewPlanosDialog(QDialog):
    """Diálogo para visualizar e gerenciar os planos alimentares de um paciente."""
    def __init__(self, paciente: Paciente, parent=None):
        super().__init__(parent)
        self.paciente = paciente
        self.plano_repo = PlanoAlimentarRepository()
        self.planos: List[PlanoAlimentar] = []
        self.selected_plano: Optional[PlanoAlimentar] = None # Para retornar qual editar/excluir

        self.setWindowTitle(f"Planos Alimentares - {self.paciente.nome_completo}")
        self.setMinimumSize(700, 400)

        # --- Modelo e Tabela --- 
        self.table_model = PlanoAlimentarTableModel()
        self.table_view = QTableView()
        self.setup_table_view()
        self.table_view.setModel(self.table_model)

        # --- Botões --- 
        self.edit_button = QPushButton("Editar Selecionado")
        self.delete_button = QPushButton("Excluir Selecionado")
        self.close_button = QPushButton("Fechar")
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.close_button)

        # --- Layout --- 
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel(f"<b>Planos Alimentares para:</b> {self.paciente.nome_completo}"))
        main_layout.addWidget(self.table_view)
        main_layout.addLayout(button_layout)

        # --- Conexões --- 
        self.close_button.clicked.connect(self.reject) # Fechar simplesmente rejeita
        self.edit_button.clicked.connect(self._handle_edit)
        self.delete_button.clicked.connect(self._handle_delete)
        self.table_view.selectionModel().selectionChanged.connect(self._update_button_states)
        self.table_view.doubleClicked.connect(self._handle_edit) # Duplo clique edita

        # --- Inicialização --- 
        self._load_data()
        self._update_button_states()

    def setup_table_view(self):
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Ajustar colunas específicas se necessário
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive) # Nome pode ser longo
        header.setSectionResizeMode(1, QHeaderView.Interactive) # Objetivo pode ser longo
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Meta Kcal
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Data
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.sortByColumn(3, Qt.DescendingOrder) # Ordenar por data mais recente

    def _load_data(self):
        logging.info(f"Carregando planos alimentares para paciente ID {self.paciente.id}")
        try:
            self.planos = self.plano_repo.get_by_paciente_id(self.paciente.id)
            self.table_model.setData(self.planos)
            logging.info(f"{len(self.planos)} planos carregados.")
            if not self.planos:
                 QMessageBox.information(self, "Sem Planos", "Nenhum plano alimentar encontrado para este paciente.")
        except Exception as e:
            logging.exception("Erro ao carregar planos alimentares:")
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar os planos alimentares:\n{e}")
            self.reject() # Fecha o diálogo se houver erro

    def _get_selected_plano(self) -> Optional[PlanoAlimentar]:
        """Retorna o PlanoAlimentar selecionado na tabela."""
        selected_rows = self.table_view.selectionModel().selectedRows()
        if not selected_rows: return None
        return self.table_model.getPlanoAtRow(selected_rows[0].row())

    @Slot()
    def _update_button_states(self):
        has_selection = bool(self.table_view.selectionModel().selectedRows())
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    @Slot()
    def _handle_edit(self):
        """Marca o plano selecionado para edição e aceita o diálogo."""
        self.selected_plano = self._get_selected_plano()
        if self.selected_plano:
            logging.info(f"Plano ID {self.selected_plano.id} selecionado para edição.")
            self.accept() # Aceita o diálogo para sinalizar a edição
        else:
            QMessageBox.warning(self, "Atenção", "Selecione um plano na tabela para editar.")

    @Slot()
    def _handle_delete(self):
        """Exclui o plano selecionado após confirmação."""
        plano_a_excluir = self._get_selected_plano()
        if not plano_a_excluir or plano_a_excluir.id is None:
            QMessageBox.warning(self, "Atenção", "Selecione um plano na tabela para excluir.")
            return

        confirm = QMessageBox.question(self, "Confirmar Exclusão", 
                                       f"Tem certeza que deseja excluir o plano \"{plano_a_excluir.nome_plano}\"?\n\nATENÇÃO: Todos os itens deste plano também serão excluídos.",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            logging.info(f"Excluindo plano ID {plano_a_excluir.id}")
            try:
                if self.plano_repo.delete(plano_a_excluir.id):
                    logging.info("Plano excluído com sucesso.")
                    self._load_data() # Recarrega a lista
                    self._update_button_states() # Atualiza botões
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível excluir o plano (repositório retornou falso).")
            except Exception as e:
                logging.exception("Erro ao excluir plano alimentar:")
                QMessageBox.critical(self, "Erro", f"Erro ao excluir o plano:\n{e}")

    def get_selected_plano_for_edit(self) -> Optional[PlanoAlimentar]:
        """Retorna o plano que foi selecionado para edição (se o diálogo foi aceito)."""
        return self.selected_plano

# Bloco para teste isolado (opcional)
# if __name__ == '__main__':
#     import sys
#     from PySide6.QtWidgets import QApplication
#     # Mock Paciente e PlanoAlimentarRepository para teste
#     class MockPaciente(Paciente):
#         def __init__(self):
#             super().__init__(id=1, nome_completo="Paciente Teste", data_nascimento="2000-01-01")
#     class MockPlanoAlimentarRepository:
#         def get_by_paciente_id(self, paciente_id):
#             return [
#                 PlanoAlimentar(id=1, paciente_id=1, nome_plano="Plano Inicial", objetivo="Ganho de Massa", data_criacao="2024-05-20 11:00:00", meta_kcal=2500),
#                 PlanoAlimentar(id=2, paciente_id=1, nome_plano="Plano Manutenção", objetivo="Manter Peso", data_criacao="2024-04-10 15:30:00")
#             ]
#         def delete(self, plano_id):
#             print(f"Simulando exclusão do plano ID {plano_id}")
#             return True

#     app = QApplication(sys.argv)
#     paciente_teste = MockPaciente()
#     dialog = ViewPlanosDialog(paciente_teste)
#     dialog.plano_repo = MockPlanoAlimentarRepository() # Inject mock
#     dialog._load_data()
#     if dialog.exec() == QDialog.Accepted:
#         plano_edit = dialog.get_selected_plano_for_edit()
#         if plano_edit:
#             print(f"Usuário selecionou para editar: {plano_edit.nome_plano}")
#     sys.exit()

