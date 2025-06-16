# src/ui/models/paciente_table_model.py

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor
from typing import List, Any, Optional

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import Paciente # Navega dois níveis acima para src/core
except ImportError:
    # Fallback se a estrutura de importação falhar (ex: execução direta)
    # Isso pode exigir ajustar o PYTHONPATH ou a forma como o app é iniciado
    from src.core.models import Paciente 

class PacienteTableModel(QAbstractTableModel):
    """Modelo de dados para exibir Pacientes em uma QTableView."""
    
    # Define os cabeçalhos das colunas
    HEADERS = ["ID", "Nome Completo", "Data Nascimento", "Telefone", "Email"]

    def __init__(self, data: Optional[List[Paciente]] = None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else []

    def rowCount(self, parent=QModelIndex()) -> int:
        """Retorna o número de linhas (pacientes)."""
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        """Retorna o número de colunas."""
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """Retorna os dados para um índice específico e role."""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        paciente = self._data[row]

        if role == Qt.DisplayRole:
            if col == 0: return paciente.id
            if col == 1: return paciente.nome_completo
            if col == 2: return paciente.data_nascimento
            if col == 3: return paciente.telefone
            if col == 4: return paciente.email
            return None
        
        # Exemplo: Adicionar cor de fundo alternada (já feito na view, mas pode ser feito aqui)
        # if role == Qt.BackgroundRole:
        #     if row % 2 == 0:
        #         return QColor(Qt.lightGray).lighter(110)
        #     else:
        #         return QColor(Qt.white)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        """Retorna os dados do cabeçalho."""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if 0 <= section < len(self.HEADERS):
                    return self.HEADERS[section]
        return None

    def setData(self, data: List[Paciente]):
        """Define os dados do modelo e atualiza a view."""
        self.beginResetModel() # Informa à view que o modelo será resetado
        self._data = data
        self.endResetModel() # Informa à view que o reset terminou

    def getPacienteAtRow(self, row: int) -> Optional[Paciente]:
        """Retorna o objeto Paciente na linha especificada."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

