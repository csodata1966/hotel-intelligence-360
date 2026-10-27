"""Conector da API pública de localidades do IBGE."""
from dataclasses import dataclass

import httpx

BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"
MUNICIPIOS = {"Taubaté": 3554102, "Tremembé": 3554805}


@dataclass(frozen=True)
class Municipio:
    codigo_ibge: int
    nome: str
    uf: str
    regiao_imediata: str | None


def obter_municipio(codigo_ibge: int, client: httpx.Client | None = None) -> Municipio:
    """Consulta município por código IBGE, com timeout e erros explícitos."""
    if codigo_ibge not in MUNICIPIOS.values():
        raise ValueError("Município fora do escopo inicial: Taubaté e Tremembé.")
    def fetch(c: httpx.Client) -> dict:
        resposta = c.get(f"{BASE_URL}/municipios/{codigo_ibge}")
        resposta.raise_for_status()
        return resposta.json()
    if client is None:
        with httpx.Client(timeout=15, follow_redirects=True) as new_client:
            raw = fetch(new_client)
    else:
        raw = fetch(client)
    regiao = raw.get("regiao-imediata") or {}
    uf = (((raw.get("microrregiao") or {}).get("mesorregiao") or {}).get("UF") or {})
    if not uf:
        uf = (((regiao.get("regiao-intermediaria") or {}).get("UF")) or {})
    if not isinstance(raw.get("id"), int) or not isinstance(raw.get("nome"), str):
        raise ValueError("Formato inesperado na resposta do IBGE")
    return Municipio(
        codigo_ibge=raw["id"], nome=raw["nome"], uf=uf.get("sigla", ""),
        regiao_imediata=regiao.get("nome"),
    )
