# Arquitetura — Hotel Intelligence 360

## Objetivo
Criar um produto demonstrativo reprodutível que una informações públicas, indicadores de mercado e simulações hoteleiras sem apresentar cenários hipotéticos como fatos.

## Camadas
1. **Origem**: API IBGE (MVP 0.1); futuramente BrasilAPI, Open-Meteo e IBGE/SIDRA.
2. **Ingestão**: HTTPX com timeout, checagem de código HTTP e validação de campos essenciais.
3. **Exposição**: Streamlit com cache diário de município.
4. **Simulação**: cálculo determinístico de diárias disponíveis, receita e RevPAR.
5. **Futuro**: arquivos Parquet, DuckDB, validação de esquemas, CI e deploy.

## Requisitos não funcionais
- Sem dados pessoais de hóspedes.
- Interface avisa quando conteúdo é simulado.
- API indisponível não causa parada geral do painel.
- Testes de ingestão independentes de acesso à internet (mock HTTP).
- API pública sujeita a disponibilidade e regras de uso.

## Escopo inicial
Taubaté (3554102) e Tremembé (3554805); demais cidades virão após o MVP.

## Implantação
App Streamlit público em hospedagem compatível com o uso e limites dos provedores; WordPress apresenta o projeto e fornece acesso à demonstração.

## Atualização MVP 0.2

`src/ingestion/open_meteo.py` consulta a previsão diária, valida os arrays e transforma os resultados em `PrevisaoDiaria`. O dashboard armazena temporariamente o retorno com `st.cache_data(ttl=3600)` e apresenta gráficos/tabelas. A falha desse serviço não interrompe o simulador existente. Persistência Parquet e DuckDB é uma fase futura.

## MVP 0.3: camadas locais

Ao clicar em **Salvar snapshot**, o conector Open-Meteo entrega uma previsão diária validada.
O pipeline gera uma cópia Bronze JSON, uma cópia Silver Parquet e recompõe Gold Parquet
via DuckDB (janela SQL `row_number` por município/dia ordenada por coleta).
A interface consulta Gold por SQL e permite exportar CSV. O caminho é local e não é
storage persistente de produção. Conexões SQL são transitórias; não há servidor DuckDB.
