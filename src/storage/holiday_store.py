"""Persistência de feriados: Bronze JSON, Silver Parquet, Gold Parquet via DuckDB."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
import duckdb
import pandas as pd
from src.ingestion.brasilapi import Feriado
from src.analytics_holidays import classificar_data


def salvar_feriados(ano: int, feriados: list[Feriado], raiz: Path,
                    coletado_em: datetime | None = None) -> str:
    if not 1900 <= ano <= 2199 or any(f.dia.year != ano for f in feriados):
        raise ValueError('Ano incompatível com os feriados')
    instante = coletado_em or datetime.now(timezone.utc)
    if instante.tzinfo is None:
        raise ValueError('Timestamp sem timezone')
    instante = instante.astimezone(timezone.utc)
    coleta_id = instante.strftime('%Y%m%dT%H%M%S%fZ') + '_' + uuid4().hex[:8]
    raiz = Path(raiz)
    bronze, silver = raiz / 'bronze' / 'feriados' / str(ano), raiz / 'silver' / 'feriados' / str(ano)
    bronze.mkdir(parents=True, exist_ok=True)
    silver.mkdir(parents=True, exist_ok=True)
    linhas = [{'ano': ano, 'dia': f.dia.isoformat(), 'nome': f.nome, 'tipo': f.tipo,
               'coletado_em_utc': instante.isoformat(), 'coleta_id': coleta_id} for f in feriados]
    (bronze / f'{coleta_id}.json').write_text(json.dumps({'fonte':'BrasilAPI', 'tipo':'calendario', 'linhas':linhas}, ensure_ascii=False,indent=2),encoding='utf-8')
    # Preserva schema mesmo quando a API retorna zero datas.
    frame = pd.DataFrame(linhas, columns=['ano','dia','nome','tipo','coletado_em_utc','coleta_id'])
    frame['classificacao'] = [classificar_data(f.dia, f.nome, f.tipo)[0] for f in feriados]
    frame['referencia_classificacao'] = [classificar_data(f.dia, f.nome, f.tipo)[1] for f in feriados]
    frame['dia'] = pd.to_datetime(frame['dia'])
    frame['coletado_em_utc'] = pd.to_datetime(frame['coletado_em_utc'],utc=True)
    frame.to_parquet(silver / f'{coleta_id}.parquet',index=False)
    gerar_gold_feriados(raiz)
    return coleta_id


def gerar_gold_feriados(raiz: Path) -> int:
    raiz = Path(raiz)
    arquivos = sorted((raiz/'silver'/'feriados').glob('*/*.parquet'))
    if not arquivos:
        return 0
    with duckdb.connect() as con:
        con.from_parquet([str(p) for p in arquivos]).create_view('feriados')
        frame = con.execute('''
            SELECT ano, dia, nome, tipo, coletado_em_utc, coleta_id
            FROM feriados
            QUALIFY row_number() OVER (
                PARTITION BY ano, dia, nome
                ORDER BY coletado_em_utc DESC, coleta_id DESC
            ) = 1
            ORDER BY dia, nome
        ''').df()
    # DuckDB .df() pode converter TIMESTAMPTZ para o fuso local do processo.
    # Normalizamos explicitamente para UTC antes de salvar a camada Gold.
    frame['coletado_em_utc'] = pd.to_datetime(frame['coletado_em_utc'], utc=True)
    # Reclassifica também snapshots Silver antigos sem modificar o dado bruto.
    frame['classificacao'] = [classificar_data(pd.Timestamp(d).date(), n, t)[0] for d,n,t in zip(frame['dia'],frame['nome'],frame['tipo'])]
    frame['referencia_classificacao'] = [classificar_data(pd.Timestamp(d).date(), n, t)[1] for d,n,t in zip(frame['dia'],frame['nome'],frame['tipo'])]
    destino = raiz/'gold'/'feriados_atuais.parquet'
    destino.parent.mkdir(parents=True,exist_ok=True)
    frame.to_parquet(destino,index=False)
    return len(frame)


def _migrar_gold_legado(raiz: Path) -> None:
    """Migra Gold antiga sem apagar o histórico Bronze/Silver."""
    caminho = raiz / 'gold' / 'feriados_atuais.parquet'
    if not caminho.exists():
        return
    with duckdb.connect() as con:
        colunas = set(con.from_parquet(str(caminho)).columns)
    if {'classificacao', 'referencia_classificacao'} <= colunas:
        return
    if list((raiz / 'silver' / 'feriados').glob('*/*.parquet')):
        gerar_gold_feriados(raiz)
        return
    frame = pd.read_parquet(caminho)
    classificacoes = [classificar_data(pd.Timestamp(d).date(), n, t)
                      for d, n, t in zip(frame['dia'], frame['nome'], frame['tipo'])]
    frame['classificacao'] = [c[0] for c in classificacoes]
    frame['referencia_classificacao'] = [c[1] for c in classificacoes]
    frame['coletado_em_utc'] = pd.to_datetime(frame['coletado_em_utc'], utc=True)
    temporario = caminho.with_name('feriados_atuais.migrando.parquet')
    frame.to_parquet(temporario, index=False)
    temporario.replace(caminho)


def consultar_feriados_gold(raiz: Path, ano: int) -> pd.DataFrame:
    raiz = Path(raiz)
    caminho = raiz / 'gold' / 'feriados_atuais.parquet'
    if not caminho.exists():
        return pd.DataFrame()
    _migrar_gold_legado(raiz)
    with duckdb.connect() as con:
        con.from_parquet(str(caminho)).create_view('gold_feriados')
        resultado = con.execute("""SELECT dia, nome, tipo, classificacao,
            referencia_classificacao, coletado_em_utc FROM gold_feriados
            WHERE ano = ? ORDER BY dia,nome""", [ano]).df()
    if 'coletado_em_utc' in resultado.columns:
        resultado['coletado_em_utc'] = pd.to_datetime(resultado['coletado_em_utc'], utc=True)
    return resultado


def total_coletas_feriados(raiz: Path, ano: int) -> int:
    return len(list((Path(raiz)/'bronze'/'feriados'/str(ano)).glob('*.json')))
