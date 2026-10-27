"""Persistência incremental Bronze / Silver / Gold de indicadores SIDRA."""
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import json
import pandas as pd
import duckdb
from dataclasses import asdict

COLUNAS=["municipio","codigo_ibge","indicador","ano","valor","unidade","fonte","coletado_em_utc","coleta_id"]

def salvar_indicadores(indicador, dados, raiz: Path, instante=None):
    raiz=Path(raiz)
    if not dados:
        raise ValueError("Sem dados disponíveis; nenhuma coleta foi gravada")
    instante=(instante or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cid=instante.strftime('%Y%m%dT%H%M%S%fZ')+'_'+uuid4().hex[:8]
    bronze=raiz/'bronze'/'mercado'/indicador
    silver=raiz/'silver'/'mercado'/indicador
    bronze.mkdir(parents=True,exist_ok=True)
    silver.mkdir(parents=True,exist_ok=True)
    rows=[{**asdict(x),'coletado_em_utc': instante.isoformat(),'coleta_id':cid} for x in dados]
    if any(x.indicador != indicador for x in dados):
        raise ValueError('Mistura de indicadores')
    (bronze/f'{cid}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame(rows,columns=COLUNAS).to_parquet(silver/f'{cid}.parquet',index=False)
    gerar_gold(raiz)
    return cid

def gerar_gold(raiz: Path):
    raiz=Path(raiz)
    paths=sorted((raiz/'silver'/'mercado').glob('*/*.parquet'))
    if not paths:
        return 0
    dest=raiz/'gold'/'mercado_atual.parquet'
    dest.parent.mkdir(parents=True,exist_ok=True)
    with duckdb.connect() as conn:
        conn.from_parquet([str(f) for f in paths]).create_view('base')
        result=conn.execute("""SELECT municipio, codigo_ibge, indicador, ano, valor, unidade,
            fonte, coletado_em_utc, coleta_id FROM base
            QUALIFY ROW_NUMBER() OVER (
               PARTITION BY codigo_ibge, indicador, ano
               ORDER BY coletado_em_utc DESC, coleta_id DESC
            )=1""").df()
    result.to_parquet(dest,index=False)
    return len(result)

def consultar_mercado(raiz: Path):
    p=Path(raiz)/'gold'/'mercado_atual.parquet'
    if not p.exists():
        return pd.DataFrame(columns=COLUNAS)
    with duckdb.connect() as conn:
        return conn.execute('SELECT * FROM read_parquet(?) ORDER BY indicador, ano, municipio',[str(p)]).df()
