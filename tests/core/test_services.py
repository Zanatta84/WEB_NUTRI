# tests/core/test_services.py

import pytest
import os
import sys
import math

# Adiciona o diretório src ao sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), \'..\', \'..\'))
sys.path.insert(0, src_path)

from src.core import services

# --- Testes para calcular_imc --- 

@pytest.mark.parametrize("peso, altura, expected_imc, expected_class", [
    (70, 1.75, (22.86, "Peso normal")),
    (50, 1.70, (17.3, "Abaixo do peso")),
    (85, 1.75, (27.76, "Sobrepeso")),
    (100, 1.80, (30.86, "Obesidade Grau I")),
    (120, 1.70, (41.52, "Obesidade Grau II")),
    (150, 1.85, (43.84, "Obesidade Grau III")),
])
def test_calcular_imc_valid(peso, altura, expected_imc, expected_class):
    imc, classificacao = services.calcular_imc(peso_kg=peso, altura_m=altura)
    assert imc == expected_imc
    assert classificacao == expected_class

@pytest.mark.parametrize("peso, altura", [
    (None, 1.75),
    (70, None),
    (0, 1.75),
    (70, 0),
    (-70, 1.75),
    (70, -1.75),
])
def test_calcular_imc_invalid_input(peso, altura):
    result = services.calcular_imc(peso_kg=peso, altura_m=altura)
    assert result is None

# --- Testes para calcular_geb_harris_benedict --- 

@pytest.mark.parametrize("sexo, peso, altura_cm, idade, expected_geb", [
    ("Masculino", 80, 180, 30, 1860.14),
    ("Feminino", 60, 165, 25, 1390.97),
    ("m", 95, 190, 45, 2018.94),
    ("f", 55, 160, 50, 1241.12),
])
def test_calcular_geb_harris_benedict_valid(sexo, peso, altura_cm, idade, expected_geb):
    geb = services.calcular_geb_harris_benedict(sexo=sexo, peso_kg=peso, altura_cm=altura_cm, idade_anos=idade)
    assert geb == pytest.approx(expected_geb, 0.01)

@pytest.mark.parametrize("sexo, peso, altura_cm, idade", [
    (None, 80, 180, 30),
    ("Masculino", 0, 180, 30),
    ("Masculino", 80, 0, 30),
    ("Masculino", 80, 180, 0),
    ("Outro", 80, 180, 30),
])
def test_calcular_geb_harris_benedict_invalid_input(sexo, peso, altura_cm, idade):
    geb = services.calcular_geb_harris_benedict(sexo=sexo, peso_kg=peso, altura_cm=altura_cm, idade_anos=idade)
    assert geb is None

# --- Testes para calcular_geb_mifflin_st_jeor --- 

@pytest.mark.parametrize("sexo, peso, altura_cm, idade, expected_geb", [
    ("Masculino", 80, 180, 30, 1780.00),
    ("Feminino", 60, 165, 25, 1307.50),
    ("m", 95, 190, 45, 1862.50),
    ("f", 55, 160, 50, 1139.00),
])
def test_calcular_geb_mifflin_st_jeor_valid(sexo, peso, altura_cm, idade, expected_geb):
    geb = services.calcular_geb_mifflin_st_jeor(sexo=sexo, peso_kg=peso, altura_cm=altura_cm, idade_anos=idade)
    assert geb == pytest.approx(expected_geb, 0.01)

@pytest.mark.parametrize("sexo, peso, altura_cm, idade", [
    (None, 80, 180, 30),
    ("Masculino", 0, 180, 30),
    ("Masculino", 80, 0, 30),
    ("Masculino", 80, 180, 0),
    ("Outro", 80, 180, 30),
])
def test_calcular_geb_mifflin_st_jeor_invalid_input(sexo, peso, altura_cm, idade):
    geb = services.calcular_geb_mifflin_st_jeor(sexo=sexo, peso_kg=peso, altura_cm=altura_cm, idade_anos=idade)
    assert geb is None

# --- Testes para calcular_get --- 

@pytest.mark.parametrize("geb, fator, expected_get", [
    (1800, 1.2, 2160.00), # Sedentário
    (1400, 1.375, 1925.00), # Leve
    (2000, 1.55, 3100.00), # Moderado
    (1600, 1.725, 2760.00), # Ativo
    (2200, 1.9, 4180.00), # Muito Ativo
])
def test_calcular_get_valid(geb, fator, expected_get):
    get = services.calcular_get(geb=geb, fator_atividade=fator)
    assert get == pytest.approx(expected_get, 0.01)

@pytest.mark.parametrize("geb, fator", [
    (None, 1.55),
    (1800, None),
    (0, 1.55),
    (1800, 0),
    (-1800, 1.55),
    (1800, -1.55),
])
def test_calcular_get_invalid_input(geb, fator):
    get = services.calcular_get(geb=geb, fator_atividade=fator)
    assert get is None

