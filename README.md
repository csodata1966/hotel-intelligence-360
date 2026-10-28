# Hotel Intelligence 360 | Portfolio Edition v1.0.0

Projeto demonstrativo de **Engenharia de Dados, Business Intelligence e análise de mercado para hotelaria**, desenvolvido para o [Universo Dados](https://universodados.com.br).

**Repositório:** https://github.com/csodata1966/hotel-intelligence-360

## O que demonstra

- Integração com fontes públicas: **IBGE/SIDRA**, **Open-Meteo** e **BrasilAPI**.
- Pipeline local Bronze (JSON) → Silver (Parquet) → Gold (DuckDB/Parquet).
- Aplicação Streamlit com cinco abas: Visão Executiva, Clima e Histórico, Calendário, Mercado Regional e Simulador.
- Comparação de indicadores de Taubaté e Tremembé preservando o ano de referência.
- Simulação de capacidade, ocupação, ADR, RevPAR e cenários de receita de hospedagem.
- Snapshots de referência em `data/reference` para a aplicação permanecer útil quando uma API estiver indisponível.
- Testes automatizados com pytest e CI no GitHub Actions.

## Uso e limitações

**Os valores de ocupação, diária média e receitas são simulações matemáticas, não dados reais de hotéis.** Informações de população e PIB são indicadores de contexto regional, não estimativas de demanda turística. Valores de PIB estão em preços correntes, sem correção pela inflação.

A aplicação usa fontes públicas com períodos e horários de atualização diferentes. Os snapshots de contingência são históricos e identificados por sua data de coleta. A previsão meteorológica antiga não é apresentada como atual.

A persistência Bronze/Silver/Gold funciona localmente. No Streamlit Community Cloud, o disco pode ser descartado durante reinicializações: **não há histórico Cloud durável**. A Visão Executiva apresenta indicadores a partir dos snapshots quando não há Gold local. A versão de portfólio não exige R2, S3 ou serviços pagos adicionais.

O serviço gratuito e as APIs de terceiros têm termos, franquias e limites próprios; uso comercial futuro requer reavaliação dessas condições.

## Executar localmente (Windows PowerShell)

```powershell
cd D:\Projetos\hotel-intelligence-360
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

## Estrutura

- `app/main.py`: interface Streamlit.
- `src/ingestion/`: conectores das APIs.
- `src/storage/`: persistência Bronze/Silver/Gold local.
- `src/portfolio_summary.py`: síntese executiva com prioridade Gold e fallback documentado.
- `src/analytics_hotel.py`: métricas de negócio e cenários.
- `src/fallback_data.py`: leitura de snapshots públicos versionados.
- `data/reference/`: dados históricos de contingência, sem dados pessoais.
- `tests/`: verificações automatizadas.
- `docs/`: arquitetura, fontes e dicionário de dados.

## Dados e créditos

Fontes: [IBGE](https://www.ibge.gov.br/), [SIDRA](https://sidra.ibge.gov.br/), [Open-Meteo](https://open-meteo.com/) e [BrasilAPI](https://brasilapi.com.br/). Consulte as condições de uso antes de reutilização em produção.

## Evolução

- `v0.5.0`: integração de indicadores regionais e marco inicial no Git.
- `v0.6.1`: dashboard executivo e simulações aprimoradas.
- `v0.6.2`: snapshots de contingência e maior tolerância a falhas.
- `v1.0.0`: edição final de portfólio, painel executivo resiliente e documentação consolidada.

## Próximos passos opcionais

Este projeto está concluído como **demonstração**. Persistência Cloud durável, autenticação empresarial e integração com sistemas reais de hotelaria são possíveis extensões futuras, fora do escopo desta edição.
