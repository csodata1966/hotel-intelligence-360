"""Consulta robusta à API oficial SIDRA do IBGE, sem valores inventados."""
from dataclasses import dataclass
import httpx

CIDADES = {"Taubaté": 3554102, "Tremembé": 3554805}
BASE = "https://apisidra.ibge.gov.br/values"
FONTES = {
    "populacao_estimada": {"tabela": 6579, "variavel": 9324, "unidade": "pessoas"},
    "pib_municipal": {"tabela": 5938, "variavel": 37, "unidade": "mil R$ correntes"},
}

@dataclass(frozen=True)
class Indicador:
    municipio: str
    codigo_ibge: int
    indicador: str
    ano: int
    valor: float
    unidade: str
    fonte: str

def _valor(texto):
    if texto is None or str(texto).strip() in {"", "-", "...", "..", "X"}:
        return None
    try:
        return float(str(texto).replace(",", "."))
    except ValueError:
        return None

def processar_resposta(payload, indicador: str):
    """Transforma registros SIDRA; verifica variável, município e ano."""
    if indicador not in FONTES:
        raise ValueError("Indicador desconhecido")
    if not isinstance(payload, list) or not payload:
        raise ValueError("Resposta SIDRA inválida")
    saida = []
    info=FONTES[indicador]
    for linha in payload[1:]: # Primeira linha é cabeçalho descritivo do SIDRA
        try:
            codigo=int(linha.get("D1C", ""))
            ano=int(linha.get("D3C", ""))
            variavel=int(linha.get("D2C", ""))
        except (TypeError,ValueError):
            continue
        nome=next((n for n,c in CIDADES.items() if c==codigo), None)
        valor=_valor(linha.get("V"))
        if nome is None or variavel != info["variavel"] or not 2000 <= ano <= 2100 or valor is None or valor < 0:
            continue
        saida.append(Indicador(nome,codigo,indicador,ano,valor,info["unidade"],
                               f"IBGE/SIDRA tabela {info['tabela']}, variável {variavel}"))
    return sorted(saida,key=lambda x:(x.indicador,x.municipio,x.ano))

def consultar_indicador(indicador: str, client=None):
    if indicador not in FONTES:
        raise ValueError("Indicador desconhecido")
    info=FONTES[indicador]
    municipios=','.join(str(i) for i in CIDADES.values())
    url=f"{BASE}/t/{info['tabela']}/n6/{municipios}/v/{info['variavel']}/p/last%203"
    if client is not None:
        response=client.get(url, timeout=25)
        response.raise_for_status()
        return processar_resposta(response.json(),indicador)
    with httpx.Client(follow_redirects=True) as conn:
        response=conn.get(url, timeout=25)
        response.raise_for_status()
        return processar_resposta(response.json(),indicador)
