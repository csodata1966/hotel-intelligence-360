"""Testes isolados sem internet para o conector meteorológico."""
from datetime import date

import httpx
import pytest

from src.ingestion.open_meteo import obter_previsao


def payload():
    return {"daily": {
        "time": [f"2026-10-{day:02d}" for day in range(27, 32)] + ["2026-11-01", "2026-11-02"],
        "temperature_2m_max": [28, 29, 27, 25, 26, 30, 31],
        "temperature_2m_min": [18, 19, 17, 16, 18, 20, 21],
        "precipitation_sum": [0, 2.5, 1, 0, 4, 0, 3],
    }}


def test_previsao_tremembe():
    def responder(request):
        assert request.url.params["timezone"] == "America/Sao_Paulo"
        assert request.url.params["forecast_days"] == "7"
        return httpx.Response(200, json=payload())
    with httpx.Client(transport=httpx.MockTransport(responder)) as client:
        itens = obter_previsao("Tremembé", client)
    assert len(itens) == 7
    assert itens[0].dia == date(2026, 10, 27)
    assert itens[1].chuva_mm == 2.5


def test_municipio_desconhecido():
    with pytest.raises(ValueError, match="indisponível"):
        obter_previsao("São Paulo")


def test_erro_http():
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(503))) as client:
        with pytest.raises(httpx.HTTPStatusError):
            obter_previsao("Taubaté", client)


def test_dados_incompletos():
    incompleto = payload()
    incompleto["daily"]["precipitation_sum"] = [0, 1]
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=incompleto))) as client:
        with pytest.raises(ValueError, match="séries ausentes"):
            obter_previsao("Taubaté", client)


def test_chuva_invalida():
    invalido = payload()
    invalido["daily"]["precipitation_sum"][0] = None
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=invalido))) as client:
        with pytest.raises(ValueError, match="Valores meteorológicos inválidos"):
            obter_previsao("Taubaté", client)
