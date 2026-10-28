from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")


def test_executive_tabs_exist():
    for label in ("Visão executiva", "Clima e histórico", "Calendário", "Mercado regional", "Simulador"):
        assert label in SOURCE


def test_preserves_modules_and_sources():
    for symbol in ("obter_previsao", "obter_feriados", "consultar_indicador", "salvar_coleta", "salvar_indicadores", "salvar_feriados", "RevPAR"):
        assert symbol in SOURCE


def test_disclaims_simulation():
    assert "hipotéticos" in SOURCE
    assert "não estima demanda" in SOURCE
