# Dicionário de dados — MVP 0.1

| Campo | Tipo | Origem | Descrição |
|---|---|---|---|
| codigo_ibge | int | IBGE | Identificador de sete dígitos do município |
| nome | str | IBGE | Nome do município |
| uf | str | IBGE | Sigla da UF |
| regiao_imediata | str/null | IBGE | Região geográfica imediata |
| quartos | int | Usuário (hipotético) | Número de quartos disponíveis por dia |
| dias | int | Usuário (hipotético) | Dias de operação no período |
| ocupacao | percentual | Usuário (hipotético) | Percentual médio de diárias ocupadas |
| adr | BRL | Usuário (hipotético) | Receita média por diária vendida assumida |
| diarias_disponiveis | número | Cálculo | quartos × dias |
| diarias_vendidas_equivalentes | número | Cálculo | diarias_disponiveis × ocupacao / 100 |
| receita_hospedagem | BRL | Cálculo | diarias_vendidas_equivalentes × adr |
| revpar | BRL | Cálculo | receita_hospedagem / diarias_disponiveis |

Nota: as diárias equivalentes podem ser fracionárias em simulação agregada. Isso não significa vender uma fração de quarto em operação real.

## Previsão meteorológica (MVP 0.2)
| Campo | Tipo | Unidade | Fonte |
|---|---|---|---|
| Dia | data ISO | dia local | Open-Meteo `daily.time` |
| Máxima | float | °C | Open-Meteo `daily.temperature_2m_max` |
| Mínima | float | °C | Open-Meteo `daily.temperature_2m_min` |
| Chuva | float | mm/dia | Open-Meteo `daily.precipitation_sum` |

Todos são valores **previstos**, sujeitos a revisões dos modelos.

### Calendário BrasilAPI — MVP 0.4

| Coluna | Tipo | Definição |
|---|---|---|
| ano | inteiro | Ano solicitado à API |
| dia | date | Data retornada pela BrasilAPI |
| nome | texto | Nome da data |
| tipo | texto | Classificação informada pela BrasilAPI; não verificação legal |
| coletado_em_utc | timestamp timezone UTC | Instante de ingestão normalizado para UTC |
| coleta_id | texto | Identificador de snapshot |

Gold: seleção da coleta mais recente por `(ano, dia, nome)`. O campo `chuva prevista` na interface só aparece quando há correspondência com os próximos 7 dias da Open-Meteo. Um calendário não equivale a ocupação real de hotéis.
