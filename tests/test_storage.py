from datetime import date, datetime, timezone, timedelta
import json
import pytest
from src.ingestion.open_meteo import PrevisaoDiaria
from src.storage.weather_store import salvar_coleta, consultar_gold, total_coletas


def forecast(maxima=25):
    return [PrevisaoDiaria(date(2026, 10, 27) + timedelta(days=i), maxima+i, 15+i, float(i)) for i in range(7)]


def test_camadas_e_consulta(tmp_path):
    id1 = salvar_coleta("Taubaté", forecast(), tmp_path,
        datetime(2026, 10, 27, 15, tzinfo=timezone.utc))
    assert (tmp_path / "bronze" / "Taubaté" / f"{id1}.json").exists()
    raw = json.loads((tmp_path / "bronze" / "Taubaté" / f"{id1}.json").read_text(encoding="utf8"))
    assert raw["tipo"] == "previsao"
    assert (tmp_path / "silver" / "Taubaté" / f"{id1}.parquet").exists()
    assert len(consultar_gold(tmp_path, "Taubaté")) == 7
    assert total_coletas(tmp_path, "Taubaté") == 1


def test_gold_usa_coleta_mais_recente(tmp_path):
    salvar_coleta("Taubaté", forecast(25), tmp_path, datetime(2026,10,27,15,tzinfo=timezone.utc))
    salvar_coleta("Taubaté", forecast(30), tmp_path, datetime(2026,10,27,16,tzinfo=timezone.utc))
    frame = consultar_gold(tmp_path, "Taubaté")
    assert len(frame) == 7
    assert frame.iloc[0]["temp_max_c"] == 30
    assert total_coletas(tmp_path, "Taubaté") == 2


def test_separacao_municipios(tmp_path):
    salvar_coleta("Tremembé", forecast(), tmp_path)
    assert consultar_gold(tmp_path, "Taubaté").empty
    assert len(consultar_gold(tmp_path, "Tremembé")) == 7


def test_valida_entrada(tmp_path):
    with pytest.raises(ValueError):
        salvar_coleta("Cidade Desconhecida", forecast(), tmp_path)
    with pytest.raises(ValueError):
        salvar_coleta("Taubaté", forecast()[:3], tmp_path)
    with pytest.raises(ValueError):
        salvar_coleta("Taubaté", forecast(), tmp_path, datetime(2026, 10, 27, 10))
