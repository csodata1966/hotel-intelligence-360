# Fontes de dados

## Ativa no MVP 0.1
- IBGE Localidades: https://servicodados.ibge.gov.br/api/docs/localidades
- Endpoint: `GET https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{codigo_ibge}`
- Fonte da codificação: https://www.ibge.gov.br/explica/codigos-dos-municipios.php

## Planejadas (não integradas ainda)
- Open-Meteo: https://open-meteo.com/en/docs — respeitar termos, limites e condição de uso não comercial.
- BrasilAPI: https://brasilapi.com.br/docs — feriados nacionais.
- IBGE Agregados/SIDRA: https://servicodados.ibge.gov.br/api/v3/agregados — escolher indicadores com cobertura municipal verificada.

Não confundir fontes públicas de contexto turístico com indicadores operacionais reais de hotéis.

### Open-Meteo (MVP 0.2)
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Campos diários: `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `time`
- Fuso: `America/Sao_Paulo`; horizonte: 7 dias; cache de 1 hora.
- Coordenadas aproximadas dos centros de Taubaté e Tremembé; não identificam hotéis.
- Previsões meteorológicas sujeitas a alteração. Conferir licença e limites antes do uso comercial.


## SIDRA (MVP 0.5)
- `https://apisidra.ibge.gov.br/values/t/6579/n6/3554102,3554805/v/9324/p/last%203` — estimativas populacionais.
- `https://apisidra.ibge.gov.br/values/t/5938/n6/3554102,3554805/v/37/p/last%203` — PIB municipal, mil reais correntes.
- Formato: linha inicial de metadados (`V`, `D1C`, `D2C`, `D3C`), demais linhas dados. A disponibilidade de anos depende das séries publicadas.
