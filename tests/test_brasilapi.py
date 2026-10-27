from datetime import date
import httpx
import pytest
from src.ingestion.brasilapi import obter_feriados

def response(request):
    return httpx.Response(200,json=[{'date':'2026-12-25','name':'Natal','type':'national'},
                                   {'date':'2026-01-01','name':'Ano Novo','type':'national'}])

def test_retorno_normalizado():
    with httpx.Client(transport=httpx.MockTransport(response)) as c:
        dados=obter_feriados(2026,c)
    assert [f.dia for f in dados]==[date(2026,1,1),date(2026,12,25)]

def test_ano_invalido():
    with pytest.raises(ValueError): obter_feriados(1800)

def test_resposta_invalida():
    with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json={'erro':'dados'}))) as c:
        with pytest.raises(ValueError): obter_feriados(2026,c)

def test_feriado_ano_errado():
    with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json=[{'date':'2027-01-01','name':'Ano Novo'}]))) as c:
        with pytest.raises(ValueError): obter_feriados(2026,c)
