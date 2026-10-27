"""Pipeline local Bronze (JSON), Silver (Parquet) e Gold (DuckDB/Parquet).

Uma coleta é um *snapshot de previsão*; não é observação do tempo ocorrido.
"""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
import re

import duckdb
import pandas as pd

from src.ingestion.open_meteo import PrevisaoDiaria

CIDADES = {"Taubaté", "Tremembé"}


def salvar_coleta(cidade: str, previsao: list[PrevisaoDiaria], raiz: Path,
                  coletado_em: datetime | None = None) -> str:
    """Persiste snapshot de previsão. Retorna identificador único da coleta."""
    if cidade not in CIDADES:
        raise ValueError("Cidade não suportada")
    if len(previsao) != 7 or len({x.dia for x in previsao}) != 7:
        raise ValueError("Previsão deve conter sete datas diferentes")
    instante = coletado_em or datetime.now(timezone.utc)
    if instante.tzinfo is None:
        raise ValueError("Horário da coleta deve conter fuso horário")
    instante = instante.astimezone(timezone.utc)
    coleta_id = instante.strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    raiz = Path(raiz)
    bronze = raiz / "bronze" / cidade
    silver = raiz / "silver" / cidade
    gold = raiz / "gold"
    for pasta in (bronze, silver, gold):
        pasta.mkdir(parents=True, exist_ok=True)
    linhas = [dict(cidade=cidade, coleta_id=coleta_id,
                   coletado_em_utc=instante.isoformat(), dia=x.dia.isoformat(),
                   temp_max_c=x.temp_max_c, temp_min_c=x.temp_min_c,
                   chuva_mm=x.chuva_mm) for x in previsao]
    # Bronze: conteúdo validado do conector, preservado como JSON para auditoria.
    (bronze / f"{coleta_id}.json").write_text(
        json.dumps({"fonte": "Open-Meteo", "tipo": "previsao", "linhas": linhas},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    # Silver: colunas tipadas em Parquet.
    frame = pd.DataFrame(linhas)
    frame["dia"] = pd.to_datetime(frame["dia"])
    frame["coletado_em_utc"] = pd.to_datetime(frame["coletado_em_utc"], utc=True)
    frame.to_parquet(silver / f"{coleta_id}.parquet", index=False)
    gerar_gold(raiz)
    return coleta_id


def gerar_gold(raiz: Path) -> int:
    """Materializa uma linha por cidade/dia com a coleta mais recente disponível."""
    raiz = Path(raiz)
    arquivos = sorted((raiz / "silver").glob("*/*.parquet"))
    destino = raiz / "gold" / "previsao_atual.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not arquivos:
        return 0
    with duckdb.connect() as conn:
        # A API relacional do DuckDB aceita listas de arquivos diretamente.
        # Não usar parâmetros (?) dentro de CREATE VIEW: o binder não os permite.
        conn.from_parquet([str(p) for p in arquivos]).create_view("previsoes")
        atual = conn.execute("""
            SELECT cidade, dia, temp_max_c, temp_min_c, chuva_mm,
                   coletado_em_utc, coleta_id
            FROM previsoes
            QUALIFY row_number() OVER (
                PARTITION BY cidade, dia ORDER BY coletado_em_utc DESC, coleta_id DESC
            ) = 1
            ORDER BY cidade, dia
        """).df()
    atual.to_parquet(destino, index=False)
    return len(atual)


def consultar_gold(raiz: Path, cidade: str) -> pd.DataFrame:
    """Consulta via SQL DuckDB; retorna tabela vazia se não houver histórico."""
    if cidade not in CIDADES:
        raise ValueError("Cidade não suportada")
    caminho = Path(raiz) / "gold" / "previsao_atual.parquet"
    if not caminho.exists():
        return pd.DataFrame()
    with duckdb.connect() as conn:
        conn.from_parquet(str(caminho)).create_view("gold_data")
        return conn.execute("""
            SELECT dia, temp_max_c, temp_min_c, chuva_mm, coletado_em_utc
            FROM gold_data WHERE cidade = ? ORDER BY dia
        """, [cidade]).df()


def total_coletas(raiz: Path, cidade: str) -> int:
    if cidade not in CIDADES:
        raise ValueError("Cidade não suportada")
    return len(list((Path(raiz) / "bronze" / cidade).glob("*.json")))
