# src/ui/views/view_avaliacoes_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QDialogButtonBox, QMessageBox, QLabel, QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Slot, Qt, QDateTime, QAbstractTableModel, QModelIndex
from typing import List, Optional, Any
import logging

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import Paciente, Avaliacao
    from ...core.repositories import AvaliacaoRepository
except ImportError:
    # Fallback
    from src.core.models import Paciente, Avaliacao
    from src.core.repositories import AvaliacaoRepository

# --- Modelo de Tabela para Avaliações ---
class AvaliacaoTableModel(QAbstractTableModel):
    HEADERS = ["Data", "Peso (kg)", "Altura (m)", "IMC", "Cintura (cm)", "Quadril (cm)", "RCQ", "Observações"]

    def __init__(self, data: List[Avaliacao] = None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        aval = self._data[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0:
                try:
                    dt_obj = QDateTime.fromString(aval.data_avaliacao, Qt.ISODate)
                    return dt_obj.toString("dd/MM/yyyy HH:mm") if dt_obj.isValid() else aval.data_avaliacao
                except:
                    return aval.data_avaliacao
            if column == 1: return f"{aval.peso:.2f}" if aval.peso is not None else "-"
            if column == 2: return f"{aval.altura:.2f}" if aval.altura is not None else "-"
            if column == 3: # IMC
                try:
                    imc = aval.peso / (aval.altura ** 2) if aval.peso and aval.altura else None
                    return f"{imc:.1f}" if imc is not None else "-"
                except:
                    return "Erro"
            if column == 4: return f"{aval.circunferencia_cintura:.1f}" if aval.circunferencia_cintura is not None else "-"
            if column == 5: return f"{aval.circunferencia_quadril:.1f}" if aval.circunferencia_quadril is not None else "-"
            if column == 6: # RCQ
                try:
                    rcq = aval.circunferencia_cintura / aval.circunferencia_quadril if aval.circunferencia_cintura and aval.circunferencia_quadril else None
                    return f"{rcq:.2f}" if rcq is not None else "-"
                except:
                    return "Erro"
            if column == 7: return aval.observacoes or ""

        elif role == Qt.TextAlignmentRole:
            if column in [1, 2, 3, 4, 5, 6]: # Alinhar números à direita
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def setData(self, data: List[Avaliacao]):
        self.beginResetModel()
        self._data = data if data is not None else []
        self.endResetModel()

    def getAvaliacaoAtRow(self, row: int) -> Optional[Avaliacao]:
        if 0 <= row < self.rowCount():
            return self._data[row]
        return None

# --- Diálogo de Visualização --- 
class ViewAvaliacoesDialog(QDialog):
    """Diálogo para visualizar o histórico de avaliações de um paciente."""
    def __init__(self, paciente: Paciente, parent=None):
        super().__init__(parent)
        self.paciente = paciente
        self.avaliacao_repo = AvaliacaoRepository()
        self.avaliacoes: List[Avaliacao] = []

        self.setWindowTitle(f"Histórico de Avaliações - {self.paciente.nome_completo}")
        self.setMinimumSize(750, 450)

        # --- Modelo e Tabela --- 
        self.table_model = AvaliacaoTableModel()
        self.table_view = QTableView()
        self.setup_table_view()
        self.table_view.setModel(self.table_model)

        # --- Botões --- 
        # Adicionar botões para Editar/Excluir se necessário no futuro
        # self.edit_button = QPushButton("Editar Selecionada")
        # self.delete_button = QPushButton("Excluir Selecionada")
        self.close_button = QPushButton("Fechar")
        
        # button_layout = QHBoxLayout()
        # button_layout.addStretch()
        # button_layout.addWidget(self.edit_button)
        # button_layout.addWidget(self.delete_button)
        # button_layout.addWidget(self.close_button)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Close).setText("Fechar")

        # --- Layout --- 
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel(f"<b>Histórico de Avaliações para:</b> {self.paciente.nome_completo}"))
        main_layout.addWidget(self.table_view)
        main_layout.addWidget(button_box)
        # main_layout.addLayout(button_layout)

        # --- Conexões --- 
        button_box.rejected.connect(self.reject)
        # self.close_button.clicked.connect(self.reject)
        # self.edit_button.clicked.connect(self._handle_edit)
        # self.delete_button.clicked.connect(self._handle_delete)
        # self.table_view.selectionModel().selectionChanged.connect(self._update_button_states)
        # self.table_view.doubleClicked.connect(self._handle_edit) # Duplo clique edita

        # --- Inicialização --- 
        self._load_data()
        # self._update_button_states()

    def setup_table_view(self):
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_view.horizontalHeader().setStretchLastSection(True) # Estica a última coluna (Observações)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.sortByColumn(0, Qt.DescendingOrder) # Ordenar por data mais recente

    def _load_data(self):
        logging.info(f"Carregando avaliações para paciente ID {self.paciente.id}")
        try:
            self.avaliacoes = self.avaliacao_repo.get_by_paciente_id(self.paciente.id)
            self.table_model.setData(self.avaliacoes)
            logging.info(f"{len(self.avaliacoes)} avaliações carregadas.")
            if not self.avaliacoes:
                 QMessageBox.information(self, "Sem Avaliações", "Nenhuma avaliação encontrada para este paciente.")
        except Exception as e:
            logging.exception("Erro ao carregar avaliações:")
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar as avaliações:\n{e}")
            self.reject() # Fecha o diálogo se houver erro

    # --- Slots para botões (se implementados) ---
    # @Slot()
    # def _update_button_states(self):
    #     has_selection = bool(self.table_view.selectionModel().selectedRows())
    #     self.edit_button.setEnabled(has_selection)
    #     self.delete_button.setEnabled(has_selection)

    # @Slot()
    # def _handle_edit(self):
    #     selected_rows = self.table_view.selectionModel().selectedRows()
    #     if not selected_rows: return
    #     avaliacao_selecionada = self.table_model.getAvaliacaoAtRow(selected_rows[0].row())
    #     if avaliacao_selecionada:
    #         logging.info(f"Editando avaliação ID {avaliacao_selecionada.id}")
    #         # TODO: Abrir AvaliacaoDialog para edição
    #         QMessageBox.information(self, "Editar", "Funcionalidade de editar avaliação ainda não implementada.")

    # @Slot()
    # def _handle_delete(self):
    #     selected_rows = self.table_view.selectionModel().selectedRows()
    #     if not selected_rows: return
    #     avaliacao_selecionada = self.table_model.getAvaliacaoAtRow(selected_rows[0].row())
    #     if avaliacao_selecionada and avaliacao_selecionada.id is not None:
    #         confirm = QMessageBox.question(self, "Confirmar Exclusão", 
    #                                        f"Tem certeza que deseja excluir a avaliação de {avaliacao_selecionada.data_avaliacao}?",
    #                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    #         if confirm == QMessageBox.Yes:
    #             logging.info(f"Excluindo avaliação ID {avaliacao_selecionada.id}")
    #             # TODO: Implementar delete no AvaliacaoRepository e chamar aqui
    #             # try:
    #             #     if self.avaliacao_repo.delete(avaliacao_selecionada.id):
    #             #         self._load_data() # Recarrega
    #             #     else:
    #             #         QMessageBox.warning(self, "Erro", "Não foi possível excluir a avaliação.")
    #             # except Exception as e:
    #             #     QMessageBox.critical(self, "Erro", f"Erro ao excluir: {e}")
    #             QMessageBox.information(self, "Excluir", "Funcionalidade de excluir avaliação ainda não implementada.")

# Bloco para teste isolado (opcional)
# if __name__ == '__main__':
#     import sys
#     from PySide6.QtWidgets import QApplication
#     # Mock Paciente e AvaliacaoRepository para teste
#     class MockPaciente(Paciente):
#         def __init__(self):
#             super().__init__(id=1, nome_completo="Paciente Teste", data_nascimento="2000-01-01")
#     class MockAvaliacaoRepository:
#         def get_by_paciente_id(self, paciente_id):
#             return [
#                 Avaliacao(id=1, paciente_id=1, data_avaliacao="2024-05-27 10:00:00", peso=70.5, altura=1.75),
#                 Avaliacao(id=2, paciente_id=1, data_avaliacao="2024-04-15 09:30:00", peso=72.0, altura=1.75, circunferencia_cintura=85.0)
#             ]

#     app = QApplication(sys.argv)
#     paciente_teste = MockPaciente()
#     dialog = ViewAvaliacoesDialog(paciente_teste)
#     dialog.avaliacao_repo = MockAvaliacaoRepository() # Inject mock
#     dialog._load_data()
#     dialog.exec()
#     sys.exit()

