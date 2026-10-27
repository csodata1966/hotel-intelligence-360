from datetime import date
from src.analytics_holidays import classificar_data

def test_carnaval_2026_nao_feriado_nacional():
    assert classificar_data(date(2026, 2, 17), 'Carnaval', 'national')[0] == 'Ponto facultativo federal'

def test_corpus_christi_2026():
    assert classificar_data(date(2026, 6, 4), 'Corpus Christi', 'national')[0] == 'Ponto facultativo federal'

def test_pascoa_nao_e_feriado_adicional():
    assert classificar_data(date(2026, 4, 5), 'Páscoa', 'national')[0] == 'Data comemorativa'

def test_natal_feriado_nacional():
    assert classificar_data(date(2026, 12, 25), 'Natal', 'national')[0] == 'Feriado nacional'

def test_2027_nao_inventa_ponto_facultativo():
    assert classificar_data(date(2027, 2, 9), 'Carnaval', 'national')[0] == 'A verificar'
