# tests/core/test_repositories.py

import pytest
import os
import sys
import datetime

# Adiciona o diretório src ao sys.path para permitir importações relativas
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), \"..\", \"..\"))
sys.path.insert(0, src_path)

from src.core.models import Paciente, Avaliacao, Alimento, PlanoAlimentar, ItemPlanoAlimentar
from src.core.repositories import (
    PacienteRepository, AvaliacaoRepository, AlimentoRepository, 
    PlanoAlimentarRepository, ItemPlanoAlimentarRepository
)
from src.core import database
from src.config import DATABASE_PATH

# Fixture para garantir que o banco de dados esteja limpo antes de cada teste
@pytest.fixture(autouse=True)
def setup_teardown_database():
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    # É crucial inicializar o DB *antes* de cada teste
    assert database.initialize_database() is True, "Falha ao inicializar banco de dados para teste"
    yield
    # if os.path.exists(DATABASE_PATH):
    #     os.remove(DATABASE_PATH)

# --- Fixtures para Repositórios ---
@pytest.fixture
def paciente_repo():
    return PacienteRepository()

@pytest.fixture
def avaliacao_repo():
    return AvaliacaoRepository()

@pytest.fixture
def alimento_repo():
    return AlimentoRepository()

@pytest.fixture
def plano_repo():
    return PlanoAlimentarRepository()

@pytest.fixture
def item_plano_repo():
    return ItemPlanoAlimentarRepository()

# --- Fixtures para Dados de Exemplo ---
@pytest.fixture
def sample_paciente(paciente_repo) -> Paciente:
    """Cria e retorna um paciente de exemplo já salvo no banco."""
    paciente_data = {
        "nome_completo": "Paciente Teste Base",
        "data_nascimento": "1988-03-10",
        "email": "paciente.base@teste.com"
    }
    paciente = Paciente(**paciente_data)
    paciente_id = paciente_repo.add(paciente)
    assert paciente_id is not None
    paciente.id = paciente_id
    return paciente

@pytest.fixture
def sample_alimento(alimento_repo) -> Alimento:
    """Cria e retorna um alimento de exemplo já salvo."""
    alimento_data = {
        "nome": "Maçã Fuji", "grupo": "Frutas", "unidade_padrao": "g",
        "kcal_por_unidade": 52, "cho_por_unidade": 14, "ptn_por_unidade": 0.3, 
        "lip_por_unidade": 0.2, "fonte_dados": "TACO"
    }
    alimento = Alimento(**alimento_data)
    alimento_id = alimento_repo.add(alimento)
    assert alimento_id is not None
    alimento.id = alimento_id
    return alimento

@pytest.fixture
def sample_plano(plano_repo, sample_paciente) -> PlanoAlimentar:
    """Cria e retorna um plano alimentar de exemplo já salvo."""
    plano_data = {
        "paciente_id": sample_paciente.id,
        "nome_plano": "Plano Teste Inicial",
        "data_criacao": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "objetivo": "Manutenção"
    }
    plano = PlanoAlimentar(**plano_data)
    plano_id = plano_repo.add(plano)
    assert plano_id is not None
    plano.id = plano_id
    return plano

# --- Testes para PacienteRepository (já existentes, omitidos para brevidade) ---
# ... (testes anteriores de PacienteRepository aqui) ...

# --- Testes para AvaliacaoRepository ---

def test_add_avaliacao(avaliacao_repo, sample_paciente):
    avaliacao_data = {
        "paciente_id": sample_paciente.id,
        "data_avaliacao": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "peso": 75.5, "altura": 1.78
    }
    avaliacao = Avaliacao(**avaliacao_data)
    avaliacao_id = avaliacao_repo.add(avaliacao)
    assert avaliacao_id is not None
    assert avaliacao_id > 0

def test_get_avaliacao_by_id(avaliacao_repo, sample_paciente):
    avaliacao_data = {"paciente_id": sample_paciente.id, "peso": 76.0}
    avaliacao = Avaliacao(**avaliacao_data)
    avaliacao_id = avaliacao_repo.add(avaliacao)
    assert avaliacao_id is not None

    retrieved = avaliacao_repo.get_by_id(avaliacao_id)
    assert retrieved is not None
    assert retrieved.id == avaliacao_id
    assert retrieved.peso == 76.0

def test_get_avaliacoes_by_paciente_id(avaliacao_repo, sample_paciente):
    avaliacao_repo.add(Avaliacao(paciente_id=sample_paciente.id, peso=75.0))
    avaliacao_repo.add(Avaliacao(paciente_id=sample_paciente.id, peso=74.5))
    # Adiciona avaliação de outro paciente (não deve ser retornada)
    # outro_paciente = ... ; avaliacao_repo.add(Avaliacao(paciente_id=outro_paciente.id, peso=60.0))
    
    avaliacoes = avaliacao_repo.get_by_paciente_id(sample_paciente.id)
    assert len(avaliacoes) == 2
    assert avaliacoes[0].peso == 74.5 # Ordenado por data DESC (mais recente primeiro)
    assert avaliacoes[1].peso == 75.0

def test_update_avaliacao(avaliacao_repo, sample_paciente):
    avaliacao = Avaliacao(paciente_id=sample_paciente.id, peso=75.0)
    avaliacao_id = avaliacao_repo.add(avaliacao)
    assert avaliacao_id is not None
    avaliacao.id = avaliacao_id

    avaliacao.peso = 75.8
    avaliacao.observacoes = "Aumento leve"
    success = avaliacao_repo.update(avaliacao)
    assert success is True

    updated = avaliacao_repo.get_by_id(avaliacao_id)
    assert updated is not None
    assert updated.peso == 75.8
    assert updated.observacoes == "Aumento leve"

def test_delete_avaliacao(avaliacao_repo, sample_paciente):
    avaliacao = Avaliacao(paciente_id=sample_paciente.id, peso=75.0)
    avaliacao_id = avaliacao_repo.add(avaliacao)
    assert avaliacao_id is not None

    success = avaliacao_repo.delete(avaliacao_id)
    assert success is True
    assert avaliacao_repo.get_by_id(avaliacao_id) is None

# --- Testes para AlimentoRepository ---

def test_add_alimento(alimento_repo):
    alimento_data = {"nome": "Banana Prata", "kcal_por_unidade": 89}
    alimento = Alimento(**alimento_data)
    alimento_id = alimento_repo.add(alimento)
    assert alimento_id is not None
    assert alimento_id > 0

def test_add_alimento_nome_unique(alimento_repo, sample_alimento):
    alimento_data = {"nome": sample_alimento.nome} # Mesmo nome
    alimento_duplicado = Alimento(**alimento_data)
    alimento_id = alimento_repo.add(alimento_duplicado)
    assert alimento_id is None # Deve falhar devido à constraint UNIQUE

def test_get_alimento_by_id(alimento_repo, sample_alimento):
    retrieved = alimento_repo.get_by_id(sample_alimento.id)
    assert retrieved is not None
    assert retrieved.id == sample_alimento.id
    assert retrieved.nome == sample_alimento.nome

def test_get_all_alimentos(alimento_repo, sample_alimento):
    alimento_repo.add(Alimento(nome="Pão Francês"))
    alimentos = alimento_repo.get_all()
    assert len(alimentos) == 2
    assert alimentos[0].nome == "Maçã Fuji" # Ordem alfabética
    assert alimentos[1].nome == "Pão Francês"

def test_search_alimento_by_name(alimento_repo, sample_alimento):
    alimento_repo.add(Alimento(nome="Maçã Verde"))
    alimento_repo.add(Alimento(nome="Suco de Maçã"))
    alimento_repo.add(Alimento(nome="Pera Williams"))

    results = alimento_repo.search_by_name("Maçã")
    assert len(results) == 3
    assert results[0].nome == "Maçã Fuji"
    assert results[1].nome == "Maçã Verde"
    assert results[2].nome == "Suco de Maçã"

    results_exact = alimento_repo.search_by_name("Maçã Fuji")
    assert len(results_exact) == 1

    results_none = alimento_repo.search_by_name("Inexistente")
    assert len(results_none) == 0

def test_update_alimento(alimento_repo, sample_alimento):
    sample_alimento.kcal_por_unidade = 55
    sample_alimento.grupo = "Frutas Vermelhas" # Errado, mas para testar update
    success = alimento_repo.update(sample_alimento)
    assert success is True

    updated = alimento_repo.get_by_id(sample_alimento.id)
    assert updated is not None
    assert updated.kcal_por_unidade == 55
    assert updated.grupo == "Frutas Vermelhas"

def test_delete_alimento(alimento_repo, sample_alimento):
    alimento_id = sample_alimento.id
    success = alimento_repo.delete(alimento_id)
    assert success is True
    assert alimento_repo.get_by_id(alimento_id) is None

# --- Testes para PlanoAlimentarRepository ---

def test_add_plano(plano_repo, sample_paciente):
    plano_data = {
        "paciente_id": sample_paciente.id,
        "nome_plano": "Plano Hipertrofia",
        "data_criacao": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "meta_kcal": 3000
    }
    plano = PlanoAlimentar(**plano_data)
    plano_id = plano_repo.add(plano)
    assert plano_id is not None
    assert plano_id > 0

def test_get_plano_by_id(plano_repo, sample_plano):
    retrieved = plano_repo.get_by_id(sample_plano.id)
    assert retrieved is not None
    assert retrieved.id == sample_plano.id
    assert retrieved.nome_plano == sample_plano.nome_plano

def test_get_planos_by_paciente_id(plano_repo, sample_paciente):
    plano_repo.add(PlanoAlimentar(paciente_id=sample_paciente.id, nome_plano="Plano A"))
    plano_repo.add(PlanoAlimentar(paciente_id=sample_paciente.id, nome_plano="Plano B"))
    planos = plano_repo.get_by_paciente_id(sample_paciente.id)
    assert len(planos) == 2 # Mais o sample_plano criado na fixture
    # A ordem depende da data de criação, difícil prever exatamente sem controlar o tempo

def test_update_plano(plano_repo, sample_plano):
    sample_plano.objetivo = "Ganho de Massa Magra"
    sample_plano.meta_kcal = 2800
    success = plano_repo.update(sample_plano)
    assert success is True

    updated = plano_repo.get_by_id(sample_plano.id)
    assert updated is not None
    assert updated.objetivo == "Ganho de Massa Magra"
    assert updated.meta_kcal == 2800

def test_delete_plano(plano_repo, sample_plano):
    plano_id = sample_plano.id
    success = plano_repo.delete(plano_id)
    assert success is True
    assert plano_repo.get_by_id(plano_id) is None

# --- Testes para ItemPlanoAlimentarRepository ---

def test_add_item_plano(item_plano_repo, sample_plano, sample_alimento):
    item_data = {
        "plano_alimentar_id": sample_plano.id,
        "refeicao": "Almoço",
        "alimento_id": sample_alimento.id,
        "quantidade": 150.0,
        "unidade_medida": "g"
    }
    item = ItemPlanoAlimentar(**item_data)
    item_id = item_plano_repo.add(item)
    assert item_id is not None
    assert item_id > 0

def test_get_item_plano_by_id(item_plano_repo, sample_plano, sample_alimento):
    item = ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="Lanche", alimento_id=sample_alimento.id, quantidade=1, unidade_medida="unidade")
    item_id = item_plano_repo.add(item)
    assert item_id is not None

    retrieved = item_plano_repo.get_by_id(item_id)
    assert retrieved is not None
    assert retrieved.id == item_id
    assert retrieved.refeicao == "Lanche"
    assert retrieved.alimento_id == sample_alimento.id
    assert retrieved.nome_alimento == sample_alimento.nome # Verifica JOIN

def test_get_itens_by_plano_id(item_plano_repo, sample_plano, sample_alimento):
    item_plano_repo.add(ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="Café", alimento_id=sample_alimento.id, quantidade=1, unidade_medida="un"))
    item_plano_repo.add(ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="Almoço", alimento_id=sample_alimento.id, quantidade=100, unidade_medida="g"))
    
    itens = item_plano_repo.get_by_plano_id(sample_plano.id)
    assert len(itens) == 2
    assert itens[0].refeicao == "Almoço" # Ordem alfabética da refeição? Ou ID? Verificar query ORDER BY
    assert itens[1].refeicao == "Café"
    assert itens[0].nome_alimento == sample_alimento.nome

def test_update_item_plano(item_plano_repo, sample_plano, sample_alimento):
    item = ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="Jantar", alimento_id=sample_alimento.id, quantidade=120, unidade_medida="g")
    item_id = item_plano_repo.add(item)
    assert item_id is not None
    item.id = item_id

    item.quantidade = 130
    item.refeicao = "Ceia"
    success = item_plano_repo.update(item)
    assert success is True

    updated = item_plano_repo.get_by_id(item_id)
    assert updated is not None
    assert updated.quantidade == 130
    assert updated.refeicao == "Ceia"

def test_delete_item_plano(item_plano_repo, sample_plano, sample_alimento):
    item = ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="Extra", alimento_id=sample_alimento.id, quantidade=50, unidade_medida="g")
    item_id = item_plano_repo.add(item)
    assert item_id is not None

    success = item_plano_repo.delete(item_id)
    assert success is True
    assert item_plano_repo.get_by_id(item_id) is None

def test_delete_itens_by_plano_id(item_plano_repo, sample_plano, sample_alimento):
    item_plano_repo.add(ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="A", alimento_id=sample_alimento.id, quantidade=1, unidade_medida="un"))
    item_plano_repo.add(ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="B", alimento_id=sample_alimento.id, quantidade=100, unidade_medida="g"))
    assert len(item_plano_repo.get_by_plano_id(sample_plano.id)) == 2

    success = item_plano_repo.delete_by_plano_id(sample_plano.id)
    assert success is True
    assert len(item_plano_repo.get_by_plano_id(sample_plano.id)) == 0

# Teste para ON DELETE CASCADE (Plano -> Itens) e ON DELETE RESTRICT (Alimento -> Itens)

def test_delete_plano_cascades_to_itens(plano_repo, item_plano_repo, sample_plano, sample_alimento):
    item_id = item_plano_repo.add(ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="C", alimento_id=sample_alimento.id, quantidade=1, unidade_medida="un"))
    assert item_id is not None
    assert item_plano_repo.get_by_id(item_id) is not None # Item existe

    # Deleta o plano pai
    success_delete_plano = plano_repo.delete(sample_plano.id)
    assert success_delete_plano is True

    # Verifica se o item foi deletado em cascata
    assert item_plano_repo.get_by_id(item_id) is None

def test_delete_alimento_restricted_when_used(alimento_repo, item_plano_repo, sample_plano, sample_alimento):
    # Adiciona um item usando o sample_alimento
    item_id = item_plano_repo.add(ItemPlanoAlimentar(plano_alimentar_id=sample_plano.id, refeicao="D", alimento_id=sample_alimento.id, quantidade=1, unidade_medida="un"))
    assert item_id is not None

    # Tenta deletar o alimento
    success_delete_alimento = alimento_repo.delete(sample_alimento.id)
    # Deve falhar por causa da restrição de chave estrangeira
    assert success_delete_alimento is False 

    # Verifica se o alimento ainda existe
    assert alimento_repo.get_by_id(sample_alimento.id) is not None
    # Verifica se o item ainda existe
    assert item_plano_repo.get_by_id(item_id) is not None

    # Agora deleta o item primeiro
    success_delete_item = item_plano_repo.delete(item_id)
    assert success_delete_item is True

    # Tenta deletar o alimento novamente
    success_delete_alimento_after = alimento_repo.delete(sample_alimento.id)
    # Agora deve funcionar
    assert success_delete_alimento_after is True
    assert alimento_repo.get_by_id(sample_alimento.id) is None


