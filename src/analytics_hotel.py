"""Cálculos puros para simulações de hospedagem, sem dependência de Streamlit."""
from dataclasses import dataclass


@dataclass(frozen=True)
class IndicadoresHotel:
    diarias_disponiveis: int
    diarias_ocupadas: float
    receita: float
    adr: float
    revpar: float


@dataclass(frozen=True)
class CenarioHotel:
    nome: str
    ocupacao: int
    indicadores: IndicadoresHotel


def calcular_indicadores(quartos: int, dias: int, ocupacao: float, adr: float) -> IndicadoresHotel:
    if quartos <= 0 or dias <= 0 or not 0 <= ocupacao <= 100 or adr < 0:
        raise ValueError("Quartos e dias devem ser positivos; ocupação 0–100%; ADR não negativo")
    disponiveis = quartos * dias
    ocupadas = disponiveis * ocupacao / 100
    receita = ocupadas * adr
    return IndicadoresHotel(disponiveis, ocupadas, receita, adr, receita / disponiveis)


def calcular_cenarios(quartos: int, dias: int, ocupacao: int, adr: float) -> list[CenarioHotel]:
    return [CenarioHotel(nome, taxa, calcular_indicadores(quartos, dias, taxa, adr))
            for nome, taxa in (
                ("Conservador", max(0, ocupacao - 10)),
                ("Base", ocupacao),
                ("Otimista", min(100, ocupacao + 10)),
            )]


def formatar_brl(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
