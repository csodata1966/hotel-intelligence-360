
"""Hotel Intelligence 360 — Portfolio Edition v1.0.0."""

# ============================================================
# CONFIGURAÇÃO DE CAMINHOS — STREAMLIT CLOUD E AMBIENTE LOCAL
# ============================================================

import sys
from pathlib import Path

# Identifica automaticamente a pasta raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

# Adiciona a raiz ao caminho de importação do Python
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ============================================================
# BIBLIOTECAS EXTERNAS
# ============================================================

import streamlit as st
import httpx
import pandas as pd
import plotly.express as px


# ============================================================
# BIBLIOTECAS PADRÃO DO PYTHON
# ============================================================

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# MÓDULOS INTERNOS — HOTEL INTELLIGENCE 360
# ============================================================

# Indicadores e simulação hoteleira
from src.analytics_hotel import (
    calcular_indicadores,
    calcular_cenarios,
    formatar_brl,
)

# Dados meteorológicos
from src.ingestion.open_meteo import obter_previsao

# Municípios do IBGE
from src.ingestion.ibge import MUNICIPIOS, obter_municipio

# Calendário de feriados
from src.ingestion.brasilapi import obter_feriados
from src.analytics_holidays import classificar_data
from src.fallback_data import carregar_mercado, carregar_feriados

# Persistência meteorológica
from src.storage.weather_store import (
    salvar_coleta,
    consultar_gold,
    total_coletas,
)

# Persistência de feriados
from src.storage.holiday_store import (
    salvar_feriados,
    consultar_feriados_gold,
    total_coletas_feriados,
)


st.set_page_config(page_title="Hotel Intelligence 360", page_icon="🏨", layout="wide")
st.title("Hotel Intelligence 360")
st.caption("v1.0.0 — Portfolio Edition | dados públicos + cenários hipotéticos")


# ============================================================
# SELEÇÃO DE MUNICÍPIO — METADADOS LOCAIS DO IBGE
# ============================================================

# Códigos oficiais e estáveis dos municípios
# Não é necessária uma consulta HTTP para obter esses códigos.
MUNICIPIOS_REFERENCIA = {
    "Taubaté": {
        "codigo": 3554102,
        "uf": "SP",
    },
    "Tremembé": {
        "codigo": 3554805,
        "uf": "SP",
    },
}

nome = st.sidebar.selectbox(
    "Município de referência",
    list(MUNICIPIOS_REFERENCIA.keys())
)

municipio = MUNICIPIOS_REFERENCIA[nome]

st.sidebar.success(
    f"Município: {nome} ({municipio['uf']})"
)

st.sidebar.caption(
    f"Código IBGE: {municipio['codigo']}"
)

st.sidebar.caption(
    "Identificação municipal: códigos oficiais do IBGE."
)

st.sidebar.markdown("---")
st.sidebar.caption("Hotel Intelligence 360 · v1.0.0 | Dados públicos e simulações identificadas")
aba_resumo, aba_clima, aba_calendario, aba_mercado, aba_simulador = st.tabs([
    "Visão executiva", "Clima e histórico", "Calendário", "Mercado regional", "Simulador"
])
with aba_clima:
    st.subheader("Previsão meteorológica — próximos 7 dias")
    st.caption("Dados de previsão, não observações históricas. Coordenadas aproximadas do centro municipal.")

    @st.cache_data(ttl=3600, show_spinner=False)
    def previsao_cached(cidade: str):
        return obter_previsao(cidade)

    previsao = None
    try:
        previsao = previsao_cached(nome)
        frame = pd.DataFrame([
            {"Dia": item.dia, "Máxima (°C)": item.temp_max_c,
             "Mínima (°C)": item.temp_min_c, "Chuva (mm)": item.chuva_mm}
            for item in previsao
        ])
        um, dois, tres = st.columns(3)
        um.metric("Máxima prevista hoje", f"{previsao[0].temp_max_c:.1f} °C")
        dois.metric("Mínima prevista hoje", f"{previsao[0].temp_min_c:.1f} °C")
        tres.metric("Chuva acumulada prevista (7 dias)", f"{frame['Chuva (mm)'].sum():.1f} mm")
        st.markdown("**Temperaturas previstas (°C)**")
        grafico_t = frame.copy()
        grafico_t["Dia"] = grafico_t["Dia"].astype(str)
        fig_t = px.line(grafico_t, x="Dia", y=["Máxima (°C)", "Mínima (°C)"], markers=True)
        fig_t.update_layout(xaxis_title="Data", yaxis_title="Temperatura (°C)", legend_title="Série")
        st.plotly_chart(fig_t, use_container_width=True)
        st.markdown("**Precipitação prevista (mm/dia)**")
        fig_c = px.bar(grafico_t, x="Dia", y="Chuva (mm)")
        fig_c.update_layout(xaxis_title="Data", yaxis_title="Precipitação (mm)")
        st.plotly_chart(fig_c, use_container_width=True)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.markdown("#### Histórico local e Engenharia de Dados")
        st.caption("Coletas são snapshots de **previsões**, não registros do clima observado. "
                   "Bronze: JSON | Silver: Parquet | Gold: Parquet consultado com DuckDB.")
        dados_dir = Path(__file__).resolve().parents[1] / "data" / "warehouse"
        if st.button("Salvar snapshot da previsão no histórico local", key=f"salvar_{nome}"):
            try:
                identificador = salvar_coleta(nome, previsao, dados_dir)
                st.success(f"Coleta registrada: {identificador}")
            except (OSError, ValueError, RuntimeError) as erro:
                st.error(f"Não foi possível gravar a coleta ({type(erro).__name__}).")
        st.caption(f"Snapshots salvos de {nome}: {total_coletas(dados_dir, nome)}")
        try:
            historico = consultar_gold(dados_dir, nome)
            if not historico.empty:
                st.dataframe(historico, use_container_width=True, hide_index=True)
                st.download_button("Exportar previsão consolidada (CSV)",
                    historico.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"previsao_{nome.lower()}.csv", mime="text/csv")
        except (OSError, RuntimeError) as erro:
            st.warning(f"Histórico local indisponível ({type(erro).__name__}).")
        st.caption(
            "Fonte: Open-Meteo (open-meteo.com) | Modelo meteorológico, "
            "com atualização de cache a cada 60 minutos. "
            "Página carregada em: "
            + datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M (Brasília)")
            + ". Horário de carregamento não é horário de execução do modelo."
        )
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        st.warning("Previsão meteorológica indisponível no momento. O simulador segue funcionando.")
        st.caption(f"Detalhe técnico: {type(exc).__name__}")

with aba_calendario:
    st.subheader("Calendário inteligente — feriados e clima")
    st.caption("Tipo original preservado; classificação legal conservadora (fonte federal 2026). "
               "Não inclui automaticamente feriados municipais. Não representa previsão de ocupação.")

    @st.cache_data(ttl=86400, show_spinner=False)
    def feriados_cached(ano: int):
        return obter_feriados(ano)

    hoje_local = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    anos = [hoje_local.year, hoje_local.year + 1]
    ano_escolhido = st.selectbox("Ano do calendário", anos)
    warehouse = Path(__file__).resolve().parents[1] / "data" / "warehouse"
    try:
        feriados = feriados_cached(ano_escolhido)
        linhas_feriados = []
        for feriado in feriados:
            diferenca = (feriado.dia - hoje_local).days
            dia_semana = feriado.dia.weekday()
            ponte = dia_semana in (0, 4)
            chuva = next((p.chuva_mm for p in previsao if p.dia == feriado.dia), None) if previsao is not None else None
            linhas_feriados.append({
                "Data": feriado.dia.strftime("%d/%m/%Y"), "Feriado/data": feriado.nome,
                "Tipo da API": feriado.tipo, "Classificação verificada": classificar_data(feriado.dia, feriado.nome, feriado.tipo)[0], "Dia da semana": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][dia_semana],
                "Dias até a data": diferenca, "Próximo/hoje": diferenca >= 0,
                "Próximo ao fim de semana": ponte,
                "Chuva prevista (mm)": chuva,
            })
        feriados_frame = pd.DataFrame(linhas_feriados)
        proximos = [f for f in feriados if f.dia >= hoje_local]
        m1, m2, m3 = st.columns(3)
        m1.metric("Datas retornadas pela API", len(feriados))
        m2.metric("Datas restantes no ano", len(proximos))
        m3.metric("Próxima data", proximos[0].dia.strftime("%d/%m/%Y") if proximos else "Nenhuma")
        st.dataframe(feriados_frame, use_container_width=True, hide_index=True)
        st.caption('Atenção: a classificação federal não substitui consulta à legislação municipal/estadual; para 2027 datas não confirmadas permanecem A verificar.')
        st.caption("'Próximo ao fim de semana' indica segunda ou sexta-feira; "
                   "não confirma feriado prolongado em todos os estabelecimentos. "
                   "Clima aparece somente se a data estiver nos sete dias de previsão.")
        if st.button("Salvar calendário no histórico Bronze/Silver/Gold"):
            try:
                cid = salvar_feriados(ano_escolhido, feriados, warehouse)
                st.success(f"Coleta de calendário salva: {cid}")
            except Exception as exc:
                st.error(f"Falha ao persistir o calendário: {type(exc).__name__}: {exc}")
        st.caption(f"Coletas de calendário gravadas para {ano_escolhido}: "
                   f"{total_coletas_feriados(warehouse, ano_escolhido)}")
        persistidos = consultar_feriados_gold(warehouse, ano_escolhido)
        if not persistidos.empty:
            st.download_button("Exportar feriados consolidados (CSV)",
                               persistidos.to_csv(index=False).encode('utf-8-sig'),
                               file_name=f"feriados_{ano_escolhido}.csv", mime="text/csv")
    except (httpx.HTTPError, ValueError, KeyError, TypeError, OSError, RuntimeError) as exc:
        contingencia = carregar_feriados(ROOT_DIR, ano_escolhido)
        if contingencia:
            st.warning("BrasilAPI indisponível. Exibindo snapshot histórico de referência (não atualizado).")
            st.caption(f"Fonte: BrasilAPI | Coleta original UTC: {contingencia.coletado_em_utc} | Falha: {type(exc).__name__}")
            st.dataframe(pd.DataFrame(contingencia.registros), hide_index=True, use_container_width=True)
        else:
            st.warning("Calendário indisponível e sem snapshot histórico de referência para este ano.")
            st.caption(f"Detalhe técnico: {type(exc).__name__}")

with aba_mercado:
    st.subheader("Inteligência de mercado — IBGE/SIDRA")
    st.caption("População estimada e PIB municipal, com anos de referência próprios. Não são dados de reservas ou ocupação hoteleira.")
    from src.ingestion.sidra import consultar_indicador, FONTES
    from src.storage.market_store import salvar_indicadores, consultar_mercado
    @st.cache_data(ttl=86400, show_spinner=False)
    def mercado_cached(chave):
        return consultar_indicador(chave)
    indicadores = []
    indicador_selecionado=st.selectbox("Indicador regional", list(FONTES),
        format_func=lambda x: {"populacao_estimada":"População estimada", "pib_municipal":"PIB municipal"}[x])
    try:
        indicadores = mercado_cached(indicador_selecionado)
        if indicadores:
            df_mercado = pd.DataFrame([{
                "Município":x.municipio,"Ano":x.ano,"Valor":x.valor,"Unidade":x.unidade,"Fonte":x.fonte
            } for x in indicadores])
            st.dataframe(df_mercado,hide_index=True,use_container_width=True)
            fig=px.line(df_mercado,x="Ano",y="Valor",color="Município",markers=True,
                        title="Comparativo por ano de referência")
            fig.update_xaxes(type="category")
            st.plotly_chart(fig,use_container_width=True)
            st.caption("Fonte: IBGE/SIDRA | Dados públicos sujeitos a revisão. PIB em mil reais correntes, sem ajuste de inflação.")
            if st.button("Salvar indicador no histórico Bronze/Silver/Gold"):
                cid=salvar_indicadores(indicador_selecionado,indicadores,warehouse)
                st.success(f"Indicadores armazenados: {cid}")
        else:
            st.info("A API não retornou valores válidos para o indicador e os municípios selecionados.")
    except (httpx.HTTPError,ValueError,TypeError,KeyError,OSError,RuntimeError) as erro:
        contingencia = carregar_mercado(ROOT_DIR, indicador_selecionado)
        if contingencia:
            st.warning("SIDRA indisponível. Exibindo dados oficiais de uma coleta anterior, não atualizados.")
            st.caption(f"Coleta original UTC: {contingencia.coletado_em_utc} | Fonte indicada no CSV: IBGE/SIDRA | Falha: {type(erro).__name__}")
            df_fallback = pd.DataFrame(contingencia.registros)
            st.dataframe(df_fallback, hide_index=True, use_container_width=True)
            fig_fallback = px.line(df_fallback, x="ano", y="valor", color="municipio", markers=True,
                                   title="Indicador regional — snapshot anterior")
            fig_fallback.update_xaxes(type="category")
            st.plotly_chart(fig_fallback, use_container_width=True)
        else:
            st.warning("Indicadores regionais indisponíveis e sem cópia de contingência.")
            st.caption(f"Detalhe técnico: {type(erro).__name__}")
    try:
        historico_mercado=consultar_mercado(warehouse)
        if not historico_mercado.empty:
            st.markdown("**Histórico consolidado (Gold)**")
            st.dataframe(historico_mercado,use_container_width=True,hide_index=True)
            st.download_button("Exportar indicadores IBGE (CSV)",
                historico_mercado.to_csv(index=False).encode("utf-8-sig"),
                file_name="indicadores_regionais.csv",mime="text/csv")
    except (OSError,RuntimeError) as erro:
        st.warning(f"Histórico regional indisponível: {type(erro).__name__}")

with aba_simulador:
    st.subheader("Simulador de hospedagem")
    st.info("Todos os valores deste módulo são hipotéticos e não representam hotéis reais.")
    st.caption("Altere um parâmetro por vez e observe a atualização automática dos indicadores e dos cenários.")

    col_input1, col_input2 = st.columns(2)
    with col_input1:
        quartos = st.slider("Quantidade de quartos", 5, 200, 40, 5, key="sim_quartos")
        ocupacao = st.slider("Taxa de ocupação estimada (%)", 0, 100, 65, 5, key="sim_ocupacao")
    with col_input2:
        adr = st.number_input("Diária média (ADR) em R$", min_value=0.0, value=250.0, step=10.0, key="sim_adr")
        dias = st.slider("Dias no período", 1, 31, 30, key="sim_dias")

    indicadores = calcular_indicadores(quartos, dias, ocupacao, adr)
    st.markdown("#### Capacidade e ocupação")
    k1, k2, k3 = st.columns(3)
    k1.metric("Diárias disponíveis", f"{indicadores.diarias_disponiveis:,}".replace(",", "."))
    k2.metric("Diárias ocupadas estimadas", f"{indicadores.diarias_ocupadas:,.0f}".replace(",", "."))
    k3.metric("Taxa de ocupação", f"{ocupacao}%")
    st.caption("Diárias disponíveis = quartos × dias. Diárias ocupadas equivalentes = diárias disponíveis × ocupação média; podem ser fracionárias por se tratar de uma média simulada.")

    st.markdown("#### Indicadores financeiros")
    c1, c2, c3 = st.columns(3)
    c1.metric("Receita estimada de hospedagem", formatar_brl(indicadores.receita))
    c2.metric("ADR — diária média", formatar_brl(indicadores.adr))
    c3.metric("RevPAR — receita por diária disponível", formatar_brl(indicadores.revpar))
    st.caption("Receita = diárias ocupadas equivalentes × ADR. RevPAR = receita ÷ diárias disponíveis = ADR × ocupação.")

    st.markdown("#### Comparação de cenários")
    st.caption("Cenários didáticos: conservador (ocupação −10 pontos percentuais), base (ocupação informada) e otimista (+10 pontos percentuais); valores limitados a 0%–100%. Mantêm quartos, dias e ADR iguais.")
    cenarios = calcular_cenarios(quartos, dias, ocupacao, adr)
    df_cenarios = pd.DataFrame([{
        "Cenário": c.nome,
        "Ocupação (%)": c.ocupacao,
        "Diárias ocupadas": round(c.indicadores.diarias_ocupadas, 2),
        "Receita (R$)": c.indicadores.receita,
        "RevPAR (R$)": c.indicadores.revpar,
    } for c in cenarios])
    fig_cenarios = px.bar(df_cenarios, x="Cenário", y="Receita (R$)", text_auto=".2f", title="Receita simulada por cenário")
    fig_cenarios.update_layout(yaxis_title="Receita de hospedagem (R$)", xaxis_title=None)
    st.plotly_chart(fig_cenarios, use_container_width=True)
    tabela_cenarios = df_cenarios.copy()
    tabela_cenarios["Receita (R$)"] = tabela_cenarios["Receita (R$)"].map(formatar_brl)
    tabela_cenarios["RevPAR (R$)"] = tabela_cenarios["RevPAR (R$)"].map(formatar_brl)
    st.dataframe(tabela_cenarios, hide_index=True, use_container_width=True)
    st.download_button("Exportar cenários (CSV)", data=df_cenarios.to_csv(index=False, sep=";").encode("utf-8-sig"), file_name="simulacao_hoteleira_cenarios.csv", mime="text/csv")
    st.caption("Exercício matemático simplificado: não considera custos, impostos, cancelamentos, receitas adicionais ou variações diárias. Não representa previsão de demanda ou faturamento real.")

with aba_resumo:
    st.subheader("Visão executiva")
    st.caption("Contexto regional para decisões hoteleiras. A aplicação não apresenta reservas ou faturamento reais de hotéis.")
    try:
        resumo_previsao = previsao_cached(nome)
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        resumo_previsao = []
    try:
        resumo_feriados = feriados_cached(datetime.now(ZoneInfo("America/Sao_Paulo")).year)
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        resumo_feriados = []
    proximas_datas = sorted((f for f in resumo_feriados if f.dia >= hoje_local), key=lambda f: f.dia)
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Cidade selecionada", nome)
    q2.metric("Previsão: máxima 1º dia", f"{resumo_previsao[0].temp_max_c:.1f} °C" if resumo_previsao else "Indisponível")
    q3.metric("Chuva prevista em 7 dias", f"{sum(p.chuva_mm for p in resumo_previsao):.1f} mm" if resumo_previsao else "Indisponível")
    q4.metric("Próxima data do calendário", proximas_datas[0].dia.strftime("%d/%m/%Y") if proximas_datas else "Indisponível")
    st.caption("Previsões meteorológicas: Open-Meteo; calendário: BrasilAPI. As datas podem não ser feriados municipais/estaduais.")
    st.markdown("#### Panorama econômico e demográfico")
    from src.portfolio_summary import preparar_resumo_regional
    try:
        gold_resumo = consultar_mercado(warehouse)
    except (OSError, RuntimeError, ValueError, KeyError):
        gold_resumo = pd.DataFrame()

    for chave, titulo in [
        ("populacao_estimada", "População estimada"),
        ("pib_municipal", "PIB municipal"),
    ]:
        referencia = carregar_mercado(ROOT_DIR, chave)
        tabela, proveniencia, coleta = preparar_resumo_regional(
            gold_resumo,
            chave,
            referencia.registros if referencia else [],
            referencia.coletado_em_utc if referencia else None,
        )
        if tabela.empty:
            st.info(f"{titulo}: nenhum dado público de referência disponível.")
            continue
        ano = int(tabela["ano"].max())
        st.markdown(f"**{titulo} — {ano}**")
        st.caption(f"Origem: {proveniencia}. Última coleta: {coleta}.")
        exibir = tabela[["municipio", "ano", "valor", "unidade", "fonte"]].copy()
        if chave == "populacao_estimada":
            exibir["valor"] = exibir["valor"].map(
                lambda x: f"{x:,.0f}".replace(",", ".")
            )
        else:
            # SIDRA 5938: PIB publicado em milhares de reais correntes.
            exibir["valor"] = exibir["valor"].map(
                lambda x: f"R$ {x / 1_000_000:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            exibir["unidade"] = "bilhões de R$ correntes"
        exibir.columns = ["Município", "Ano", "Valor", "Unidade", "Fonte"]
        st.dataframe(exibir, hide_index=True, use_container_width=True)
    st.markdown("#### Interpretação gerencial")
    st.write("Compare o ambiente econômico das cidades, observe feriados e condições meteorológicas e use a aba Simulador para testar cenários. O painel não estima demanda nem prevê ocupação real.")
    st.caption("Proveniência: IBGE/SIDRA (anos específicos), Open-Meteo (previsão) e BrasilAPI (datas). Dados de coleta local podem estar desatualizados; consulte as abas específicas.")

