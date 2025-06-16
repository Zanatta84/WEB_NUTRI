# src/ui/views/cadastro_alimento_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QComboBox, QTextEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QDoubleSpinBox, QGroupBox
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import Alimento
except ImportError:
    from src.core.models import Alimento

class CadastroAlimentoDialog(QDialog):
    """Diálogo para cadastrar ou editar um alimento."""
    def __init__(self, alimento: Optional[Alimento] = None, parent=None):
        super().__init__(parent)
        self.alimento = alimento # Armazena o alimento se estiver editando
        self.is_editing = alimento is not None

        self.setWindowTitle("Editar Alimento" if self.is_editing else "Novo Alimento")
        self.setMinimumWidth(450)

        # --- Widgets --- 
        self.nome_edit = QLineEdit()
        self.grupo_combo = QComboBox()
        # TODO: Carregar grupos de uma fonte configurável ou do banco?
        self.grupo_combo.addItems(["", "Cereais e Pães", "Verduras e Legumes", "Frutas", 
                                   "Leite e Derivados", "Carnes e Ovos", "Leguminosas", 
                                   "Óleos e Gorduras", "Açúcares e Doces", "Industrializados", "Outros"])
        
        self.unidade_padrao_combo = QComboBox()
        self.unidade_padrao_combo.addItems(["g", "ml", "unidade", "fatia", "colher de sopa", "colher de chá", "xícara", "copo", "pedaço"])
        self.unidade_padrao_combo.setEditable(True) # Permitir unidades customizadas

        # Grupo de Macronutrientes
        macro_group = QGroupBox("Informações Nutricionais (por unidade padrão)")
        macro_layout = QFormLayout(macro_group)
        
        self.kcal_spinbox = QDoubleSpinBox()
        self.kcal_spinbox.setSuffix(" kcal")
        self.kcal_spinbox.setRange(0.0, 9999.0)
        self.kcal_spinbox.setDecimals(1)
        self.kcal_spinbox.setSingleStep(1.0)
        macro_layout.addRow("Energia (Kcal):", self.kcal_spinbox)

        self.cho_spinbox = QDoubleSpinBox()
        self.cho_spinbox.setSuffix(" g")
        self.cho_spinbox.setRange(0.0, 999.0)
        self.cho_spinbox.setDecimals(1)
        self.cho_spinbox.setSingleStep(0.1)
        macro_layout.addRow("Carboidratos (CHO):", self.cho_spinbox)

        self.ptn_spinbox = QDoubleSpinBox()
        self.ptn_spinbox.setSuffix(" g")
        self.ptn_spinbox.setRange(0.0, 999.0)
        self.ptn_spinbox.setDecimals(1)
        self.ptn_spinbox.setSingleStep(0.1)
        macro_layout.addRow("Proteínas (PTN):", self.ptn_spinbox)

        self.lip_spinbox = QDoubleSpinBox()
        self.lip_spinbox.setSuffix(" g")
        self.lip_spinbox.setRange(0.0, 999.0)
        self.lip_spinbox.setDecimals(1)
        self.lip_spinbox.setSingleStep(0.1)
        macro_layout.addRow("Gorduras (LIP):", self.lip_spinbox)

        self.fibras_spinbox = QDoubleSpinBox()
        self.fibras_spinbox.setSuffix(" g")
        self.fibras_spinbox.setRange(0.0, 999.0)
        self.fibras_spinbox.setDecimals(1)
        self.fibras_spinbox.setSingleStep(0.1)
        macro_layout.addRow("Fibras:", self.fibras_spinbox)

        self.sodio_spinbox = QDoubleSpinBox()
        self.sodio_spinbox.setSuffix(" mg")
        self.sodio_spinbox.setRange(0.0, 99999.0)
        self.sodio_spinbox.setDecimals(1)
        self.sodio_spinbox.setSingleStep(1.0)
        macro_layout.addRow("Sódio:", self.sodio_spinbox)

        self.fonte_dados_edit = QLineEdit()
        self.fonte_dados_edit.setPlaceholderText("Ex: TACO, IBGE, Rótulo, etc.")
        self.observacoes_edit = QTextEdit()
        self.observacoes_edit.setPlaceholderText("Medidas caseiras, preparo, etc.")
        self.observacoes_edit.setFixedHeight(60)

        # Botões Salvar/Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        # --- Layout --- 
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        form_layout.addRow("Nome*: ", self.nome_edit)
        form_layout.addRow("Grupo: ", self.grupo_combo)
        form_layout.addRow("Unidade Padrão*: ", self.unidade_padrao_combo)
        
        layout.addLayout(form_layout)
        layout.addWidget(macro_group) # Adiciona o grupo de macros
        
        form_layout_bottom = QFormLayout()
        form_layout_bottom.addRow("Fonte dos Dados: ", self.fonte_dados_edit)
        form_layout_bottom.addRow("Observações: ", self.observacoes_edit)
        layout.addLayout(form_layout_bottom)
        
        layout.addWidget(self.button_box)

        # --- Conexões --- 
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # --- Preencher dados se estiver editando --- 
        if self.is_editing and self.alimento:
            self._populate_form()

    def _populate_form(self):
        """Preenche o formulário com os dados do alimento existente."""
        if not self.alimento: return
        
        self.nome_edit.setText(self.alimento.nome or "")
        self.grupo_combo.setCurrentText(self.alimento.grupo or "")
        self.unidade_padrao_combo.setCurrentText(self.alimento.unidade_padrao or "g")
        self.kcal_spinbox.setValue(self.alimento.kcal_por_unidade or 0.0)
        self.cho_spinbox.setValue(self.alimento.cho_por_unidade or 0.0)
        self.ptn_spinbox.setValue(self.alimento.ptn_por_unidade or 0.0)
        self.lip_spinbox.setValue(self.alimento.lip_por_unidade or 0.0)
        self.fibras_spinbox.setValue(self.alimento.fibras_por_unidade or 0.0)
        self.sodio_spinbox.setValue(self.alimento.sodio_mg_por_unidade or 0.0)
        self.fonte_dados_edit.setText(self.alimento.fonte_dados or "")
        self.observacoes_edit.setText(self.alimento.observacoes or "")

    def get_data(self) -> Dict[str, Any]:
        """Retorna os dados do formulário como um dicionário."""
        # Retorna None para campos numéricos se o valor for zero
        kcal = self.kcal_spinbox.value()
        cho = self.cho_spinbox.value()
        ptn = self.ptn_spinbox.value()
        lip = self.lip_spinbox.value()
        fibras = self.fibras_spinbox.value()
        sodio = self.sodio_spinbox.value()
        
        return {
            "nome": self.nome_edit.text().strip(),
            "grupo": self.grupo_combo.currentText() if self.grupo_combo.currentIndex() > 0 else None,
            "unidade_padrao": self.unidade_padrao_combo.currentText().strip(),
            "kcal_por_unidade": kcal if kcal > 1e-6 else None,
            "cho_por_unidade": cho if cho > 1e-6 else None,
            "ptn_por_unidade": ptn if ptn > 1e-6 else None,
            "lip_por_unidade": lip if lip > 1e-6 else None,
            "fibras_por_unidade": fibras if fibras > 1e-6 else None,
            "sodio_mg_por_unidade": sodio if sodio > 1e-6 else None,
            "fonte_dados": self.fonte_dados_edit.text().strip() or None,
            "observacoes": self.observacoes_edit.toPlainText().strip() or None,
        }

    @Slot()
    def accept(self):
        """Valida os dados antes de aceitar o diálogo."""
        dados = self.get_data()
        
        # Validação básica (campos obrigatórios)
        if not dados["nome"]:
            QMessageBox.warning(self, "Campo Obrigatório", "O nome do alimento é obrigatório.")
            self.nome_edit.setFocus()
            return
            
        if not dados["unidade_padrao"]:
             QMessageBox.warning(self, "Campo Obrigatório", "A unidade padrão do alimento é obrigatória.")
             self.unidade_padrao_combo.setFocus()
             return
        
        # Validação: Pelo menos um macronutriente ou Kcal deve ser informado?
        # if not any([dados["kcal_por_unidade"], dados["cho_por_unidade"], 
        #             dados["ptn_por_unidade"], dados["lip_por_unidade"]]):
        #     QMessageBox.warning(self, "Dados Nutricionais", "Informe pelo menos o valor de Kcal ou de um macronutriente.")
        #     return

        # Se a validação passar, aceita o diálogo
        super().accept()

# Bloco para testar o diálogo isoladamente
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # Teste de Novo Alimento
    dialog_novo = CadastroAlimentoDialog()
    if dialog_novo.exec() == QDialog.Accepted:
        print("Dados Novo Alimento:", dialog_novo.get_data())
    else:
        print("Cadastro de novo alimento cancelado.")

    # Teste de Edição de Alimento (com dados fictícios)
    alimento_existente = Alimento(
        id=101,
        nome="Arroz Branco Cozido",
        grupo="Cereais e Pães",
        unidade_padrao="g",
        kcal_por_unidade=128.0,
        cho_por_unidade=28.1,
        ptn_por_unidade=2.5,
        lip_por_unidade=0.2,
        fonte_dados="TACO"
    )
    dialog_editar = CadastroAlimentoDialog(alimento=alimento_existente)
    if dialog_editar.exec() == QDialog.Accepted:
        print("Dados Alimento Editado:", dialog_editar.get_data())
    else:
        print("Edição de alimento cancelada.")

    sys.exit() # Não iniciar loop de eventos aqui

