import pytest
from src.analytics_hotel import calcular_indicadores, calcular_cenarios, formatar_brl


def test_valores_primeira_captura():
    m = calcular_indicadores(75, 27, 60, 250)
    assert m.diarias_disponiveis == 2025
    assert m.diarias_ocupadas == 1215
    assert m.receita == 303750
    assert m.revpar == 150


def test_valores_segunda_captura():
    m = calcular_indicadores(95, 20, 60, 250)
    assert m.receita == 285000
    assert m.revpar == 150


def test_cenario_muda_ocupacao_sem_alterar_adr():
    cenarios = calcular_cenarios(75, 30, 60, 250)
    assert [c.ocupacao for c in cenarios] == [50, 60, 70]
    assert [c.indicadores.receita for c in cenarios] == [281250, 337500, 393750]


def test_cenarios_respeitam_limites():
    assert [c.ocupacao for c in calcular_cenarios(10, 30, 0, 200)] == [0, 0, 10]
    assert [c.ocupacao for c in calcular_cenarios(10, 30, 100, 200)] == [90, 100, 100]


def test_validacao_entradas():
    with pytest.raises(ValueError):
        calcular_indicadores(0, 30, 60, 250)
    with pytest.raises(ValueError):
        calcular_indicadores(20, 30, 120, 250)


def test_formatacao_brasileira():
    assert formatar_brl(303750) == "R$ 303.750,00"
