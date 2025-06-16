# src/ui/views/plano_alimentar_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QDateTimeEdit, QDoubleSpinBox, QTextEdit, QPushButton, 
    QDialogButtonBox, QMessageBox, QLabel, QGroupBox, QTableView, 
    QAbstractItemView, QHeaderView, QComboBox, QSpacerItem, QSizePolicy,
    QInputDialog # Importar QInputDialog para edição simples
)
from PySide6.QtCore import QDateTime, Slot, Qt, QModelIndex
from typing import Optional, Dict, Any, List
import logging # Adicionar logging

# Tenta importar de forma relativa primeiro
try:
    from ...core.models import PlanoAlimentar, Paciente, ItemPlanoAlimentar, Alimento
    from ...core.repositories import ItemPlanoAlimentarRepository, AlimentoRepository # Repos necessários
    from ..models.item_plano_table_model import ItemPlanoTableModel
    from .alimento_search_dialog import AlimentoSearchDialog
except ImportError:
    # Fallback
    from src.core.models import PlanoAlimentar, Paciente, ItemPlanoAlimentar, Alimento
    from src.core.repositories import ItemPlanoAlimentarRepository, AlimentoRepository
    from src.ui.models.item_plano_table_model import ItemPlanoTableModel
    from src.ui.views.alimento_search_dialog import AlimentoSearchDialog

class PlanoAlimentarDialog(QDialog):
    """Diálogo para criar ou editar um plano alimentar."""
    def __init__(self, paciente: Paciente, plano: Optional[PlanoAlimentar] = None, parent=None):
        super().__init__(parent)
        self.paciente = paciente
        self.plano = plano
        self.is_editing = plano is not None
        self.items_do_plano: list[ItemPlanoAlimentar] = []

        # Repositórios necessários
        try:
            self.item_repo = ItemPlanoAlimentarRepository()
            self.alimento_repo = AlimentoRepository()
        except Exception as e:
            logging.exception("Erro ao instanciar repositórios no PlanoAlimentarDialog")
            QMessageBox.critical(self, "Erro Crítico", f"Não foi possível inicializar os repositórios necessários:\n{e}")
            # Fechar o diálogo imediatamente se repositórios falharem
            # Usar QTimer para chamar self.reject() após o construtor terminar
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.reject)
            return # Evita continuar a inicialização

        self.setWindowTitle(f"Editar Plano Alimentar - {paciente.nome_completo}" if self.is_editing else f"Novo Plano Alimentar - {paciente.nome_completo}")
        self.setMinimumSize(800, 650)

        # --- Camada de Dados (Modelos UI) --- 
        self.item_table_model = ItemPlanoTableModel(self.items_do_plano)

        # --- Widgets --- 
        # Informações Gerais do Plano
        info_group = QGroupBox("Informações Gerais do Plano")
        info_layout = QFormLayout(info_group)
        self.nome_plano_edit = QLineEdit()
        self.objetivo_edit = QLineEdit()
        self.meta_kcal_spinbox = QDoubleSpinBox()
        self.meta_kcal_spinbox.setRange(0, 10000)
        self.meta_kcal_spinbox.setSuffix(" kcal")
        self.meta_kcal_spinbox.setDecimals(0)
        self.data_criacao_label = QLabel("-") # Será preenchido se editando
        info_layout.addRow("Nome do Plano<font color=\"red\">*</font>: ", self.nome_plano_edit)
        info_layout.addRow("Objetivo: ", self.objetivo_edit)
        info_layout.addRow("Meta Calórica (Opcional): ", self.meta_kcal_spinbox)
        if self.is_editing:
            info_layout.addRow("Data Criação: ", self.data_criacao_label)

        # Gerenciamento de Itens do Plano
        items_group = QGroupBox("Itens do Plano Alimentar")
        items_layout = QVBoxLayout(items_group)
        
        # Controles para adicionar item
        add_item_layout = QHBoxLayout()
        self.refeicao_combo = QComboBox()
        self.refeicao_combo.addItems(["Café da Manhã", "Lanche da Manhã", "Almoço", "Lanche da Tarde", "Jantar", "Ceia", "Pré-Treino", "Pós-Treino"])
        self.refeicao_combo.setEditable(True)
        self.add_alimento_button = QPushButton("Adicionar Alimento...")
        add_item_layout.addWidget(QLabel("Refeição:"))
        add_item_layout.addWidget(self.refeicao_combo)
        add_item_layout.addWidget(self.add_alimento_button)
        add_item_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        items_layout.addLayout(add_item_layout)

        # Tabela de Itens
        self.itens_table_view = QTableView()
        self.setup_table_view()
        self.itens_table_view.setModel(self.item_table_model)
        items_layout.addWidget(self.itens_table_view)

        # Botões para editar/remover item selecionado
        item_buttons_layout = QHBoxLayout()
        self.edit_item_button = QPushButton("Editar Item")
        self.remove_item_button = QPushButton("Remover Item")
        item_buttons_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        item_buttons_layout.addWidget(self.edit_item_button)
        item_buttons_layout.addWidget(self.remove_item_button)
        items_layout.addLayout(item_buttons_layout)

        # Resumo Nutricional
        summary_group = QGroupBox("Resumo Nutricional Estimado")
        summary_layout = QFormLayout(summary_group)
        self.total_kcal_label = QLabel("0.0 kcal")
        self.total_cho_label = QLabel("0.0 g")
        self.total_ptn_label = QLabel("0.0 g")
        self.total_lip_label = QLabel("0.0 g")
        # Adicionar labels para outros nutrientes se necessário (fibras, sódio)
        # self.total_fibras_label = QLabel("0.0 g")
        # self.total_sodio_label = QLabel("0 mg")
        summary_layout.addRow("Total Kcal:", self.total_kcal_label)
        summary_layout.addRow("Total CHO:", self.total_cho_label)
        summary_layout.addRow("Total PTN:", self.total_ptn_label)
        summary_layout.addRow("Total LIP:", self.total_lip_label)
        # summary_layout.addRow("Total Fibras:", self.total_fibras_label)
        # summary_layout.addRow("Total Sódio:", self.total_sodio_label)

        # Observações Gerais do Plano
        obs_group = QGroupBox("Observações Gerais")
        obs_layout = QVBoxLayout(obs_group)
        self.observacoes_plano_edit = QTextEdit()
        obs_layout.addWidget(self.observacoes_plano_edit)

        # Botões Salvar/Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText("Salvar Plano")
        self.button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")

        # --- Layout Principal --- 
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(info_group)
        main_layout.addWidget(items_group)
        main_layout.addWidget(summary_group)
        main_layout.addWidget(obs_group)
        main_layout.addWidget(self.button_box)

        # --- Conexões --- 
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.add_alimento_button.clicked.connect(self._handle_add_alimento)
        self.remove_item_button.clicked.connect(self._handle_remove_item)
        self.edit_item_button.clicked.connect(self._handle_edit_item)
        self.itens_table_view.selectionModel().selectionChanged.connect(self._update_item_button_states)
        self.itens_table_view.doubleClicked.connect(self._handle_edit_item) # Duplo clique edita
        
        # Conectar sinais do modelo para recalcular resumo dinamicamente
        # Estes sinais garantem que _update_summary é chamado sempre que:
        # - O modelo é resetado (setData)
        # - Linhas são removidas (removeRow)
        # - Dados em uma célula são alterados (updateRow via dataChanged)
        self.item_table_model.modelReset.connect(self._update_summary)
        self.item_table_model.rowsRemoved.connect(self._update_summary)
        self.item_table_model.dataChanged.connect(self._update_summary)

        # --- Inicialização --- 
        if self.is_editing and self.plano:
            self._populate_form()
            self._load_items() # Carrega itens e dispara _update_summary via modelReset
        else:
            # Se for novo plano, inicializa lista vazia e modelo
            self.items_do_plano = []
            self.item_table_model.setData(self.items_do_plano) # Dispara _update_summary via modelReset
            
        self._update_item_button_states()
        # _update_summary() já foi chamado pela inicialização/setData

    def setup_table_view(self):
        """Configura a aparência da tabela de itens do plano."""
        self.itens_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.itens_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.itens_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.itens_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Ajustar colunas específicas
        # Ordem: Refeição, Alimento, Quantidade, Unidade, Kcal, CHO, PTN, LIP
        header = self.itens_table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Refeição
        header.setSectionResizeMode(1, QHeaderView.Interactive)     # Alimento (pode ser longo)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Qtd
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Und
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Kcal
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # CHO
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # PTN
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # LIP
        self.itens_table_view.verticalHeader().setVisible(False)
        self.itens_table_view.setAlternatingRowColors(True)
        self.itens_table_view.setSortingEnabled(True)

    def _populate_form(self):
        """Preenche os campos gerais com dados do plano existente."""
        if not self.plano: return
        self.nome_plano_edit.setText(self.plano.nome_plano or "")
        self.objetivo_edit.setText(self.plano.objetivo or "")
        self.meta_kcal_spinbox.setValue(self.plano.meta_kcal or 0.0)
        self.observacoes_plano_edit.setText(self.plano.observacoes or "")
        try:
            # Tentar converter de ISO 8601 (formato do SQLite)
            dt_obj = QDateTime.fromString(self.plano.data_criacao or "", Qt.ISODate)
            dt_str = dt_obj.toString("dd/MM/yyyy HH:mm") if dt_obj.isValid() else self.plano.data_criacao
            self.data_criacao_label.setText(dt_str or "-")
        except Exception as e:
             logging.warning(f"Erro ao formatar data de criação {self.plano.data_criacao}: {e}")
             self.data_criacao_label.setText(self.plano.data_criacao or "-")

    def _load_items(self):
        """Carrega os itens do plano alimentar do banco de dados (se editando)."""
        if self.is_editing and self.plano and self.plano.id is not None:
            logging.info(f"Carregando itens para o plano ID: {self.plano.id}")
            try:
                self.items_do_plano = self.item_repo.get_by_plano_id(self.plano.id)
                logging.info(f"{len(self.items_do_plano)} itens encontrados no banco.")
                # Precisamos dos dados do alimento para calcular/exibir
                for item in self.items_do_plano:
                    alimento = self.alimento_repo.get_by_id(item.alimento_id)
                    if alimento:
                        item.nome_alimento = alimento.nome # Garante que nome está atualizado
                        # Calcular nutrientes ao carregar
                        self._calculate_item_nutrients(item, alimento)
                    else:
                        logging.warning(f"Alimento ID {item.alimento_id} não encontrado para o item {item.id}. O item será exibido com aviso.")
                        item.nome_alimento = f"<Alimento ID {item.alimento_id} não encontrado>"
                        # Zerar nutrientes calculados se alimento não existe?
                        item.kcal_calculado = 0
                        item.cho_calculado = 0
                        item.ptn_calculado = 0
                        item.lip_calculado = 0
                
                self.item_table_model.setData(self.items_do_plano)
                logging.info("Modelo da tabela de itens atualizado.")
            except Exception as e:
                logging.exception("Erro crítico ao carregar itens do plano:")
                QMessageBox.critical(self, "Erro", f"Não foi possível carregar os itens do plano:\n{e}")
        else:
            logging.info("Nenhum item para carregar (novo plano ou ID inválido).")
            self.items_do_plano = []
            self.item_table_model.setData(self.items_do_plano)

    @Slot()
    def _update_item_button_states(self):
        """Habilita/desabilita botões de editar/remover item."""
        has_selection = bool(self.itens_table_view.selectionModel().selectedRows())
        self.edit_item_button.setEnabled(has_selection)
        self.remove_item_button.setEnabled(has_selection)

    @Slot()
    def _handle_add_alimento(self):
        """Abre diálogo para buscar e adicionar um alimento à refeição selecionada."""
        refeicao_selecionada = self.refeicao_combo.currentText().strip()
        if not refeicao_selecionada:
            QMessageBox.warning(self, "Refeição Inválida", "Selecione ou digite um nome para a refeição.")
            self.refeicao_combo.setFocus()
            return

        logging.info("Abrindo diálogo de busca de alimentos.")
        search_dialog = AlimentoSearchDialog(parent=self)
        if search_dialog.exec() == QDialog.Accepted:
            selection = search_dialog.get_selection()
            if selection:
                alimento_selecionado, quantidade, unidade = selection
                logging.info(f"Alimento selecionado: {alimento_selecionado.nome}, Qtd: {quantidade}, Und: {unidade}")
                
                # Criar novo item (sem ID ainda)
                novo_item = ItemPlanoAlimentar(
                    plano_alimentar_id=self.plano.id if self.is_editing and self.plano else None,
                    refeicao=refeicao_selecionada,
                    alimento_id=alimento_selecionado.id,
                    nome_alimento=alimento_selecionado.nome,
                    quantidade=quantidade,
                    unidade_medida=unidade,
                    kcal_calculado=0, cho_calculado=0, ptn_calculado=0, lip_calculado=0
                )
                
                # Calcular nutrientes para o novo item
                self._calculate_item_nutrients(novo_item, alimento_selecionado)
                
                # Adicionar à lista e atualizar tabela
                # Usar insertRow do modelo para notificação correta
                self.item_table_model.insertRow(novo_item)
                logging.info("Novo item adicionado ao modelo da tabela.")
                # _update_summary será chamado pelo modelReset/rowsInserted
            else:
                logging.warning("Seleção do diálogo de busca retornou None.")
        else:
            logging.info("Busca de alimento cancelada.")

    def _calculate_item_nutrients(self, item: ItemPlanoAlimentar, alimento: Alimento):
        """Calcula os nutrientes de um item do plano baseado no alimento e quantidade.
           ATENÇÃO: A conversão de unidades NÃO está implementada.
        """
        # Validação básica
        if not alimento or item.quantidade is None:
            item.kcal_calculado = 0
            item.cho_calculado = 0
            item.ptn_calculado = 0
            item.lip_calculado = 0
            return
            
        # Simplificação: Assume que a unidade do item é a unidade padrão do alimento
        alimento_unidade_padrao = (alimento.unidade_padrao or "").strip().lower()
        item_unidade = (item.unidade_medida or "").strip().lower()
        
        fator = item.quantidade
        
        # Lógica de conversão (MUITO BÁSICA - EXEMPLO)
        # Idealmente, usar uma biblioteca ou tabela de conversão robusta
        if alimento_unidade_padrao == "g" and item_unidade == "kg":
            fator *= 1000
            logging.debug(f"Convertendo kg para g para {alimento.nome}")
        elif alimento_unidade_padrao == "ml" and item_unidade == "l":
            fator *= 1000
            logging.debug(f"Convertendo l para ml para {alimento.nome}")
        elif alimento_unidade_padrao != item_unidade and alimento_unidade_padrao and item_unidade:
            # Se unidades diferentes e não for conversão simples conhecida, ZERAR e AVISAR?
            # Ou tentar calcular mesmo assim e avisar?
            logging.warning(f"Unidade do item ({item.unidade_medida}) diferente da padrão ({alimento.unidade_padrao}) para {alimento.nome}. Cálculo baseado na unidade padrão.")
            # Poderia tentar buscar um fator de conversão em `alimento.observacoes`? Ex: "1 fatia = 30g"
            # Por ora, calcula usando a unidade padrão do alimento
            pass 
            
        # Calcular nutrientes
        item.kcal_calculado = (alimento.kcal_por_unidade or 0) * fator
        item.cho_calculado = (alimento.cho_por_unidade or 0) * fator
        item.ptn_calculado = (alimento.ptn_por_unidade or 0) * fator
        item.lip_calculado = (alimento.lip_por_unidade or 0) * fator
        # Adicionar outros nutrientes (fibras, sódio) se existirem no modelo Alimento
        # item.fibras_calculado = (alimento.fibras_por_unidade or 0) * fator
        # item.sodio_calculado = (alimento.sodio_mg_por_unidade or 0) * fator
        logging.debug(f"Nutrientes calculados para {item.nome_alimento}: Kcal={item.kcal_calculado:.1f}")

    def _get_selected_item_index(self) -> Optional[QModelIndex]:
        """Retorna o QModelIndex do item selecionado na tabela."""
        selected_rows = self.itens_table_view.selectionModel().selectedRows()
        if not selected_rows: return None
        # Mapear view -> model (considerando sort/filter se houver)
        # TODO: Implementar mapeamento se usar QSortFilterProxyModel
        model_index = self.item_table_model.index(selected_rows[0].row(), 0)
        return model_index

    def _get_selected_item(self) -> Optional[ItemPlanoAlimentar]:
         """Retorna o ItemPlanoAlimentar selecionado na tabela."""
         model_index = self._get_selected_item_index()
         if model_index and model_index.isValid():
             return self.item_table_model.getItemAtRow(model_index.row())
         return None

    @Slot()
    def _handle_edit_item(self):
        """Edita a quantidade e unidade do item selecionado."""
        selected_index = self._get_selected_item_index()
        item_selecionado = self._get_selected_item()
        
        if not item_selecionado or not selected_index:
            QMessageBox.warning(self, "Atenção", "Selecione um item na tabela para editar.")
            return

        logging.info(f"Editando item: {item_selecionado.nome_alimento}")
        # Usar QInputDialog para simplicidade
        nova_quantidade, ok1 = QInputDialog.getDouble(self, "Editar Quantidade", 
                                                     f"Nova quantidade para {item_selecionado.nome_alimento}:", 
                                                     item_selecionado.quantidade, 0.01, 9999.99, 2)
        
        if ok1:
            # Sugerir unidades comuns + a atual
            unidades_sugeridas = ["g", "ml", "unidade", "fatia", "colher de sopa", "colher de chá", "xícara", "copo", "pedaço"]
            if item_selecionado.unidade_medida not in unidades_sugeridas:
                unidades_sugeridas.insert(0, item_selecionado.unidade_medida)
                
            nova_unidade, ok2 = QInputDialog.getItem(self, "Editar Unidade", 
                                                   f"Nova unidade para {item_selecionado.nome_alimento}:", 
                                                   unidades_sugeridas, 
                                                   unidades_sugeridas.index(item_selecionado.unidade_medida) if item_selecionado.unidade_medida in unidades_sugeridas else 0, 
                                                   editable=True) # Permitir digitar unidade nova
            
            if ok2 and nova_unidade.strip():
                logging.debug(f"Novos valores - Qtd: {nova_quantidade}, Und: {nova_unidade}")
                item_selecionado.quantidade = nova_quantidade
                item_selecionado.unidade_medida = nova_unidade.strip()
                
                # Recalcular nutrientes
                alimento = self.alimento_repo.get_by_id(item_selecionado.alimento_id)
                if alimento:
                    self._calculate_item_nutrients(item_selecionado, alimento)
                    # Notificar a view que os dados mudaram para esta linha
                    # Usar updateRow do modelo para simplificar
                    self.item_table_model.updateRow(selected_index.row(), item_selecionado)
                    logging.info(f"Item {item_selecionado.nome_alimento} atualizado e recalculado.")
                    # _update_summary será chamado pelo dataChanged emitido por updateRow
                else:
                     logging.error(f"Alimento ID {item_selecionado.alimento_id} não encontrado ao tentar editar item.")
                     QMessageBox.warning(self, "Erro", f"Não foi possível encontrar o alimento ID {item_selecionado.alimento_id} para recalcular.")
            else:
                logging.info("Edição de unidade cancelada ou vazia.")
        else:
            logging.info("Edição de quantidade cancelada.")

    @Slot()
    def _handle_remove_item(self):
        """Remove o item selecionado da lista."""
        selected_index = self._get_selected_item_index()
        item_selecionado = self._get_selected_item()

        if not item_selecionado or not selected_index:
            QMessageBox.warning(self, "Atenção", "Selecione um item na tabela para remover.")
            return
        
        logging.info(f"Tentando remover item: {item_selecionado.nome_alimento}")
        confirm = QMessageBox.question(self, "Confirmar Remoção", 
                                       f"Remover \"{item_selecionado.nome_alimento}\" da refeição \"{item_selecionado.refeicao}\"?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            row_to_remove = selected_index.row()
            # Usar removeRow do modelo para notificação correta
            if self.item_table_model.removeRow(row_to_remove):
                logging.info("Item removido com sucesso do modelo.")
                # A lista interna self.items_do_plano precisa ser sincronizada?
                # O ideal é que o modelo seja a fonte da verdade.
                # Se removeRow removeu do _data do modelo, está ok.
                # Vamos garantir que removeRow no modelo remova de self._data
            else:
                 logging.error("Falha ao remover linha do modelo.")
                 QMessageBox.warning(self, "Erro", "Não foi possível remover o item selecionado (erro no modelo).")
            # _update_summary será chamado pelo rowsRemoved emitido por removeRow

    @Slot()
    def _update_summary(self):
        """Calcula e exibe o resumo nutricional do plano baseado nos itens atuais do MODELO."""
        logging.debug("Atualizando resumo nutricional...")
        # Usar os dados diretamente do modelo para garantir consistência
        items_no_modelo = self.item_table_model._data 
        
        total_kcal = sum(item.kcal_calculado or 0 for item in items_no_modelo)
        total_cho = sum(item.cho_calculado or 0 for item in items_no_modelo)
        total_ptn = sum(item.ptn_calculado or 0 for item in items_no_modelo)
        total_lip = sum(item.lip_calculado or 0 for item in items_no_modelo)
        # Adicionar outros totais se necessário
        # total_fibras = sum(item.fibras_calculado or 0 for item in items_no_modelo)
        # total_sodio = sum(item.sodio_calculado or 0 for item in items_no_modelo)
            
        self.total_kcal_label.setText(f"<b>{total_kcal:.1f} kcal</b>")
        self.total_cho_label.setText(f"<b>{total_cho:.1f} g</b>")
        self.total_ptn_label.setText(f"<b>{total_ptn:.1f} g</b>")
        self.total_lip_label.setText(f"<b>{total_lip:.1f} g</b>")
        # self.total_fibras_label.setText(f"<b>{total_fibras:.1f} g</b>")
        # self.total_sodio_label.setText(f"<b>{total_sodio:.0f} mg</b>")
        logging.debug(f"Resumo atualizado: Kcal={total_kcal:.1f}")

    def get_plano_data(self) -> Dict[str, Any]:
        """Retorna os dados gerais do plano do formulário."""
        meta_kcal = self.meta_kcal_spinbox.value()
        return {
            "paciente_id": self.paciente.id,
            "nome_plano": self.nome_plano_edit.text().strip(),
            "objetivo": self.objetivo_edit.text().strip() or None,
            "meta_kcal": meta_kcal if meta_kcal > 1e-6 else None,
            "observacoes": self.observacoes_plano_edit.toPlainText().strip() or None,
        }

    def get_itens_data(self) -> List[ItemPlanoAlimentar]:
        """Retorna a lista de itens do plano (do modelo)."""
        # Retorna a lista de dados que está no modelo
        return self.item_table_model._data

    @Slot()
    def accept(self):
        """Valida os dados antes de aceitar o diálogo."""
        plano_data = self.get_plano_data()
        itens_data = self.get_itens_data()
        
        if not plano_data["nome_plano"]:
            QMessageBox.warning(self, "Campo Obrigatório", "O <b>Nome do Plano</b> alimentar é obrigatório.")
            self.nome_plano_edit.setFocus()
            return
            
        if not itens_data:
            confirm = QMessageBox.question(self, "Plano Vazio", 
                                           "O plano alimentar não contém nenhum item. Deseja salvar mesmo assim?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.No:
                return

        logging.info("Validação do plano alimentar passou. Aceitando diálogo.")
        super().accept()

# Bloco para testar o diálogo isoladamente
# (Omitido para brevidade)
# if __name__ == "__main__": ...

