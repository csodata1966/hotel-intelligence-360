"""Seleção segura dos indicadores para a Visão Executiva."""
from __future__ import annotations
import pandas as pd


def preparar_resumo_regional(gold: pd.DataFrame, indicador: str,
                             registros_referencia: list[dict],
                             data_referencia: str | None) -> tuple[pd.DataFrame, str, str]:
    """Retorna o último ano comparável das duas cidades, priorizando Gold local.

    Se o Gold não estiver disponível, utiliza snapshot público versionado.
    Nunca mistura diferentes anos na mesma comparação.
    """
    obrigatorias = {"municipio", "indicador", "ano", "valor", "unidade", "fonte"}
    candidatos = [(gold, "Gold local", "coleta gravada localmente"),
                  (pd.DataFrame(registros_referencia), "snapshot de referência", data_referencia or "não informada")]
    for frame, origem, coleta in candidatos:
        if frame.empty or not obrigatorias.issubset(frame.columns):
            continue
        filtrado = frame.loc[frame["indicador"] == indicador].copy()
        filtrado["ano"] = pd.to_numeric(filtrado["ano"], errors="coerce")
        filtrado["valor"] = pd.to_numeric(filtrado["valor"], errors="coerce")
        filtrado = filtrado.dropna(subset=["ano", "valor"])
        filtrado = filtrado[filtrado["municipio"].isin(["Taubaté", "Tremembé"])]
        if filtrado.empty:
            continue
        # Seleciona apenas anos com as duas cidades, sem misturar períodos.
        completos = filtrado.groupby("ano")["municipio"].nunique()
        anos = completos[completos == 2].index
        if len(anos) == 0:
            continue
        ultimo = max(anos)
        resultado = filtrado[filtrado["ano"] == ultimo].sort_values("municipio")
        resultado = resultado.drop_duplicates(subset=["municipio"], keep="last")
        return resultado.reset_index(drop=True), origem, coleta
    return pd.DataFrame(), "indisponível", "não informada"
