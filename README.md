# Hotel Intelligence 360

Demonstração de engenharia de dados, Business Intelligence e simulação de indicadores hoteleiros, destinada ao portfólio [Universo Dados](https://universodados.com.br).

## Status
MVP 0.1: consulta em tempo real à API oficial de localidades do IBGE, seleção Taubaté/Tremembé e simulador hipotético de receita, ADR e RevPAR.

## Instalação
Requer Python 3.11 ou superior.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app/main.py
```

## Testes
```bash
python -m pytest -q
python -m ruff check .
```

## Atenção à interpretação dos dados
As informações municipais são reais (fonte IBGE). Ocupação, receita, ADR e RevPAR são calculados a partir de parâmetros informados pelo usuário e **não são dados observados de hotéis reais**. Valores representam receita bruta estimada de hospedagem, não lucro.

## Próximas etapas
- Integração Open-Meteo e BrasilAPI
- Exportação e persistência analítica DuckDB/Parquet
- Dashboard por cidade e calendário
- CI e implantação de demonstração

Documentos: [arquitetura](docs/architecture.md) · [dicionário de dados](docs/data_dictionary.md) · [fontes](docs/api_sources.md).

## MVP 0.2 — Previsão do tempo

- Integração com a Open-Meteo para Taubaté e Tremembé usando coordenadas aproximadas dos centros urbanos.
- Temperaturas máximas/mínimas e precipitação previstas por sete dias, gráficos e tabela.
- Cache Streamlit de uma hora, tratamento de respostas inválidas e indisponibilidade da API.
- Dados meteorológicos são **previsões**, não medições de estações locais; não estimam ocupação de hotéis.

Atualize as dependências com `python -m pip install -r requirements.txt`, rode `python -m pytest -q` e inicie `python -m streamlit run app/main.py`.

Fonte: [Open-Meteo Weather Forecast API](https://open-meteo.com/en/docs). Verifique condições de uso antes de qualquer operação comercial.

## MVP 0.3 — persistência analítica

O painel de clima permite salvar manualmente um **snapshot** da previsão consultada.
As camadas locais ficam em `data/warehouse/` (ignorada pelo Git):

- `bronze/<cidade>/<id>.json`: resposta normalizada do conector e metadados da coleta.
- `silver/<cidade>/<id>.parquet`: séries tipadas por município e data prevista.
- `gold/previsao_atual.parquet`: a coleta mais recente por cidade e dia, materializada por DuckDB.

**Importante:** o histórico contém versões de previsões obtidas, não medições do clima real.
No Streamlit Community Cloud os arquivos locais podem desaparecer em reinicializações;
para persistência durável, usar armazenamento externo em versão futura. Não versionar dados locais de execução.

Após instalar a versão nova, execute `python -m pip install -r requirements.txt`
e `python -m pytest -q`, então `python -m streamlit run app/main.py`.

## MVP 0.4 — Calendário Inteligente

A BrasilAPI fornece datas e categorias publicadas para 2026 e 2027 (ou o ano atual e seguinte), mostradas no painel juntamente com as previsões da Open-Meteo quando há coincidência de datas. As datas de calendário **não** são indicadores observados de demanda turística: o painel não calcula previsão de ocupação com base em feriados.

O botão de persistência cria camadas separadas para feriados: `data/warehouse/bronze/feriados/{ano}/*.json`, `silver/feriados/{ano}/*.parquet`, `gold/feriados_atuais.parquet`. Os snapshots são opcionais e explícitos; no Streamlit Community Cloud, disco local pode ser temporário. Timestamp `coletado_em_utc` é timezone-aware UTC e é convertido para Brasília apenas na interface.

**Fontes/limitações:** API em `https://brasilapi.com.br/api/feriados/v1/{ano}`. A BrasilAPI pode classificar pontos facultativos como nacionais; confira as regras oficiais para decidir a situação jurídica. Feriados municipais não são garantidos. Condições de utilização podem mudar.

### MVP 0.4.2 — qualidade do calendário

- Mantém `tipo` original da BrasilAPI em Bronze/Silver/Gold.
- Adiciona `classificacao` e `referencia_classificacao` em Silver e Gold.
- Corrige categorização de Carnaval, Corpus Christi e Páscoa para 2026, conforme calendário federal da Portaria MGI 11.460/2025.
- Para outras datas sem validação normativa explícita, registra **A verificar**. A classificação federal não determina feriado municipal ou estadual.
- Reconstrói a Gold ao salvar nova coleta, incluindo Silver existente; sem apagar arquivos históricos.

Referência: https://www.gov.br/gestao/pt-br/assuntos/noticias/2025/dezembro/confira-o-calendario-oficial-de-feriados-nacionais-e-pontos-facultativos-em-2026


### Compatibilidade MVP 0.4.3
A consulta da camada Gold reconhece arquivos legados sem colunas de classificação e reconstrói a Gold a partir da Silver (ou migra o próprio arquivo Gold quando não houver Silver), preservando o histórico Bronze. Faça backup dos dados antes de atualizar.


## MVP 0.5 — inteligência regional
- IBGE/SIDRA: população estimada (tabela 6579/variável 9324), PIB municipal (5938/37).
- Séries anuais reais disponibilizadas pela API para Taubaté e Tremembé.
- Bronze JSON / Silver Parquet / Gold DuckDB e exportação CSV.
- O PIB é expresso em **mil reais correntes** e não deve ser comparado entre anos como crescimento real sem deflacionamento.
- Ausência de dados na API não gera valores inventados.
- Ao atualizar, preserve a pasta `data/warehouse` e o ambiente `.venv`.
