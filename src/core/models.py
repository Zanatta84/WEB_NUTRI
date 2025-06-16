# src/core/models.py

from dataclasses import dataclass, field
from typing import Optional, List

# Usar dataclasses para criar modelos de dados simples e claros

@dataclass
class Paciente:
    """Representa um paciente no sistema."""
    id: Optional[int] = None
    nome_completo: str = ""
    data_nascimento: str = ""  # Formato "YYYY-MM-DD"
    sexo: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    objetivo_consulta: Optional[str] = None
    historico_clinico: Optional[str] = None
    observacoes: Optional[str] = None
    data_cadastro: Optional[str] = None # Será preenchido pelo DB

@dataclass
class Avaliacao:
    """Representa uma avaliação nutricional de um paciente."""
    paciente_id: int # Chave estrangeira para Paciente
    id: Optional[int] = None
    data_avaliacao: str = "" # Formato "YYYY-MM-DD HH:MM:SS" ou similar
    peso: Optional[float] = None
    altura: Optional[float] = None # Em metros
    circunferencia_cintura: Optional[float] = None # Em cm
    circunferencia_quadril: Optional[float] = None # Em cm
    # Adicionar outras medidas antropométricas conforme necessário (dobras, etc.)
    anamnese_resumo: Optional[str] = None # Campo para resumo da anamnese ou link para dados mais detalhados
    exames_resumo: Optional[str] = None # Campo para resumo de exames ou link
    observacoes: Optional[str] = None

@dataclass
class Alimento:
    """Representa um alimento no banco de dados local."""
    id: Optional[int] = None
    nome: str = ""
    grupo: Optional[str] = None # Ex: "Frutas", "Cereais", "Laticínios"
    unidade_padrao: str = "g" # Ex: "g", "ml", "unidade", "fatia"
    kcal_por_unidade: Optional[float] = None # Kcal por unidade_padrao (ex: por 100g)
    cho_por_unidade: Optional[float] = None # Carboidratos por unidade_padrao
    ptn_por_unidade: Optional[float] = None # Proteínas por unidade_padrao
    lip_por_unidade: Optional[float] = None # Gorduras por unidade_padrao
    # Adicionar outros nutrientes se necessário (fibras, vitaminas, minerais)
    fonte_dados: Optional[str] = None # Ex: "TACO", "Usuário"

@dataclass
class ItemPlanoAlimentar:
    """Representa um item (alimento) dentro de uma refeição de um plano alimentar."""
    plano_alimentar_id: int # Chave estrangeira para PlanoAlimentar
    alimento_id: int # Chave estrangeira para Alimento
    refeicao: str = "" # Ex: "Café da Manhã", "Almoço"
    quantidade: float = 1.0 # Quantidade numérica
    unidade_medida: str = "" # Unidade da quantidade (ex: "g", "unidade", "xícara")
    id: Optional[int] = None
    # Campos calculados (podem ser preenchidos ao carregar/calcular o plano)
    nome_alimento: Optional[str] = None # Para exibição fácil
    kcal_calculado: Optional[float] = None
    cho_calculado: Optional[float] = None
    ptn_calculado: Optional[float] = None
    lip_calculado: Optional[float] = None

@dataclass
class PlanoAlimentar:
    """Representa um plano alimentar completo para um paciente."""
    paciente_id: int # Chave estrangeira para Paciente
    id: Optional[int] = None
    nome_plano: str = "Plano Alimentar Padrão"
    data_criacao: str = "" # Formato "YYYY-MM-DD HH:MM:SS"
    objetivo: Optional[str] = None # Ex: "Emagrecimento", "Hipertrofia"
    meta_kcal: Optional[float] = None
    meta_cho_perc: Optional[float] = None # Percentual
    meta_ptn_perc: Optional[float] = None # Percentual
    meta_lip_perc: Optional[float] = None # Percentual
    observacoes_gerais: Optional[str] = None
    # A lista de itens será gerenciada separadamente ou carregada sob demanda
    # itens: List[ItemPlanoAlimentar] = field(default_factory=list) # Evitar carregar tudo sempre


