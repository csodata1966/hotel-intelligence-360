import httpx
import pytest
from src.ingestion.ibge import obter_municipio


def test_consulta_tremembe_com_resposta_mockada():
    payload = {
        "id": 3554805, "nome": "Tremembé",
        "regiao-imediata": {"nome": "Taubaté", "regiao-intermediaria": {"UF": {"sigla": "SP"}}},
    }
    def responder(request):
        assert request.url.path.endswith("/municipios/3554805")
        return httpx.Response(200, json=payload)
    with httpx.Client(transport=httpx.MockTransport(responder)) as client:
        cidade = obter_municipio(3554805, client)
    assert (cidade.nome, cidade.uf, cidade.regiao_imediata) == ("Tremembé", "SP", "Taubaté")


def test_rejeita_codigo_fora_do_escopo():
    with pytest.raises(ValueError, match="fora do escopo"):
        obter_municipio(9999999)


def test_erro_http_propagado():
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))) as client:
        with pytest.raises(httpx.HTTPStatusError):
            obter_municipio(3554102, client)
