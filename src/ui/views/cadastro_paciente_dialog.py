# src/ui/views/cadastro_paciente_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDateEdit, QComboBox, QTextEdit, QPushButton, 
    QDialogButtonBox, QMessageBox, QLabel # Import QLabel
)
from PySide6.QtCore import QDate, Slot, Qt # Import Qt
from typing import Optional, Dict, Any

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import Paciente
except ImportError:
    from src.core.models import Paciente

class CadastroPacienteDialog(QDialog):
    """Diálogo para cadastrar ou editar um paciente."""
    def __init__(self, paciente: Optional[Paciente] = None, parent=None):
        super().__init__(parent)
        self.paciente = paciente # Armazena o paciente se estiver editando
        self.is_editing = paciente is not None

        self.setWindowTitle("Editar Paciente" if self.is_editing else "Novo Paciente")
        self.setMinimumWidth(450)

        # --- Widgets --- 
        self.nome_completo_edit = QLineEdit()
        self.nome_completo_edit.setPlaceholderText("Nome completo do paciente")
        self.data_nascimento_edit = QDateEdit()
        self.data_nascimento_edit.setDisplayFormat("dd/MM/yyyy")
        self.data_nascimento_edit.setCalendarPopup(True)
        self.data_nascimento_edit.setDate(QDate.currentDate().addYears(-30)) # Data padrão
        self.data_nascimento_edit.setMaximumDate(QDate.currentDate()) # Não permitir data futura
        self.sexo_combo = QComboBox()
        self.sexo_combo.addItems(["", "Masculino", "Feminino", "Outro"])
        self.telefone_edit = QLineEdit()
        self.telefone_edit.setPlaceholderText("(XX) XXXXX-XXXX")
        # TODO: Adicionar máscara QLineEdit.setInputMask("(99) 99999-9999;_)")?
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("exemplo@dominio.com")
        self.endereco_edit = QLineEdit()
        self.endereco_edit.setPlaceholderText("Rua, Número, Bairro, Cidade - Estado")
        self.objetivo_consulta_edit = QLineEdit()
        self.objetivo_consulta_edit.setPlaceholderText("Ex: Perda de peso, Ganho de massa, Reeducação alimentar")
        self.historico_clinico_edit = QTextEdit()
        self.historico_clinico_edit.setPlaceholderText("Detalhes sobre condições pré-existentes, alergias, medicamentos...")
        self.historico_clinico_edit.setFixedHeight(80)
        self.observacoes_edit = QTextEdit()
        self.observacoes_edit.setPlaceholderText("Outras informações relevantes...")
        self.observacoes_edit.setFixedHeight(60)

        # Botões Salvar/Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText("Salvar")
        self.button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")

        # --- Layout --- 
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapLongRows) # Quebrar linhas longas
        form_layout.setLabelAlignment(Qt.AlignRight) # Alinhar labels à direita
        
        # Adicionar asterisco visualmente aos labels obrigatórios
        form_layout.addRow(QLabel("Nome Completo<font color=\"red\">*</font>: "), self.nome_completo_edit)
        form_layout.addRow(QLabel("Data Nascimento<font color=\"red\">*</font>: "), self.data_nascimento_edit)
        form_layout.addRow("Sexo: ", self.sexo_combo)
        form_layout.addRow("Telefone: ", self.telefone_edit)
        form_layout.addRow("Email: ", self.email_edit)
        form_layout.addRow("Endereço: ", self.endereco_edit)
        form_layout.addRow("Objetivo Consulta: ", self.objetivo_consulta_edit)
        form_layout.addRow("Histórico Clínico: ", self.historico_clinico_edit)
        form_layout.addRow("Observações: ", self.observacoes_edit)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        # --- Conexões --- 
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # --- Preencher dados se estiver editando --- 
        if self.is_editing and self.paciente:
            self._populate_form()

    def _populate_form(self):
        """Preenche o formulário com os dados do paciente existente."""
        if not self.paciente: return
        
        self.nome_completo_edit.setText(self.paciente.nome_completo or "")
        try:
            data_nasc = QDate.fromString(self.paciente.data_nascimento or "", "yyyy-MM-dd")
            if data_nasc.isValid():
                self.data_nascimento_edit.setDate(data_nasc)
        except Exception:
            pass # Mantém a data padrão se houver erro
        self.sexo_combo.setCurrentText(self.paciente.sexo or "")
        self.telefone_edit.setText(self.paciente.telefone or "")
        self.email_edit.setText(self.paciente.email or "")
        self.endereco_edit.setText(self.paciente.endereco or "")
        self.objetivo_consulta_edit.setText(self.paciente.objetivo_consulta or "")
        self.historico_clinico_edit.setText(self.paciente.historico_clinico or "")
        self.observacoes_edit.setText(self.paciente.observacoes or "")

    def get_data(self) -> Dict[str, Any]:
        """Retorna os dados do formulário como um dicionário."""
        return {
            "nome_completo": self.nome_completo_edit.text().strip(),
            "data_nascimento": self.data_nascimento_edit.date().toString("yyyy-MM-dd"),
            "sexo": self.sexo_combo.currentText() if self.sexo_combo.currentIndex() > 0 else None,
            "telefone": self.telefone_edit.text().strip() or None,
            "email": self.email_edit.text().strip().lower() or None,
            "endereco": self.endereco_edit.text().strip() or None,
            "objetivo_consulta": self.objetivo_consulta_edit.text().strip() or None,
            "historico_clinico": self.historico_clinico_edit.toPlainText().strip() or None,
            "observacoes": self.observacoes_edit.toPlainText().strip() or None,
        }

    @Slot()
    def accept(self):
        """Valida os dados antes de aceitar o diálogo."""
        dados = self.get_data()
        
        # Validação básica (campos obrigatórios)
        if not dados["nome_completo"]:
            QMessageBox.warning(self, "Campo Obrigatório", "O campo <b>Nome Completo</b> é obrigatório.")
            self.nome_completo_edit.setFocus()
            return
            
        if not dados["data_nascimento"] or not self.data_nascimento_edit.date().isValid():
             QMessageBox.warning(self, "Campo Obrigatório", "O campo <b>Data Nascimento</b> é obrigatório e deve conter uma data válida.")
             self.data_nascimento_edit.setFocus()
             return
        
        # Validação simples de email (se preenchido)
        email = dados["email"]
        if email and ("@" not in email or "." not in email.split("@")[-1]):
             QMessageBox.warning(self, "Formato Inválido", "O formato do <b>Email</b> parece inválido.")
             self.email_edit.setFocus()
             return

        # Se a validação passar, aceita o diálogo
        super().accept()

# Bloco para testar o diálogo isoladamente
# (Omitido para brevidade, igual ao anterior)
# if __name__ == \"__main__\": ...

