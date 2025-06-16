# src/ui/views/alimento_search_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QTableView, QAbstractItemView, QHeaderView, QPushButton,
    QDialogButtonBox, QDoubleSpinBox, QComboBox, QMessageBox,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Slot, Qt
from typing import Optional, Tuple

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import Alimento
    from ...core.repositories import AlimentoRepository
    from ..models.alimento_table_model import AlimentoTableModel # Reutilizar modelo
except ImportError:
    # Fallback
    from src.core.models import Alimento
    from src.core.repositories import AlimentoRepository
    from src.ui.models.alimento_table_model import AlimentoTableModel

class AlimentoSearchDialog(QDialog):
    """Diálogo para buscar e selecionar um alimento, e definir quantidade/unidade."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar e Adicionar Alimento")
        self.setMinimumSize(650, 450)

        self.selected_alimento: Optional[Alimento] = None
        self.quantidade: float = 0.0
        self.unidade: str = ""

        # --- Camada de Dados --- 
        self.alimento_repo = AlimentoRepository()
        self.table_model = AlimentoTableModel() # Reutiliza o modelo de exibição

        # --- Widgets --- 
        self.search_label = QLabel("Buscar Alimento:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Digite parte do nome...")
        
        self.alimentos_table_view = QTableView()
        self.setup_table_view()
        self.alimentos_table_view.setModel(self.table_model)

        # Campos para Quantidade e Unidade
        self.quantidade_label = QLabel("Quantidade:")
        self.quantidade_spinbox = QDoubleSpinBox()
        self.quantidade_spinbox.setRange(0.01, 9999.99)
        self.quantidade_spinbox.setDecimals(2)
        self.quantidade_spinbox.setValue(1.0) # Valor padrão
        self.quantidade_spinbox.setEnabled(False) # Habilitar ao selecionar alimento

        self.unidade_label = QLabel("Unidade:")
        self.unidade_combo = QComboBox()
        # Popular com unidades comuns + unidade padrão do alimento selecionado
        self.unidade_combo.addItems(["g", "ml", "unidade", "fatia", "colher de sopa", "colher de chá", "xícara", "copo", "pedaço"])
        self.unidade_combo.setEditable(True)
        self.unidade_combo.setEnabled(False) # Habilitar ao selecionar alimento

        # Botões OK/Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("Adicionar")
        self.button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False) # Habilitar ao selecionar

        # --- Layout --- 
        layout = QVBoxLayout(self)
        
        # Layout de busca
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Tabela
        layout.addWidget(self.alimentos_table_view)

        # Layout Quantidade/Unidade
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(self.quantidade_label)
        qty_layout.addWidget(self.quantidade_spinbox)
        qty_layout.addWidget(self.unidade_label)
        qty_layout.addWidget(self.unidade_combo)
        qty_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(qty_layout)

        # Botões
        layout.addWidget(self.button_box)

        # --- Conexões --- 
        self.search_edit.textChanged.connect(self._handle_search)
        self.alimentos_table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.alimentos_table_view.doubleClicked.connect(self.accept) # Duplo clique confirma
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # --- Inicialização --- 
        self._load_alimentos() # Carrega todos inicialmente

    def setup_table_view(self):
        """Configura a aparência da tabela de alimentos (similar ao AlimentoDialog)."""
        self.alimentos_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.alimentos_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.alimentos_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.alimentos_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alimentos_table_view.verticalHeader().setVisible(False)
        self.alimentos_table_view.setAlternatingRowColors(True)
        self.alimentos_table_view.setSortingEnabled(True)
        # Ajustar colunas se necessário (ex: esconder ID?)
        # self.alimentos_table_view.setColumnHidden(0, True)

    @Slot()
    def _load_alimentos(self, search_term: str = ""):
        """Carrega ou filtra os alimentos do repositório."""
        try:
            if search_term:
                alimentos = self.alimento_repo.search_by_name(search_term)
            else:
                # Pode ser útil limitar a carga inicial se o banco for muito grande
                alimentos = self.alimento_repo.get_all() # Ou get_all(limit=100)
            self.table_model.setData(alimentos)
            # Restaurar ordenação
            header = self.alimentos_table_view.horizontalHeader()
            self.table_model.sort(header.sortIndicatorSection(), header.sortIndicatorOrder())
            self._clear_selection_and_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar os alimentos:\n{e}")

    @Slot(str)
    def _handle_search(self, text: str):
        """Filtra a lista de alimentos conforme o texto digitado."""
        self._load_alimentos(search_term=text.strip())

    def _clear_selection_and_inputs(self):
        """Limpa a seleção e desabilita campos de quantidade/unidade."""
        self.alimentos_table_view.clearSelection()
        self.selected_alimento = None
        self.quantidade_spinbox.setEnabled(False)
        self.unidade_combo.setEnabled(False)
        self.unidade_combo.setCurrentIndex(0) # Volta para "g" ou primeira opção
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    @Slot('QItemSelection', 'QItemSelection')
    def _on_selection_changed(self, selected, deselected):
        """Chamado quando a seleção na tabela muda."""
        selected_rows = self.alimentos_table_view.selectionModel().selectedRows()
        if selected_rows:
            # Mapear view -> model
            model_index = self.table_model.index(selected_rows[0].row(), 0)
            self.selected_alimento = self.table_model.getAlimentoAtRow(model_index.row())
            if self.selected_alimento:
                self.quantidade_spinbox.setEnabled(True)
                self.unidade_combo.setEnabled(True)
                # Define a unidade padrão do alimento como selecionada
                default_unit = self.selected_alimento.unidade_padrao or "g"
                # Adiciona a unidade padrão se não estiver na lista
                if self.unidade_combo.findText(default_unit) == -1:
                    self.unidade_combo.insertItem(0, default_unit)
                self.unidade_combo.setCurrentText(default_unit)
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
                return # Sai após sucesso
        
        # Se não há seleção válida ou alimento não encontrado
        self._clear_selection_and_inputs()

    @Slot()
    def accept(self):
        """Valida os dados antes de aceitar."""
        if not self.selected_alimento:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um alimento na lista.")
            return
            
        self.quantidade = self.quantidade_spinbox.value()
        self.unidade = self.unidade_combo.currentText().strip()

        if self.quantidade <= 0:
            QMessageBox.warning(self, "Quantidade Inválida", "A quantidade deve ser maior que zero.")
            self.quantidade_spinbox.setFocus()
            return
            
        if not self.unidade:
            QMessageBox.warning(self, "Unidade Inválida", "Selecione ou digite uma unidade de medida.")
            self.unidade_combo.setFocus()
            return

        super().accept()

    def get_selection(self) -> Optional[Tuple[Alimento, float, str]]:
        """Retorna o alimento selecionado, quantidade e unidade."""
        if self.result() == QDialog.Accepted and self.selected_alimento:
            return self.selected_alimento, self.quantidade, self.unidade
        return None

# Bloco para testar o diálogo isoladamente
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    # Inicializar DB se possível para ter dados reais
    try:
        # Adiciona src ao path para importar database
        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), \"..\", \"..\"))
        sys.path.insert(0, src_path)
        from src.core import database
        database.initialize_database()
        # Adicionar alguns alimentos para teste se o banco estiver vazio
        repo = AlimentoRepository()
        if not repo.get_all():
             repo.add(Alimento(nome="Maçã Fuji", grupo="Frutas", unidade_padrao="unidade", kcal_por_unidade=95))
             repo.add(Alimento(nome="Arroz Branco Cozido", grupo="Cereais", unidade_padrao="g", kcal_por_unidade=1.28))
             repo.add(Alimento(nome="Peito de Frango Grelhado", grupo="Carnes", unidade_padrao="g", kcal_por_unidade=1.65))
    except Exception as db_err:
        print(f"WARN: Não foi possível inicializar DB ou adicionar dados: {db_err}")

    app = QApplication(sys.argv)
    dialog = AlimentoSearchDialog()
    if dialog.exec() == QDialog.Accepted:
        selection = dialog.get_selection()
        if selection:
            alimento, qtd, und = selection
            print(f"Selecionado: {alimento.nome}, Qtd: {qtd}, Und: {und}")
        else:
            print("Nenhum alimento selecionado.")
    else:
        print("Busca cancelada.")

    sys.exit()

