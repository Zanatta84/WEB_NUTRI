# src/core/services.py

import math
import logging
from typing import Optional, Tuple

# Tenta importar de forma relativa primeiro
try:
    from .models import Paciente # Pode ser necessário para obter dados do paciente
except ImportError:
    from models import Paciente

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Serviços de Cálculo Nutricional ---

def calcular_imc(peso_kg: Optional[float], altura_m: Optional[float]) -> Optional[Tuple[float, str]]:
    """Calcula o Índice de Massa Corporal (IMC) e retorna o valor e a classificação."""
    if peso_kg is None or altura_m is None or peso_kg <= 0 or altura_m <= 0:
        logging.warning("Peso ou altura inválidos para cálculo de IMC.")
        return None
    
    try:
        imc = peso_kg / (altura_m ** 2)
        imc_arredondado = round(imc, 2)

        # Classificação OMS para adultos
        if imc < 18.5:
            classificacao = "Abaixo do peso"
        elif 18.5 <= imc < 25:
            classificacao = "Peso normal"
        elif 25 <= imc < 30:
            classificacao = "Sobrepeso"
        elif 30 <= imc < 35:
            classificacao = "Obesidade Grau I"
        elif 35 <= imc < 40:
            classificacao = "Obesidade Grau II"
        else: # imc >= 40
            classificacao = "Obesidade Grau III"
            
        logging.info(f"IMC calculado: {imc_arredondado} ({classificacao})")
        return imc_arredondado, classificacao
    except ZeroDivisionError:
        logging.error("Erro de divisão por zero ao calcular IMC (altura pode ser zero).")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao calcular IMC: {e}")
        return None

def calcular_geb_harris_benedict(sexo: str, peso_kg: float, altura_cm: float, idade_anos: int) -> Optional[float]:
    """Calcula o Gasto Energético Basal (GEB) usando a fórmula de Harris-Benedict (revisada)."""
    if not all([sexo, peso_kg > 0, altura_cm > 0, idade_anos > 0]):
        logging.warning("Dados inválidos para cálculo de GEB (Harris-Benedict).")
        return None
        
    geb = 0.0
    sexo_lower = sexo.lower()
    
    try:
        if sexo_lower == \'masculino\' or sexo_lower == \'m\':
            # Fórmula revisada por Roza e Shizgal (1984)
            geb = 88.362 + (13.397 * peso_kg) + (4.799 * altura_cm) - (5.677 * idade_anos)
        elif sexo_lower == \'feminino\' or sexo_lower == \'f\':
            # Fórmula revisada por Roza e Shizgal (1984)
            geb = 447.593 + (9.247 * peso_kg) + (3.098 * altura_cm) - (4.330 * idade_anos)
        else:
            logging.warning(f"Sexo inválido para cálculo de GEB: {sexo}")
            return None
            
        geb_arredondado = round(geb, 2)
        logging.info(f"GEB (Harris-Benedict) calculado: {geb_arredondado} kcal/dia")
        return geb_arredondado
    except Exception as e:
        logging.error(f"Erro ao calcular GEB (Harris-Benedict): {e}")
        return None

def calcular_geb_mifflin_st_jeor(sexo: str, peso_kg: float, altura_cm: float, idade_anos: int) -> Optional[float]:
    """Calcula o Gasto Energético Basal (GEB) usando a fórmula de Mifflin-St Jeor."""
    if not all([sexo, peso_kg > 0, altura_cm > 0, idade_anos > 0]):
        logging.warning("Dados inválidos para cálculo de GEB (Mifflin-St Jeor).")
        return None
        
    geb = 0.0
    sexo_lower = sexo.lower()
    
    try:
        if sexo_lower == \'masculino\' or sexo_lower == \'m\':
            geb = (10 * peso_kg) + (6.25 * altura_cm) - (5 * idade_anos) + 5
        elif sexo_lower == \'feminino\' or sexo_lower == \'f\':
            geb = (10 * peso_kg) + (6.25 * altura_cm) - (5 * idade_anos) - 161
        else:
            logging.warning(f"Sexo inválido para cálculo de GEB: {sexo}")
            return None
            
        geb_arredondado = round(geb, 2)
        logging.info(f"GEB (Mifflin-St Jeor) calculado: {geb_arredondado} kcal/dia")
        return geb_arredondado
    except Exception as e:
        logging.error(f"Erro ao calcular GEB (Mifflin-St Jeor): {e}")
        return None

def calcular_get(geb: Optional[float], fator_atividade: Optional[float]) -> Optional[float]:
    """Calcula o Gasto Energético Total (GET) multiplicando o GEB pelo fator de atividade."""
    if geb is None or fator_atividade is None or geb <= 0 or fator_atividade <= 0:
        logging.warning("GEB ou Fator de Atividade inválidos para cálculo de GET.")
        return None
        
    try:
        get = geb * fator_atividade
        get_arredondado = round(get, 2)
        logging.info(f"GET calculado: {get_arredondado} kcal/dia (GEB: {geb}, Fator: {fator_atividade})")
        return get_arredondado
    except Exception as e:
        logging.error(f"Erro ao calcular GET: {e}")
        return None

# --- Outros Serviços (Exemplos Futuros) ---

# def validar_plano_alimentar(plano: PlanoAlimentar, itens: List[ItemPlanoAlimentar]) -> List[str]:
#     """Valida um plano alimentar, verificando consistência e adequação às metas."""
#     erros = []
#     # Lógica de validação aqui...
#     # Ex: Verificar se total de kcal está próximo da meta
#     # Ex: Verificar se distribuição de macros está adequada
#     # Ex: Verificar se há itens com quantidade zero
#     return erros

# def calcular_nutrientes_plano(itens: List[ItemPlanoAlimentar]) -> dict:
#     """Calcula os totais de kcal e macronutrientes para uma lista de itens de plano."""
#     totais = {"kcal": 0.0, "cho": 0.0, "ptn": 0.0, "lip": 0.0}
#     # Lógica para buscar dados nutricionais de cada alimento (via AlimentoRepository?)
#     # e calcular totais com base nas quantidades e unidades
#     return totais

if __name__ == \'__main__\":
    # Testes rápidos das funções de serviço
    logging.info("Testando módulo services.py...")
    
    # Teste IMC
    imc_info = calcular_imc(peso_kg=70, altura_m=1.75)
    print(f"Teste IMC (70kg, 1.75m): {imc_info}")
    imc_info_invalido = calcular_imc(peso_kg=0, altura_m=1.75)
    print(f"Teste IMC inválido: {imc_info_invalido}")
    
    # Teste GEB Harris-Benedict
    geb_hb_m = calcular_geb_harris_benedict(sexo=\'Masculino\", peso_kg=80, altura_cm=180, idade_anos=30)
    print(f"Teste GEB H-B (M, 80kg, 180cm, 30a): {geb_hb_m} kcal/dia")
    geb_hb_f = calcular_geb_harris_benedict(sexo=\'Feminino\", peso_kg=60, altura_cm=165, idade_anos=25)
    print(f"Teste GEB H-B (F, 60kg, 165cm, 25a): {geb_hb_f} kcal/dia")
    
    # Teste GEB Mifflin-St Jeor
    geb_msj_m = calcular_geb_mifflin_st_jeor(sexo=\'m\", peso_kg=80, altura_cm=180, idade_anos=30)
    print(f"Teste GEB M-SJ (M, 80kg, 180cm, 30a): {geb_msj_m} kcal/dia")
    geb_msj_f = calcular_geb_mifflin_st_jeor(sexo=\'f\", peso_kg=60, altura_cm=165, idade_anos=25)
    print(f"Teste GEB M-SJ (F, 60kg, 165cm, 25a): {geb_msj_f} kcal/dia")
    
    # Teste GET
    if geb_msj_m:
        get_m = calcular_get(geb=geb_msj_m, fator_atividade=1.55) # Moderado
        print(f"Teste GET (M, Moderado): {get_m} kcal/dia")
    get_invalido = calcular_get(geb=None, fator_atividade=1.55)
    print(f"Teste GET inválido: {get_invalido}")
    
    logging.info("Testes do services.py concluídos.")

