# src/ui/views/avaliacao_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDateTimeEdit, QDoubleSpinBox, QTextEdit, QPushButton, 
    QDialogButtonBox, QMessageBox, QLabel
)
from PySide6.QtCore import QDateTime, Slot, Qt
from typing import Optional, Dict, Any

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import Avaliacao, Paciente
except ImportError:
    from src.core.models import Avaliacao, Paciente

class AvaliacaoDialog(QDialog):
    """Diálogo para cadastrar ou editar uma avaliação nutricional."""
    def __init__(self, paciente: Paciente, avaliacao: Optional[Avaliacao] = None, parent=None):
        super().__init__(parent)
        self.paciente = paciente # Paciente ao qual a avaliação pertence
        self.avaliacao = avaliacao # Avaliação existente (se editando)
        self.is_editing = avaliacao is not None

        self.setWindowTitle(f"Editar Avaliação - {paciente.nome_completo}" if self.is_editing else f"Nova Avaliação - {paciente.nome_completo}")
        self.setMinimumWidth(500)

        # --- Widgets --- 
        self.paciente_label = QLabel(f"<b>Paciente:</b> {paciente.nome_completo} (ID: {paciente.id})")
        self.data_avaliacao_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.data_avaliacao_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.data_avaliacao_edit.setCalendarPopup(True)
        
        self.peso_spinbox = QDoubleSpinBox()
        self.peso_spinbox.setSuffix(" kg")
        self.peso_spinbox.setRange(0.0, 500.0)
        self.peso_spinbox.setDecimals(2)
        self.peso_spinbox.setSingleStep(0.1)
        
        self.altura_spinbox = QDoubleSpinBox()
        self.altura_spinbox.setSuffix(" m")
        self.altura_spinbox.setRange(0.0, 3.0)
        self.altura_spinbox.setDecimals(2)
        self.altura_spinbox.setSingleStep(0.01)

        self.cintura_spinbox = QDoubleSpinBox()
        self.cintura_spinbox.setSuffix(" cm")
        self.cintura_spinbox.setRange(0.0, 300.0)
        self.cintura_spinbox.setDecimals(1)
        self.cintura_spinbox.setSingleStep(0.5)
        
        self.quadril_spinbox = QDoubleSpinBox()
        self.quadril_spinbox.setSuffix(" cm")
        self.quadril_spinbox.setRange(0.0, 300.0)
        self.quadril_spinbox.setDecimals(1)
        self.quadril_spinbox.setSingleStep(0.5)

        # TODO: Adicionar campos para outras medidas (dobras, etc.) se necessário

        self.anamnese_edit = QTextEdit()
        self.anamnese_edit.setPlaceholderText("Resumo da anamnese, queixas principais, hábitos...")
        self.anamnese_edit.setFixedHeight(100)
        
        self.exames_edit = QTextEdit()
        self.exames_edit.setPlaceholderText("Resultados relevantes de exames laboratoriais...")
        self.exames_edit.setFixedHeight(80)
        
        self.observacoes_edit = QTextEdit()
        self.observacoes_edit.setPlaceholderText("Observações gerais sobre a avaliação...")
        self.observacoes_edit.setFixedHeight(60)

        # Botões Salvar/Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        # --- Layout --- 
        layout = QVBoxLayout(self)
        layout.addWidget(self.paciente_label)
        
        form_layout = QFormLayout()
        form_layout.addRow("Data da Avaliação*: ", self.data_avaliacao_edit)
        form_layout.addRow("Peso: ", self.peso_spinbox)
        form_layout.addRow("Altura: ", self.altura_spinbox)
        form_layout.addRow("Circ. Cintura: ", self.cintura_spinbox)
        form_layout.addRow("Circ. Quadril: ", self.quadril_spinbox)
        form_layout.addRow("Anamnese (Resumo): ", self.anamnese_edit)
        form_layout.addRow("Exames (Resumo): ", self.exames_edit)
        form_layout.addRow("Observações: ", self.observacoes_edit)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        # --- Conexões --- 
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # --- Preencher dados se estiver editando --- 
        if self.is_editing and self.avaliacao:
            self._populate_form()

    def _populate_form(self):
        """Preenche o formulário com os dados da avaliação existente."""
        if not self.avaliacao: return
        
        try:
            data_aval = QDateTime.fromString(self.avaliacao.data_avaliacao or "", Qt.ISODate)
            # Tentar formatos alternativos se falhar
            if not data_aval.isValid():
                 data_aval = QDateTime.fromString(self.avaliacao.data_avaliacao or "", "yyyy-MM-dd HH:mm:ss") # Formato comum SQLite
            if data_aval.isValid():
                self.data_avaliacao_edit.setDateTime(data_aval)
        except Exception:
            pass # Mantém data/hora atual se houver erro
            
        self.peso_spinbox.setValue(self.avaliacao.peso or 0.0)
        self.altura_spinbox.setValue(self.avaliacao.altura or 0.0)
        self.cintura_spinbox.setValue(self.avaliacao.circunferencia_cintura or 0.0)
        self.quadril_spinbox.setValue(self.avaliacao.circunferencia_quadril or 0.0)
        self.anamnese_edit.setText(self.avaliacao.anamnese_resumo or "")
        self.exames_edit.setText(self.avaliacao.exames_resumo or "")
        self.observacoes_edit.setText(self.avaliacao.observacoes or "")

    def get_data(self) -> Dict[str, Any]:
        """Retorna os dados do formulário como um dicionário."""
        # Retorna None para campos numéricos se o valor for zero (ou muito próximo)
        # para evitar salvar zeros indesejados se o usuário não preencheu.
        # Uma alternativa é usar um valor especial ou checkbox para indicar "não informado".
        peso = self.peso_spinbox.value()
        altura = self.altura_spinbox.value()
        cintura = self.cintura_spinbox.value()
        quadril = self.quadril_spinbox.value()
        
        return {
            "paciente_id": self.paciente.id, # ID do paciente é fixo
            "data_avaliacao": self.data_avaliacao_edit.dateTime().toString(Qt.ISODate), # Formato ISO 8601
            "peso": peso if peso > 1e-6 else None, # Considera 0 como não informado
            "altura": altura if altura > 1e-6 else None,
            "circunferencia_cintura": cintura if cintura > 1e-6 else None,
            "circunferencia_quadril": quadril if quadril > 1e-6 else None,
            "anamnese_resumo": self.anamnese_edit.toPlainText().strip() or None,
            "exames_resumo": self.exames_edit.toPlainText().strip() or None,
            "observacoes": self.observacoes_edit.toPlainText().strip() or None,
        }

    @Slot()
    def accept(self):
        """Valida os dados antes de aceitar o diálogo."""
        dados = self.get_data()
        
        # Validação básica (Data é obrigatória)
        if not dados["data_avaliacao"] or not self.data_avaliacao_edit.dateTime().isValid():
             QMessageBox.warning(self, "Campo Obrigatório", "A data e hora da avaliação são obrigatórias e devem ser válidas.")
             self.data_avaliacao_edit.setFocus()
             return
        
        # Validação: Pelo menos um dado de avaliação deve ser preenchido?
        # if not any([dados["peso"], dados["altura"], dados["circunferencia_cintura"], 
        #             dados["circunferencia_quadril"], dados["anamnese_resumo"], 
        #             dados["exames_resumo"], dados["observacoes"]]):
        #     QMessageBox.warning(self, "Dados Incompletos", "Preencha pelo menos um campo da avaliação (peso, altura, etc.).")
        #     return

        # Se a validação passar, aceita o diálogo
        super().accept()

# Bloco para testar o diálogo isoladamente
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # Paciente fictício para teste
    paciente_teste = Paciente(id=99, nome_completo="Paciente Teste Dialog")

    # Teste de Nova Avaliação
    dialog_novo = AvaliacaoDialog(paciente=paciente_teste)
    if dialog_novo.exec() == QDialog.Accepted:
        print("Dados Nova Avaliação:", dialog_novo.get_data())
    else:
        print("Cadastro de nova avaliação cancelado.")

    # Teste de Edição de Avaliação (com dados fictícios)
    avaliacao_existente = Avaliacao(
        id=101,
        paciente_id=99,
        data_avaliacao="2024-01-15T10:30:00",
        peso=78.5,
        altura=1.80,
        observacoes="Avaliação anterior"
    )
    dialog_editar = AvaliacaoDialog(paciente=paciente_teste, avaliacao=avaliacao_existente)
    if dialog_editar.exec() == QDialog.Accepted:
        print("Dados Avaliação Editada:", dialog_editar.get_data())
    else:
        print("Edição de avaliação cancelada.")

    sys.exit() # Não iniciar loop de eventos aqui

