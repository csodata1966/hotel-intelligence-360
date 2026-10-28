"""Leitura de snapshots de referência públicos e explicitamente datados.

Não promete atualização em tempo real e não reclassifica o dado original.
"""
from pathlib import Path
import csv
from dataclasses import dataclass
from datetime import date, datetime

@dataclass(frozen=True)
class Snapshot:
    registros: list[dict]
    coletado_em_utc: str
    fonte: str


def _ler_csv(caminho: Path, colunas: set[str]) -> Snapshot | None:
    caminho = Path(caminho)
    if not caminho.is_file():
        return None
    with caminho.open(encoding='utf-8-sig', newline='') as arquivo:
        leitor = csv.DictReader(arquivo)
        if not colunas.issubset(set(leitor.fieldnames or [])):
            return None
        linhas = list(leitor)
    if not linhas:
        return None
    datas = [r.get('coletado_em_utc','') for r in linhas if r.get('coletado_em_utc')]
    return Snapshot(linhas, max(datas) if datas else 'não informada', str(caminho.name))


def carregar_mercado(raiz: Path, indicador: str) -> Snapshot | None:
    if indicador not in {'populacao_estimada', 'pib_municipal'}:
        return None
    dados = _ler_csv(Path(raiz)/'data/reference/indicadores_regionais.csv',
                     {'municipio','codigo_ibge','indicador','ano','valor','unidade','fonte','coletado_em_utc'})
    if not dados:
        return None
    registros = []
    for linha in dados.registros:
        if linha['indicador'] != indicador:
            continue
        try:
            ano=int(linha['ano']); valor=float(linha['valor'])
            if not 2000 <= ano <= 2100 or valor < 0:
                continue
            registros.append({**linha,'ano':ano,'valor':valor})
        except (TypeError, ValueError):
            continue
    return Snapshot(registros,dados.coletado_em_utc,dados.fonte) if registros else None


def carregar_feriados(raiz: Path, ano: int) -> Snapshot | None:
    if not 2026 <= ano <= 2027:
        return None
    dados = _ler_csv(Path(raiz)/f'data/reference/feriados_{ano}.csv',
                     {'dia','nome','tipo','classificacao','referencia_classificacao','coletado_em_utc'})
    if not dados:
        return None
    validos=[]
    for linha in dados.registros:
        try:
            if date.fromisoformat(linha['dia']).year == ano:
                validos.append(linha)
        except ValueError:
            continue
    return Snapshot(validos,dados.coletado_em_utc,dados.fonte) if validos else None
