"""Previsão diária Open-Meteo, com validação explícita das respostas."""
from dataclasses import dataclass
from datetime import date
from math import isfinite

import httpx

BASE_URL = "https://api.open-meteo.com/v1/forecast"
# Coordenadas aproximadas dos centros municipais; não são do empreendimento.
COORDENADAS = {
    "Taubaté": (-23.0264, -45.5553),
    "Tremembé": (-22.9582, -45.5472),
}
VARIAVEIS = "temperature_2m_max,temperature_2m_min,precipitation_sum"


@dataclass(frozen=True)
class PrevisaoDiaria:
    dia: date
    temp_max_c: float
    temp_min_c: float
    chuva_mm: float


def obter_previsao(municipio: str, client: httpx.Client | None = None) -> list[PrevisaoDiaria]:
    """Retorna os próximos sete dias, no fuso horário local."""
    if municipio not in COORDENADAS:
        raise ValueError(f"Município indisponível: {municipio}")
    lat, lon = COORDENADAS[municipio]
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": VARIAVEIS,
        "forecast_days": 7,
        "timezone": "America/Sao_Paulo",
    }

    def fetch(c: httpx.Client) -> dict:
        response = c.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()

    if client is None:
        with httpx.Client(timeout=15, follow_redirects=True) as new_client:
            payload = fetch(new_client)
    else:
        payload = fetch(client)

    if not isinstance(payload, dict) or not isinstance(payload.get("daily"), dict):
        raise ValueError("Open-Meteo retornou estrutura inválida")
    dados = payload["daily"]
    fields = ("time", "temperature_2m_max", "temperature_2m_min", "precipitation_sum")
    valores = [dados.get(key) for key in fields]
    if any(not isinstance(v, list) or len(v) != 7 for v in valores):
        raise ValueError("Open-Meteo retornou séries ausentes ou com tamanho inesperado")

    result = []
    try:
        for dia, maxima, minima, chuva in zip(*valores):
            dt = date.fromisoformat(dia)
            mx, mn, mm = float(maxima), float(minima), float(chuva)
            if not all(map(isfinite, (mx, mn, mm))) or mx < mn or mm < 0:
                raise ValueError("Valores meteorológicos incoerentes")
            result.append(PrevisaoDiaria(dt, mx, mn, mm))
    except (TypeError, OverflowError) as exc:
        raise ValueError("Valores meteorológicos inválidos") from exc
    if len({item.dia for item in result}) != 7 or any(
        (result[i + 1].dia - result[i].dia).days != 1 for i in range(6)
    ):
        raise ValueError("Datas da previsão inválidas ou não consecutivas")
    return result
