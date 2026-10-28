import pandas as pd
from src.portfolio_summary import preparar_resumo_regional


def linhas(ano=2026):
    return [
        {"municipio": "Taubaté", "indicador":"populacao_estimada", "ano":str(ano),
         "valor":"323380", "unidade":"pessoas", "fonte":"IBGE"},
        {"municipio": "Tremembé", "indicador":"populacao_estimada", "ano":str(ano),
         "valor":"53734", "unidade":"pessoas", "fonte":"IBGE"},
    ]


def test_fallback_sem_gold():
    dados, origem, coleta = preparar_resumo_regional(pd.DataFrame(), "populacao_estimada", linhas(), "2026-10-27T20:00:00+00:00")
    assert len(dados) == 2 and origem == "snapshot de referência"
    assert coleta.startswith("2026-10-27")


def test_gold_tem_preferencia():
    gold = pd.DataFrame(linhas(2025))
    dados, origem, _ = preparar_resumo_regional(gold, "populacao_estimada", linhas(), "hoje")
    assert origem == "Gold local" and set(dados.ano) == {2025}


def test_nao_mistura_anos():
    parcial = linhas()[:1] + [linhas(2025)[1]]
    dados, origem, _ = preparar_resumo_regional(pd.DataFrame(parcial), "populacao_estimada", linhas(), "ontem")
    assert origem == "snapshot de referência" and len(dados) == 2


def test_indicador_ausente():
    dados, origem, _ = preparar_resumo_regional(pd.DataFrame(), "pib_municipal", linhas(), None)
    assert dados.empty and origem == "indisponível"
