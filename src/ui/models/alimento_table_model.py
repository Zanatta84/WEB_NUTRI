# src/ui/models/alimento_table_model.py

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List, Any, Optional

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import Alimento
except ImportError:
    from src.core.models import Alimento

class AlimentoTableModel(QAbstractTableModel):
    """Modelo de dados para exibir Alimentos em uma QTableView."""
    
    # Define os cabeçalhos das colunas (ajustar conforme necessário)
    HEADERS = ["ID", "Nome", "Grupo", "Kcal", "CHO", "PTN", "LIP", "Unidade"]

    def __init__(self, data: Optional[List[Alimento]] = None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        if not index.isValid(): return None
        row = index.row()
        col = index.column()
        alimento = self._data[row]

        if role == Qt.DisplayRole:
            if col == 0: return alimento.id
            if col == 1: return alimento.nome
            if col == 2: return alimento.grupo
            if col == 3: return f"{alimento.kcal_por_unidade:.1f}" if alimento.kcal_por_unidade is not None else "-"
            if col == 4: return f"{alimento.cho_por_unidade:.1f}" if alimento.cho_por_unidade is not None else "-"
            if col == 5: return f"{alimento.ptn_por_unidade:.1f}" if alimento.ptn_por_unidade is not None else "-"
            if col == 6: return f"{alimento.lip_por_unidade:.1f}" if alimento.lip_por_unidade is not None else "-"
            if col == 7: return f"/{alimento.unidade_padrao}"
            return None
        
        # Alinhar números à direita
        if role == Qt.TextAlignmentRole and col >= 3 and col <= 6:
             return Qt.AlignRight | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def setData(self, data: List[Alimento]):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def getAlimentoAtRow(self, row: int) -> Optional[Alimento]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
    
    # Necessário para ordenação
    def sort(self, column: int, order: Qt.SortOrder):
        self.layoutAboutToBeChanged.emit()
        try:
            key = None
            if column == 0: key = lambda x: x.id or 0
            elif column == 1: key = lambda x: x.nome or ""
            elif column == 2: key = lambda x: x.grupo or ""
            elif column == 3: key = lambda x: x.kcal_por_unidade or -1
            elif column == 4: key = lambda x: x.cho_por_unidade or -1
            elif column == 5: key = lambda x: x.ptn_por_unidade or -1
            elif column == 6: key = lambda x: x.lip_por_unidade or -1
            elif column == 7: key = lambda x: x.unidade_padrao or ""
            
            if key:
                self._data.sort(key=key, reverse=(order == Qt.DescendingOrder))
            else: # Fallback para não quebrar se coluna não for ordenável
                 pass 
        except Exception as e:
            print(f"Erro ao ordenar: {e}") # Logar erro
        finally:
            self.layoutChanged.emit()

