"""Feriados conforme BrasilAPI. A fonte pode incluir datas de ponto facultativo;
não inferir status jurídico a partir do rótulo recebido.
"""
from dataclasses import dataclass
from datetime import date
import httpx

URL = 'https://brasilapi.com.br/api/feriados/v1/{ano}'

@dataclass(frozen=True)
class Feriado:
    dia: date
    nome: str
    tipo: str


def obter_feriados(ano: int, client: httpx.Client | None = None) -> list[Feriado]:
    if not 1900 <= ano <= 2199:
        raise ValueError('Ano fora do intervalo permitido')
    def fetch(c: httpx.Client):
        r = c.get(URL.format(ano=ano))
        r.raise_for_status()
        return r.json()
    if client is None:
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            payload = fetch(c)
    else:
        payload = fetch(client)
    if not isinstance(payload, list):
        raise ValueError('BrasilAPI retornou estrutura inválida')
    feriados = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError('Item de feriado inválido')
        try:
            dia = date.fromisoformat(item['date'])
            nome = item['name']
            tipo = item.get('type', 'não informado')
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('Feriado sem campos válidos') from exc
        if dia.year != ano or not isinstance(nome, str) or not nome.strip() or not isinstance(tipo,str):
            raise ValueError('Feriado inconsistente')
        feriados.append(Feriado(dia, nome.strip(), tipo))
    if len({(f.dia, f.nome) for f in feriados}) != len(feriados):
        raise ValueError('Feriados duplicados')
    return sorted(feriados, key=lambda f: (f.dia, f.nome))
