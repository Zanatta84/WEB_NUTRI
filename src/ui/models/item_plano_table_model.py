# src/ui/models/item_plano_table_model.py

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List, Any, Optional

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import ItemPlanoAlimentar
except ImportError:
    # Fallback
    from src.core.models import ItemPlanoAlimentar

class ItemPlanoTableModel(QAbstractTableModel):
    """Modelo de tabela para exibir itens de um plano alimentar."""
    
    # Definir cabeçalhos das colunas
    HEADERS = ["Refeição", "Alimento", "Qtd", "Unidade", "Kcal", "CHO (g)", "PTN (g)", "LIP (g)"]
    
    def __init__(self, data: List[ItemPlanoAlimentar] = None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else []

    def rowCount(self, parent=QModelIndex()) -> int:
        """Retorna o número de linhas (itens)."""
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        """Retorna o número de colunas."""
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """Retorna os dados para um índice específico e role."""
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        item = self._data[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0: return item.refeicao
            if column == 1: return item.nome_alimento # Usar nome cacheado
            if column == 2: return f"{item.quantidade:.2f}" # Formatar quantidade
            if column == 3: return item.unidade_medida
            # Exibir nutrientes calculados
            if column == 4: return f"{item.kcal_calculado:.1f}" if item.kcal_calculado is not None else "-"
            if column == 5: return f"{item.cho_calculado:.1f}" if item.cho_calculado is not None else "-"
            if column == 6: return f"{item.ptn_calculado:.1f}" if item.ptn_calculado is not None else "-"
            if column == 7: return f"{item.lip_calculado:.1f}" if item.lip_calculado is not None else "-"
            
        elif role == Qt.TextAlignmentRole:
            # Alinhar números à direita
            if column in [2, 4, 5, 6, 7]:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        """Retorna os dados do cabeçalho."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def setData(self, data: List[ItemPlanoAlimentar]):
        """Define os dados do modelo e notifica a view."""
        self.beginResetModel()
        self._data = data if data is not None else []
        self.endResetModel()

    def getItemAtRow(self, row: int) -> Optional[ItemPlanoAlimentar]:
        """Retorna o objeto ItemPlanoAlimentar para uma dada linha."""
        if 0 <= row < self.rowCount():
            return self._data[row]
        return None

    def insertRow(self, item: ItemPlanoAlimentar, row: int = -1) -> bool:
        """Insere um novo item no modelo."""
        if row == -1:
            row = self.rowCount()
            
        self.beginInsertRows(QModelIndex(), row, row)
        self._data.insert(row, item)
        self.endInsertRows()
        return True

    def removeRow(self, row: int, parent=QModelIndex()) -> bool:
        """Remove uma linha (item) do modelo."""
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(parent, row, row)
            del self._data[row]
            self.endRemoveRows()
            # Emitir dataChanged aqui pode não ser necessário se rowsRemoved for suficiente
            # self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))
            return True
        return False

    def updateRow(self, row: int, item: ItemPlanoAlimentar) -> bool:
        """Atualiza os dados de uma linha existente."""
        if 0 <= row < self.rowCount():
            self._data[row] = item
            # Notifica a view que os dados da linha inteira mudaram
            first_col_index = self.index(row, 0)
            last_col_index = self.index(row, self.columnCount() - 1)
            self.dataChanged.emit(first_col_index, last_col_index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    # TODO: Implementar sort() se necessário para ordenação personalizada
    # def sort(self, column, order): ...

