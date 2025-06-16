# src/core/repositories.py

import sqlite3
import logging
from typing import List, Optional, Any, Dict
from datetime import datetime

# Tenta importar de forma relativa primeiro
try:
    from .database import create_connection
    from .models import Paciente, Avaliacao, Alimento, PlanoAlimentar, ItemPlanoAlimentar
except ImportError:
    # Fallback
    from src.core.database import get_db_connection
    from src.core.models import Paciente, Avaliacao, Alimento, PlanoAlimentar, ItemPlanoAlimentar

# --- Paciente Repository --- 
class PacienteRepository:
    """Gerencia operações CRUD para Pacientes no banco de dados."""
    def __init__(self):
        self.conn = get_db_connection()

    def add(self, paciente: Paciente) -> Optional[int]:
        """Adiciona um novo paciente ao banco de dados."""
        sql = """INSERT INTO pacientes(nome_completo, data_nascimento, sexo, telefone, email, endereco, objetivo_consulta, historico_clinico, observacoes, data_cadastro)
                 VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(sql, (
                paciente.nome_completo, paciente.data_nascimento, paciente.sexo,
                paciente.telefone, paciente.email, paciente.endereco,
                paciente.objetivo_consulta, paciente.historico_clinico, paciente.observacoes,
                now
            ))
            self.conn.commit()
            logging.info(f"Paciente \"{paciente.nome_completo}\" adicionado com ID: {cursor.lastrowid}")
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            logging.warning(f"Erro de integridade ao adicionar paciente {paciente.nome_completo}: {e}")
            self.conn.rollback()
            return None
        except Exception as e:
            logging.exception(f"Erro inesperado ao adicionar paciente {paciente.nome_completo}:")
            self.conn.rollback()
            raise # Re-levanta a exceção para tratamento superior

    def update(self, paciente: Paciente) -> bool:
        """Atualiza os dados de um paciente existente."""
        if not paciente.id:
            logging.error("Tentativa de atualizar paciente sem ID.")
            return False
        sql = """UPDATE pacientes SET 
                 nome_completo = ?, data_nascimento = ?, sexo = ?, telefone = ?, email = ?, 
                 endereco = ?, objetivo_consulta = ?, historico_clinico = ?, observacoes = ?
                 WHERE id = ?"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                paciente.nome_completo, paciente.data_nascimento, paciente.sexo,
                paciente.telefone, paciente.email, paciente.endereco,
                paciente.objetivo_consulta, paciente.historico_clinico, paciente.observacoes,
                paciente.id
            ))
            self.conn.commit()
            if cursor.rowcount == 0:
                logging.warning(f"Nenhum paciente encontrado com ID {paciente.id} para atualizar.")
                return False
            logging.info(f"Paciente ID {paciente.id} atualizado.")
            return True
        except sqlite3.IntegrityError as e:
            logging.warning(f"Erro de integridade ao atualizar paciente ID {paciente.id}: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            logging.exception(f"Erro inesperado ao atualizar paciente ID {paciente.id}:")
            self.conn.rollback()
            raise

    def delete(self, paciente_id: int) -> bool:
        """Exclui um paciente e seus dados relacionados (avaliações, planos)."""
        # Usar transação para garantir atomicidade
        try:
            cursor = self.conn.cursor()
            # Excluir itens dos planos do paciente
            cursor.execute("DELETE FROM itens_plano_alimentar WHERE plano_alimentar_id IN (SELECT id FROM planos_alimentares WHERE paciente_id = ?)", (paciente_id,))
            logging.info(f"{cursor.rowcount} itens de planos alimentares excluídos para paciente ID {paciente_id}.")
            # Excluir planos do paciente
            cursor.execute("DELETE FROM planos_alimentares WHERE paciente_id = ?", (paciente_id,))
            logging.info(f"{cursor.rowcount} planos alimentares excluídos para paciente ID {paciente_id}.")
            # Excluir avaliações do paciente
            cursor.execute("DELETE FROM avaliacoes WHERE paciente_id = ?", (paciente_id,))
            logging.info(f"{cursor.rowcount} avaliações excluídas para paciente ID {paciente_id}.")
            # Excluir paciente
            cursor.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            if deleted_count == 0:
                logging.warning(f"Nenhum paciente encontrado com ID {paciente_id} para excluir.")
                return False
            logging.info(f"Paciente ID {paciente_id} e dados relacionados excluídos.")
            return True
        except Exception as e:
            logging.exception(f"Erro inesperado ao excluir paciente ID {paciente_id} e dados relacionados:")
            self.conn.rollback()
            raise

    def get_by_id(self, paciente_id: int) -> Optional[Paciente]:
        """Busca um paciente pelo ID."""
        sql = "SELECT * FROM pacientes WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (paciente_id,))
            row = cursor.fetchone()
            return Paciente(**row) if row else None
        except Exception as e:
            logging.exception(f"Erro ao buscar paciente por ID {paciente_id}:")
            raise

    def get_all(self) -> List[Paciente]:
        """Retorna todos os pacientes."""
        sql = "SELECT * FROM pacientes ORDER BY nome_completo"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Paciente(**row) for row in rows]
        except Exception as e:
            logging.exception("Erro ao buscar todos os pacientes:")
            raise

# --- Avaliacao Repository --- 
class AvaliacaoRepository:
    """Gerencia operações CRUD para Avaliações."""
    def __init__(self):
        self.conn = get_db_connection()

    def add(self, avaliacao: Avaliacao) -> Optional[int]:
        sql = """INSERT INTO avaliacoes (paciente_id, data_avaliacao, peso, altura, 
                 circunferencia_cintura, circunferencia_quadril, circunferencia_braco, 
                 dobra_tricipital, dobra_subescapular, dobra_suprailiaca, dobra_abdominal, 
                 observacoes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        try:
            cursor = self.conn.cursor()
            # Usar data atual se não fornecida?
            data_aval = avaliacao.data_avaliacao or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(sql, (
                avaliacao.paciente_id, data_aval, avaliacao.peso, avaliacao.altura,
                avaliacao.circunferencia_cintura, avaliacao.circunferencia_quadril, avaliacao.circunferencia_braco,
                avaliacao.dobra_tricipital, avaliacao.dobra_subescapular, avaliacao.dobra_suprailiaca, 
                avaliacao.dobra_abdominal, avaliacao.observacoes
            ))
            self.conn.commit()
            logging.info(f"Avaliação adicionada com ID: {cursor.lastrowid} para paciente ID {avaliacao.paciente_id}")
            return cursor.lastrowid
        except Exception as e:
            logging.exception(f"Erro ao adicionar avaliação para paciente ID {avaliacao.paciente_id}:")
            self.conn.rollback()
            raise

    def get_by_paciente_id(self, paciente_id: int) -> List[Avaliacao]:
        sql = "SELECT * FROM avaliacoes WHERE paciente_id = ? ORDER BY data_avaliacao DESC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (paciente_id,))
            rows = cursor.fetchall()
            return [Avaliacao(**row) for row in rows]
        except Exception as e:
            logging.exception(f"Erro ao buscar avaliações para paciente ID {paciente_id}:")
            raise
            
    # TODO: Implementar update e delete para avaliações se necessário

# --- Alimento Repository --- 
class AlimentoRepository:
    """Gerencia operações CRUD para Alimentos."""
    def __init__(self):
        self.conn = get_db_connection()

    def add(self, alimento: Alimento) -> Optional[int]:
        sql = """INSERT INTO alimentos (nome, grupo, unidade_padrao, kcal_por_unidade, 
                 cho_por_unidade, ptn_por_unidade, lip_por_unidade, fibras_por_unidade, 
                 sodio_mg_por_unidade, fonte_dados, observacoes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                alimento.nome, alimento.grupo, alimento.unidade_padrao, alimento.kcal_por_unidade,
                alimento.cho_por_unidade, alimento.ptn_por_unidade, alimento.lip_por_unidade,
                alimento.fibras_por_unidade, alimento.sodio_mg_por_unidade, alimento.fonte_dados,
                alimento.observacoes
            ))
            self.conn.commit()
            logging.info(f"Alimento \"{alimento.nome}\" adicionado com ID: {cursor.lastrowid}")
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            logging.warning(f"Erro de integridade ao adicionar alimento {alimento.nome}: {e}")
            self.conn.rollback()
            return None
        except Exception as e:
            logging.exception(f"Erro inesperado ao adicionar alimento {alimento.nome}:")
            self.conn.rollback()
            raise

    def update(self, alimento: Alimento) -> bool:
        if not alimento.id:
            logging.error("Tentativa de atualizar alimento sem ID.")
            return False
        sql = """UPDATE alimentos SET 
                 nome = ?, grupo = ?, unidade_padrao = ?, kcal_por_unidade = ?, 
                 cho_por_unidade = ?, ptn_por_unidade = ?, lip_por_unidade = ?, 
                 fibras_por_unidade = ?, sodio_mg_por_unidade = ?, fonte_dados = ?, observacoes = ?
                 WHERE id = ?"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                alimento.nome, alimento.grupo, alimento.unidade_padrao, alimento.kcal_por_unidade,
                alimento.cho_por_unidade, alimento.ptn_por_unidade, alimento.lip_por_unidade,
                alimento.fibras_por_unidade, alimento.sodio_mg_por_unidade, alimento.fonte_dados,
                alimento.observacoes, alimento.id
            ))
            self.conn.commit()
            if cursor.rowcount == 0:
                logging.warning(f"Nenhum alimento encontrado com ID {alimento.id} para atualizar.")
                return False
            logging.info(f"Alimento ID {alimento.id} atualizado.")
            return True
        except sqlite3.IntegrityError as e:
            logging.warning(f"Erro de integridade ao atualizar alimento ID {alimento.id}: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            logging.exception(f"Erro inesperado ao atualizar alimento ID {alimento.id}:")
            self.conn.rollback()
            raise

    def delete(self, alimento_id: int) -> bool:
        # Verificar se o alimento está em uso em algum item de plano?
        # Por simplicidade, vamos permitir a exclusão, mas isso pode quebrar planos existentes.
        # Idealmente, marcar como inativo ou impedir exclusão se em uso.
        sql_check = "SELECT 1 FROM itens_plano_alimentar WHERE alimento_id = ? LIMIT 1"
        sql_delete = "DELETE FROM alimentos WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_check, (alimento_id,))
            if cursor.fetchone():
                logging.warning(f"Tentativa de excluir alimento ID {alimento_id} que está em uso em planos alimentares.")
                # Impedir exclusão ou apenas avisar?
                # return False # Impedir
                pass # Permitir, mas avisar
                
            cursor.execute(sql_delete, (alimento_id,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            if deleted_count == 0:
                logging.warning(f"Nenhum alimento encontrado com ID {alimento_id} para excluir.")
                return False
            logging.info(f"Alimento ID {alimento_id} excluído.")
            return True
        except Exception as e:
            logging.exception(f"Erro inesperado ao excluir alimento ID {alimento_id}:")
            self.conn.rollback()
            raise

    def get_by_id(self, alimento_id: int) -> Optional[Alimento]:
        sql = "SELECT * FROM alimentos WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (alimento_id,))
            row = cursor.fetchone()
            return Alimento(**row) if row else None
        except Exception as e:
            logging.exception(f"Erro ao buscar alimento por ID {alimento_id}:")
            raise

    def get_all(self, limit: Optional[int] = None) -> List[Alimento]:
        sql = "SELECT * FROM alimentos ORDER BY nome"
        if limit:
            sql += f" LIMIT {limit}"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Alimento(**row) for row in rows]
        except Exception as e:
            logging.exception("Erro ao buscar todos os alimentos:")
            raise

    def search_by_name(self, term: str, limit: Optional[int] = None) -> List[Alimento]:
        sql = "SELECT * FROM alimentos WHERE nome LIKE ? ORDER BY nome"
        if limit:
            sql += f" LIMIT {limit}"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (f"%{term}%",))
            rows = cursor.fetchall()
            return [Alimento(**row) for row in rows]
        except Exception as e:
            logging.exception(f"Erro ao buscar alimentos por termo \"{term}\":")
            raise

# --- PlanoAlimentar Repository --- 
class PlanoAlimentarRepository:
    """Gerencia operações CRUD para Planos Alimentares."""
    def __init__(self):
        self.conn = get_db_connection()

    def add(self, plano: PlanoAlimentar) -> Optional[int]:
        """Adiciona um novo plano alimentar."""
        sql = """INSERT INTO planos_alimentares (paciente_id, nome_plano, objetivo, meta_kcal, observacoes, data_criacao)
                 VALUES (?, ?, ?, ?, ?, ?)"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(sql, (
                plano.paciente_id, plano.nome_plano, plano.objetivo,
                plano.meta_kcal, plano.observacoes, now
            ))
            self.conn.commit()
            plano_id = cursor.lastrowid
            logging.info(f"Plano alimentar \"{plano.nome_plano}\" adicionado com ID: {plano_id} para paciente ID {plano.paciente_id}")
            return plano_id
        except Exception as e:
            logging.exception(f"Erro ao adicionar plano alimentar para paciente ID {plano.paciente_id}:")
            self.conn.rollback()
            raise

    def update(self, plano: PlanoAlimentar) -> bool:
        """Atualiza os dados de um plano alimentar existente."""
        if not plano.id:
            logging.error("Tentativa de atualizar plano alimentar sem ID.")
            return False
        sql = """UPDATE planos_alimentares SET 
                 nome_plano = ?, objetivo = ?, meta_kcal = ?, observacoes = ?
                 WHERE id = ? AND paciente_id = ?"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                plano.nome_plano, plano.objetivo, plano.meta_kcal, 
                plano.observacoes, plano.id, plano.paciente_id
            ))
            self.conn.commit()
            if cursor.rowcount == 0:
                logging.warning(f"Nenhum plano alimentar encontrado com ID {plano.id} para paciente ID {plano.paciente_id} para atualizar.")
                return False
            logging.info(f"Plano alimentar ID {plano.id} atualizado.")
            return True
        except Exception as e:
            logging.exception(f"Erro inesperado ao atualizar plano alimentar ID {plano.id}:")
            self.conn.rollback()
            raise

    def delete(self, plano_id: int) -> bool:
        """Exclui um plano alimentar e seus itens."""
        try:
            cursor = self.conn.cursor()
            # Excluir itens primeiro
            cursor.execute("DELETE FROM itens_plano_alimentar WHERE plano_alimentar_id = ?", (plano_id,))
            logging.info(f"{cursor.rowcount} itens excluídos para o plano ID {plano_id}.")
            # Excluir plano
            cursor.execute("DELETE FROM planos_alimentares WHERE id = ?", (plano_id,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            if deleted_count == 0:
                logging.warning(f"Nenhum plano alimentar encontrado com ID {plano_id} para excluir.")
                return False
            logging.info(f"Plano alimentar ID {plano_id} e seus itens excluídos.")
            return True
        except Exception as e:
            logging.exception(f"Erro inesperado ao excluir plano alimentar ID {plano_id}:")
            self.conn.rollback()
            raise

    def get_by_id(self, plano_id: int) -> Optional[PlanoAlimentar]:
        sql = "SELECT * FROM planos_alimentares WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (plano_id,))
            row = cursor.fetchone()
            return PlanoAlimentar(**row) if row else None
        except Exception as e:
            logging.exception(f"Erro ao buscar plano alimentar por ID {plano_id}:")
            raise

    def get_by_paciente_id(self, paciente_id: int) -> List[PlanoAlimentar]:
        sql = "SELECT * FROM planos_alimentares WHERE paciente_id = ? ORDER BY data_criacao DESC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (paciente_id,))
            rows = cursor.fetchall()
            return [PlanoAlimentar(**row) for row in rows]
        except Exception as e:
            logging.exception(f"Erro ao buscar planos alimentares para paciente ID {paciente_id}:")
            raise

# --- ItemPlanoAlimentar Repository --- 
class ItemPlanoAlimentarRepository:
    """Gerencia operações CRUD para Itens de Planos Alimentares."""
    def __init__(self):
        self.conn = get_db_connection()

    def add_batch(self, itens: List[ItemPlanoAlimentar]) -> bool:
        """Adiciona uma lista de itens de plano alimentar em lote."""
        if not itens:
            return True # Nada a fazer
            
        sql = """INSERT INTO itens_plano_alimentar (plano_alimentar_id, refeicao, alimento_id, 
                 quantidade, unidade_medida, observacoes, 
                 kcal_calculado, cho_calculado, ptn_calculado, lip_calculado)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        
        # Preparar dados para executemany
        data_to_insert = []
        for item in itens:
            if item.plano_alimentar_id is None:
                logging.error(f"Tentativa de adicionar item sem plano_alimentar_id: {item}")
                return False # Não pode adicionar item sem ID do plano
            data_to_insert.append((
                item.plano_alimentar_id, item.refeicao, item.alimento_id,
                item.quantidade, item.unidade_medida, item.observacoes,
                item.kcal_calculado, item.cho_calculado, item.ptn_calculado, item.lip_calculado
            ))
            
        try:
            cursor = self.conn.cursor()
            cursor.executemany(sql, data_to_insert)
            self.conn.commit()
            logging.info(f"{len(itens)} itens adicionados em lote para o plano ID {itens[0].plano_alimentar_id}.")
            return True
        except Exception as e:
            logging.exception(f"Erro ao adicionar itens em lote para o plano ID {itens[0].plano_alimentar_id}:")
            self.conn.rollback()
            raise

    def delete_by_plano_id(self, plano_id: int) -> int:
        """Exclui todos os itens associados a um plano alimentar."""
        sql = "DELETE FROM itens_plano_alimentar WHERE plano_alimentar_id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (plano_id,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            logging.info(f"{deleted_count} itens excluídos para o plano ID {plano_id} (antes de adicionar novos).")
            return deleted_count
        except Exception as e:
            logging.exception(f"Erro ao excluir itens para o plano ID {plano_id}:")
            self.conn.rollback()
            raise

    def get_by_plano_id(self, plano_id: int) -> List[ItemPlanoAlimentar]:
        """Busca todos os itens associados a um plano alimentar."""
        # Adicionar nome do alimento via JOIN para facilitar exibição
        sql = """SELECT i.*, a.nome as nome_alimento 
                 FROM itens_plano_alimentar i
                 LEFT JOIN alimentos a ON i.alimento_id = a.id
                 WHERE i.plano_alimentar_id = ? 
                 ORDER BY i.id -- ou por refeicao?
              """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (plano_id,))
            rows = cursor.fetchall()
            # Criar objetos ItemPlanoAlimentar, incluindo nome_alimento
            itens = []
            for row_dict in rows:
                # nome_alimento não faz parte do __init__ padrão, mas podemos adicionar
                item = ItemPlanoAlimentar(**{k: v for k, v in row_dict.items() if k != 'nome_alimento'})
                item.nome_alimento = row_dict.get('nome_alimento', f"<Alimento ID {item.alimento_id} não encontrado>")
                itens.append(item)
            return itens
        except Exception as e:
            logging.exception(f"Erro ao buscar itens para o plano ID {plano_id}:")
            raise

    # TODO: Implementar update e delete individuais para itens se necessário

