"""Classificação conservadora das datas retornadas pela BrasilAPI.

Atributos originais da API não determinam enquadramento jurídico.
A tabela 2026 é baseada na Portaria MGI 11.460/2025 (âmbito federal).
Para 2027 não atribuir ponto facultativo sem norma anual verificada.
"""
from datetime import date

FERIADOS_NACIONAIS_FIXOS = {(1,1),(4,21),(5,1),(9,7),(10,12),(11,2),(11,15),(11,20),(12,25)}
SEXTA_SANTA = {2026: date(2026,4,3), 2027: date(2027,3,26)}
PONTOS_FACULTATIVOS_2026 = {date(2026,2,16),date(2026,2,17),date(2026,2,18),date(2026,4,20),date(2026,6,4),date(2026,6,5),date(2026,10,28),date(2026,12,24),date(2026,12,31)}
REFERENCIA_2026 = 'Portaria MGI 11.460/2025 (calendário federal 2026)'


def classificar_data(dia: date, nome: str, tipo_api: str) -> tuple[str,str]:
    nome_norm = nome.casefold()
    if (dia.month, dia.day) in FERIADOS_NACIONAIS_FIXOS or SEXTA_SANTA.get(dia.year) == dia:
        return 'Feriado nacional', 'Legislação federal (datas fixas/Paixão de Cristo)'
    if dia.year == 2026 and dia in PONTOS_FACULTATIVOS_2026:
        return 'Ponto facultativo federal', REFERENCIA_2026
    if 'páscoa' in nome_norm or 'pascoa' in nome_norm:
        return 'Data comemorativa', 'Domingo de Páscoa não é feriado nacional adicional'
    return 'A verificar', 'Consultar legislação local e calendário oficial do ano'
