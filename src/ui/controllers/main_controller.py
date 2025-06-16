# src/ui/controllers/main_controller.py

import sys
import logging
import sqlite3 # Import for specific error handling
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtCore import Slot, QItemSelectionModel, QModelIndex, QDateTime, Qt

# Tenta importar de forma relativa primeiro
try:
    from ..views.main_window import MainWindow
    from ..views.cadastro_paciente_dialog import CadastroPacienteDialog
    from ..views.avaliacao_dialog import AvaliacaoDialog
    from ..views.alimento_dialog import AlimentoDialog
    from ..views.plano_alimentar_dialog import PlanoAlimentarDialog
    from ..views.view_avaliacoes_dialog import ViewAvaliacoesDialog # Importar diálogo de visualização
    from ..views.view_planos_dialog import ViewPlanosDialog # Importar diálogo de visualização
    from ..models.paciente_table_model import PacienteTableModel
    from ...core.repositories import PacienteRepository, AvaliacaoRepository, AlimentoRepository, PlanoAlimentarRepository, ItemPlanoAlimentarRepository
    from ...core.models import Paciente, Avaliacao, Alimento, PlanoAlimentar, ItemPlanoAlimentar
except ImportError:
    # Fallback
    from src.ui.views.main_window import MainWindow
    from src.ui.views.cadastro_paciente_dialog import CadastroPacienteDialog
    from src.ui.views.avaliacao_dialog import AvaliacaoDialog
    from src.ui.views.alimento_dialog import AlimentoDialog
    from src.ui.views.plano_alimentar_dialog import PlanoAlimentarDialog
    from src.ui.views.view_avaliacoes_dialog import ViewAvaliacoesDialog
    from src.ui.views.view_planos_dialog import ViewPlanosDialog
    from src.ui.models.paciente_table_model import PacienteTableModel
    from src.core.repositories import PacienteRepository, AvaliacaoRepository, AlimentoRepository, PlanoAlimentarRepository, ItemPlanoAlimentarRepository
    from src.core.models import Paciente, Avaliacao, Alimento, PlanoAlimentar, ItemPlanoAlimentar

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

class MainController:
    """Controlador principal que gerencia a MainWindow e a interação com o backend."""
    def __init__(self):
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)
            # self.app.setStyle("Fusion")

        # Inicializa camadas de dados e UI
        try:
            self.paciente_repo = PacienteRepository()
            self.avaliacao_repo = AvaliacaoRepository()
            self.alimento_repo = AlimentoRepository()
            self.plano_repo = PlanoAlimentarRepository()
            self.item_plano_repo = ItemPlanoAlimentarRepository()
        except Exception as e:
            logging.critical(f"Erro ao inicializar repositórios: {e}", exc_info=True)
            QMessageBox.critical(None, "Erro Crítico", f"Falha ao conectar ao banco de dados ou inicializar repositórios:\n{e}\n\nA aplicação será encerrada.")
            sys.exit(1)
            
        self.paciente_table_model = PacienteTableModel()
        self.view = MainWindow()

        # Configura a view
        self.view.pacientes_table_view.setModel(self.paciente_table_model)
        
        # Carrega dados iniciais
        self._load_pacientes()

        # Conecta sinais da View aos slots do Controller
        self._connect_signals()

    def show_view(self):
        """Exibe a janela principal."""
        self.view.show()
        sys.exit(self.app.exec())

    def _get_selected_paciente(self) -> Optional[Paciente]:
        """Retorna o objeto Paciente selecionado na tabela."""
        selected_rows = self.view.pacientes_table_view.selectionModel().selectedRows()
        if not selected_rows:
            return None
        model_index = self.view.pacientes_table_view.model().index(selected_rows[0].row(), 0)
        return self.paciente_table_model.getPacienteAtRow(model_index.row())

    def _connect_signals(self):
        """Conecta os sinais dos widgets da MainWindow aos métodos (slots) deste controller."""
        self.view.quit_action.triggered.connect(self._handle_quit)
        self.view.new_paciente_action.triggered.connect(self._handle_new_paciente)
        self.view.edit_paciente_action.triggered.connect(self._handle_edit_paciente)
        self.view.delete_paciente_action.triggered.connect(self._handle_delete_paciente)
        self.view.new_avaliacao_action.triggered.connect(self._handle_new_avaliacao)
        self.view.view_avaliacoes_action.triggered.connect(self._handle_view_avaliacoes)
        self.view.new_plano_action.triggered.connect(self._handle_new_plano)
        self.view.view_planos_action.triggered.connect(self._handle_view_planos)
        self.view.manage_alimentos_action.triggered.connect(self._handle_manage_alimentos)
        self.view.about_action.triggered.connect(self._handle_about)
        selection_model = self.view.pacientes_table_view.selectionModel()
        if selection_model:
             selection_model.selectionChanged.connect(self._on_selection_changed)
        else:
            logging.warning("SelectionModel não encontrado para a tabela de pacientes.")
        self.view.pacientes_table_view.doubleClicked.connect(self._handle_edit_paciente_on_double_click)

    # --- Slots (Manipuladores de Sinais) ---
    @Slot()
    def _load_pacientes(self):
        """Carrega/recarrega a lista de pacientes do repositório e atualiza a tabela."""
        self.view.set_status_message("Carregando pacientes...")
        try:
            pacientes = self.paciente_repo.get_all()
            self.paciente_table_model.setData(pacientes)
            self.view.pacientes_table_view.clearSelection()
            self.view.update_paciente_context_actions(False)
            self.view.set_status_message(f"{len(pacientes)} paciente(s) carregado(s).", 3000)
            logging.info(f"{len(pacientes)} pacientes carregados do banco de dados.")
        except Exception as e:
            logging.exception("Erro crítico ao carregar pacientes:")
            self.view.set_status_message("Erro ao carregar pacientes!", 5000)
            QMessageBox.critical(self.view, "Erro Crítico", f"Não foi possível carregar a lista de pacientes:\n{e}")

    @Slot("QItemSelection", "QItemSelection")
    def _on_selection_changed(self, selected, deselected):
        """Atualiza o estado das ações com base na seleção da tabela."""
        is_selected = bool(self.view.pacientes_table_view.selectionModel().selectedRows())
        self.view.update_paciente_context_actions(is_selected)

    def _handle_db_integrity_error(self, error: sqlite3.IntegrityError, context: str):
        """Centraliza o tratamento de erros de integridade comuns."""
        error_str = str(error).lower()
        if "unique constraint failed" in error_str:
            if "pacientes.email" in error_str:
                QMessageBox.warning(self.view, f"Erro ao {context}", f"Não foi possível {context.lower()} o paciente: o email informado já está cadastrado.")
            elif "alimentos.nome" in error_str:
                 QMessageBox.warning(self.view, f"Erro ao {context}", f"Não foi possível {context.lower()} o alimento: já existe um alimento com este nome.")
            # Adicionar outras constraints aqui (ex: nome do plano por paciente?)
            else:
                QMessageBox.warning(self.view, f"Erro ao {context}", f"Erro de chave única ao salvar: {error}")
        elif "foreign key constraint failed" in error_str:
             QMessageBox.warning(self.view, f"Erro ao {context}", f"Erro de chave estrangeira: {error}. Verifique se os dados relacionados existem.")
        else:
            QMessageBox.warning(self.view, f"Erro ao {context}", f"Erro de integridade do banco de dados ao salvar: {error}")

    @Slot()
    def _handle_new_paciente(self):
        """Abre o diálogo para adicionar um novo paciente."""
        logging.info("Ação: Novo Paciente")
        dialog = CadastroPacienteDialog(parent=self.view)
        if dialog.exec() == QDialog.Accepted:
            novo_paciente_data = dialog.get_data()
            paciente = Paciente(**novo_paciente_data)
            try:
                paciente_id = self.paciente_repo.add(paciente)
                if paciente_id:
                    logging.info(f"Novo paciente adicionado com ID: {paciente_id}")
                    self._load_pacientes()
                    self.view.set_status_message("Novo paciente adicionado com sucesso!", 3000)
                else:
                    QMessageBox.warning(self.view, "Erro ao Adicionar", "Não foi possível adicionar o paciente (repositório retornou None). Verifique os logs.")
            except sqlite3.IntegrityError as e:
                logging.warning(f"Erro de integridade ao adicionar paciente: {e}")
                self._handle_db_integrity_error(e, "Adicionar Paciente")
            except Exception as e:
                logging.exception("Erro inesperado ao adicionar paciente:")
                QMessageBox.critical(self.view, "Erro Crítico", f"Ocorreu um erro inesperado ao adicionar o paciente:\n{e}")
        else:
            logging.info("Cadastro de novo paciente cancelado.")
            self.view.set_status_message("Cadastro cancelado.", 2000)

    @Slot()
    def _handle_edit_paciente(self):
        """Abre o diálogo para editar o paciente selecionado."""
        paciente_selecionado = self._get_selected_paciente()
        if not paciente_selecionado:
            QMessageBox.warning(self.view, "Atenção", "Selecione um paciente na tabela para editar.")
            return
        
        logging.info(f"Ação: Editar Paciente ID: {paciente_selecionado.id}")
        dialog = CadastroPacienteDialog(paciente=paciente_selecionado, parent=self.view)
        if dialog.exec() == QDialog.Accepted:
            dados_atualizados = dialog.get_data()
            paciente_atualizado = Paciente(id=paciente_selecionado.id, **dados_atualizados)
            try:
                if self.paciente_repo.update(paciente_atualizado):
                    logging.info(f"Paciente ID {paciente_atualizado.id} atualizado com sucesso.")
                    self._load_pacientes()
                    self.view.set_status_message("Paciente atualizado com sucesso!", 3000)
                else:
                    QMessageBox.warning(self.view, "Erro ao Atualizar", "Não foi possível atualizar o paciente (paciente não encontrado ou erro no repositório). Verifique os logs.")
            except sqlite3.IntegrityError as e:
                logging.warning(f"Erro de integridade ao atualizar paciente ID {paciente_atualizado.id}: {e}")
                self._handle_db_integrity_error(e, "Atualizar Paciente")
            except Exception as e:
                logging.exception(f"Erro inesperado ao atualizar paciente ID {paciente_atualizado.id}: ")
                QMessageBox.critical(self.view, "Erro Crítico", f"Ocorreu um erro inesperado ao atualizar o paciente:\n{e}")
        else:
            logging.info(f"Edição do paciente ID {paciente_selecionado.id} cancelada.")
            self.view.set_status_message("Edição cancelada.", 2000)

    @Slot(QModelIndex)
    def _handle_edit_paciente_on_double_click(self, index: QModelIndex):
        """Chamado quando uma linha da tabela recebe duplo clique."""
        if index.isValid():
            self._handle_edit_paciente()

    @Slot()
    def _handle_delete_paciente(self):
        """Exclui o paciente selecionado após confirmação."""
        paciente_selecionado = self._get_selected_paciente()
        if not paciente_selecionado or paciente_selecionado.id is None:
            QMessageBox.warning(self.view, "Atenção", "Selecione um paciente na tabela para excluir.")
            return

        logging.info(f"Ação: Excluir Paciente ID: {paciente_selecionado.id}")
        confirm = QMessageBox.question(self.view, "Confirmar Exclusão", 
                                       f"Tem certeza que deseja excluir o paciente \"{paciente_selecionado.nome_completo}\"?\n\n<font color=\"red\"><b>ATENÇÃO:</b> Todas as avaliações e planos alimentares associados a este paciente serão permanentemente excluídos.</font>",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            try:
                if self.paciente_repo.delete(paciente_selecionado.id):
                    logging.info(f"Paciente ID {paciente_selecionado.id} excluído com sucesso.")
                    self._load_pacientes()
                    self.view.set_status_message("Paciente e dados relacionados excluídos com sucesso!", 3000)
                else:
                    logging.error(f"Falha na operação de exclusão do paciente ID {paciente_selecionado.id} no repositório (retornou False).")
                    QMessageBox.warning(self.view, "Erro", "Não foi possível excluir o paciente (paciente não encontrado?). Verifique os logs.")
            except Exception as e:
                 logging.exception(f"Erro inesperado ao excluir paciente ID {paciente_selecionado.id}:")
                 QMessageBox.critical(self.view, "Erro Crítico", f"Ocorreu um erro inesperado ao excluir o paciente:\n{e}")

    @Slot()
    def _handle_new_avaliacao(self):
        """Abre o diálogo para adicionar uma nova avaliação para o paciente selecionado."""
        paciente_selecionado = self._get_selected_paciente()
        if not paciente_selecionado:
            QMessageBox.warning(self.view, "Atenção", "Selecione um paciente na tabela para adicionar uma avaliação.")
            return
            
        logging.info(f"Ação: Nova Avaliação para Paciente ID: {paciente_selecionado.id}")
        dialog = AvaliacaoDialog(paciente=paciente_selecionado, parent=self.view)
        if dialog.exec() == QDialog.Accepted:
            nova_avaliacao_data = dialog.get_data()
            avaliacao = Avaliacao(**nova_avaliacao_data)
            try:
                avaliacao_id = self.avaliacao_repo.add(avaliacao)
                if avaliacao_id:
                    logging.info(f"Nova avaliação adicionada com ID: {avaliacao_id} para Paciente ID: {paciente_selecionado.id}")
                    self.view.set_status_message("Nova avaliação adicionada com sucesso!", 3000)
                else:
                    QMessageBox.warning(self.view, "Erro ao Adicionar", "Não foi possível adicionar a avaliação (repositório retornou None). Verifique os logs.")
            except Exception as e:
                logging.exception("Erro inesperado ao adicionar avaliação:")
                QMessageBox.critical(self.view, "Erro Crítico", f"Ocorreu um erro inesperado ao adicionar a avaliação:\n{e}")
        else:
            logging.info("Cadastro de nova avaliação cancelado.")
            self.view.set_status_message("Cadastro de avaliação cancelado.", 2000)

    @Slot()
    def _handle_view_avaliacoes(self):
        """Exibe o histórico de avaliações do paciente selecionado."""
        paciente_selecionado = self._get_selected_paciente()
        if not paciente_selecionado:
            QMessageBox.warning(self.view, "Atenção", "Selecione um paciente na tabela para visualizar as avaliações.")
            return
            
        logging.info(f"Ação: Ver Avaliações para Paciente ID: {paciente_selecionado.id}")
        try:
            dialog = ViewAvaliacoesDialog(paciente=paciente_selecionado, parent=self.view)
            dialog.exec()
            # Ações futuras (editar/excluir) podem ser tratadas aqui com base no resultado do diálogo
        except Exception as e:
            logging.exception(f"Erro ao abrir diálogo de visualização de avaliações para Paciente ID {paciente_selecionado.id}:")
            QMessageBox.critical(self.view, "Erro", f"Não foi possível abrir o histórico de avaliações:\n{e}")

    # --- Slots para Planos Alimentares --- 
    @Slot()
    def _handle_new_plano(self):
        """Abre o diálogo para criar um novo plano alimentar para o paciente selecionado."""
        paciente_selecionado = self._get_selected_paciente()
        if not paciente_selecionado:
            QMessageBox.warning(self.view, "Atenção", "Selecione um paciente na tabela para criar um plano.")
            return
            
        logging.info(f"Ação: Novo Plano para Paciente ID: {paciente_selecionado.id}")
        dialog = PlanoAlimentarDialog(paciente=paciente_selecionado, parent=self.view)
        
        if dialog.exec() == QDialog.Accepted:
            plano_data = dialog.get_plano_data()
            itens_data = dialog.get_itens_data()
            
            novo_plano = PlanoAlimentar(**plano_data)
            plano_id = None
            try:
                # Usar transação conceitual (idealmente seria uma transação real no DB)
                plano_id = self.plano_repo.add(novo_plano)
                if not plano_id:
                    raise Exception("Falha ao obter ID do novo plano alimentar.")
                
                logging.info(f"Plano ID {plano_id} criado. Adicionando {len(itens_data)} itens.")
                for item in itens_data:
                    item.plano_alimentar_id = plano_id
                
                if itens_data:
                    if not self.item_plano_repo.add_batch(itens_data):
                        # Tentar reverter a criação do plano se itens falharem
                        logging.error(f"Falha ao salvar itens para o novo plano ID {plano_id}. Tentando reverter.")
                        try:
                            self.plano_repo.delete(plano_id)
                            logging.info(f"Plano ID {plano_id} revertido com sucesso.")
                        except Exception as del_e:
                            logging.error(f"Falha CRÍTICA ao reverter plano ID {plano_id} após erro nos itens: {del_e}")
                        raise Exception("Falha ao salvar itens do plano alimentar em lote.")
                
                logging.info(f"Plano alimentar ID {plano_id} e seus itens salvos com sucesso.")
                self.view.set_status_message("Novo plano alimentar salvo com sucesso!", 3000)
                
            except Exception as e:
                logging.exception(f"Erro ao salvar novo plano alimentar para paciente ID {paciente_selecionado.id}:")
                QMessageBox.critical(self.view, "Erro ao Salvar Plano", f"Ocorreu um erro ao salvar o plano alimentar:\n{e}")
        else:
            logging.info("Criação de novo plano cancelada.")
            self.view.set_status_message("Criação de plano cancelada.", 2000)

    def _handle_edit_plano(self, plano_para_editar: PlanoAlimentar):
        """Abre o diálogo para editar um plano alimentar existente."""
        if not plano_para_editar or not plano_para_editar.id:
            logging.error("Tentativa de editar plano inválido.")
            return
            
        paciente = self.paciente_repo.get_by_id(plano_para_editar.paciente_id)
        if not paciente:
             QMessageBox.critical(self.view, "Erro", f"Paciente ID {plano_para_editar.paciente_id} não encontrado para o plano.")
             return

        logging.info(f"Ação: Editar Plano ID: {plano_para_editar.id} para Paciente ID: {paciente.id}")
        dialog = PlanoAlimentarDialog(paciente=paciente, plano=plano_para_editar, parent=self.view)
        
        if dialog.exec() == QDialog.Accepted:
            plano_data = dialog.get_plano_data()
            itens_data = dialog.get_itens_data()
            
            plano_atualizado = PlanoAlimentar(id=plano_para_editar.id, **plano_data)
            
            try:
                # Transação conceitual
                if not self.plano_repo.update(plano_atualizado):
                    raise Exception("Falha ao atualizar dados do plano alimentar (plano não encontrado?).")
                
                logging.info(f"Plano ID {plano_atualizado.id} atualizado. Atualizando itens...")
                self.item_plano_repo.delete_by_plano_id(plano_atualizado.id)
                
                for item in itens_data:
                    item.plano_alimentar_id = plano_atualizado.id
                
                if itens_data:
                    if not self.item_plano_repo.add_batch(itens_data):
                        # ERRO: Reverter a atualização do plano seria complexo aqui.
                        # Idealmente, a transação deveria cobrir tudo.
                        logging.error(f"Falha ao salvar itens atualizados para o plano ID {plano_atualizado.id}. O plano foi atualizado, mas os itens podem estar inconsistentes.")
                        raise Exception("Falha ao salvar itens atualizados do plano alimentar em lote.")
                
                logging.info(f"Plano alimentar ID {plano_atualizado.id} e seus itens atualizados com sucesso.")
                self.view.set_status_message("Plano alimentar atualizado com sucesso!", 3000)
                
            except Exception as e:
                logging.exception(f"Erro ao atualizar plano alimentar ID {plano_para_editar.id}:")
                QMessageBox.critical(self.view, "Erro ao Atualizar Plano", f"Ocorreu um erro ao atualizar o plano alimentar:\n{e}")
        else:
            logging.info(f"Edição do plano ID {plano_para_editar.id} cancelada.")
            self.view.set_status_message("Edição de plano cancelada.", 2000)

    @Slot()
    def _handle_view_planos(self):
        """Exibe os planos alimentares do paciente selecionado e permite edição/exclusão."""
        paciente_selecionado = self._get_selected_paciente()
        if not paciente_selecionado:
            QMessageBox.warning(self.view, "Atenção", "Selecione um paciente na tabela para visualizar os planos.")
            return
            
        logging.info(f"Ação: Ver Planos para Paciente ID: {paciente_selecionado.id}")
        try:
            dialog = ViewPlanosDialog(paciente=paciente_selecionado, parent=self.view)
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                plano_para_editar = dialog.get_selected_plano_for_edit()
                if plano_para_editar:
                    # Chamar a função de edição
                    self._handle_edit_plano(plano_para_editar)
                else:
                    # Isso não deveria acontecer se o diálogo foi aceito para edição
                    logging.warning("Diálogo ViewPlanos aceito, mas nenhum plano selecionado para edição.")
            # Se foi rejeitado (fechado) ou a exclusão foi tratada dentro do diálogo, não faz nada aqui.
            
        except Exception as e:
            logging.exception(f"Erro ao abrir/processar diálogo de visualização de planos para Paciente ID {paciente_selecionado.id}:")
            QMessageBox.critical(self.view, "Erro", f"Não foi possível abrir/processar o histórico de planos alimentares:\n{e}")

    # --- Slots para Ferramentas --- 
    @Slot()
    def _handle_manage_alimentos(self):
        """Abre o diálogo de gerenciamento de alimentos."""
        logging.info("Ação: Gerenciar Alimentos")
        try:
            dialog = AlimentoDialog(parent=self.view)
            dialog.exec()
            # Atualizações feitas no diálogo de alimentos não refletem imediatamente
            # em diálogos de plano abertos. Considerar recarregar dados se necessário.
        except Exception as e:
            logging.exception("Erro ao abrir gerenciador de alimentos:")
            QMessageBox.critical(self.view, "Erro Crítico", f"Não foi possível abrir o gerenciador de alimentos:\n{e}")

    # --- Slots para Ajuda --- 
    @Slot()
    def _handle_about(self):
        """Mostra a janela \"Sobre\"."""
        logging.info("Ação: Sobre")
        QMessageBox.about(self.view, "Sobre o Sistema Nutricional",
                          "<b>Sistema de Gestão Nutricional Desktop</b>\nVersão 0.3.0 (Desenvolvimento)\n\nCriado com Python e PySide6.")

    @Slot()
    def _handle_quit(self):
        """Fecha a aplicação."""
        logging.info("Ação: Sair")
        # Adicionar confirmação?
        # confirm = QMessageBox.question(self.view, "Sair", "Deseja realmente sair da aplicação?",
        #                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if confirm == QMessageBox.Yes:
        #     self.view.close()
        self.view.close()

