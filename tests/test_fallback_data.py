from pathlib import Path
from src.fallback_data import carregar_mercado, carregar_feriados


def _csv(p, conteudo):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(conteudo, encoding='utf-8')


def test_mercado_fallback(tmp_path):
    _csv(tmp_path/'data/reference/indicadores_regionais.csv',
         'municipio,codigo_ibge,indicador,ano,valor,unidade,fonte,coletado_em_utc\nTaubaté,3554102,populacao_estimada,2026,323380,pessoas,IBGE,2026-10-27T18:00:00+00:00\n')
    snap=carregar_mercado(tmp_path,'populacao_estimada')
    assert snap is not None and snap.registros[0]['valor']==323380
    assert carregar_mercado(tmp_path,'pib_municipal') is None


def test_calendario_fallback(tmp_path):
    _csv(tmp_path/'data/reference/feriados_2026.csv',
         'dia,nome,tipo,classificacao,referencia_classificacao,coletado_em_utc\n2026-12-25,Natal,national,Feriado nacional,Legislação,2026-10-27T18:00:00+00:00\n')
    snap=carregar_feriados(tmp_path,2026)
    assert snap.registros[0]['classificacao']=='Feriado nacional'
    assert carregar_feriados(tmp_path,2028) is None


def test_ausencia_de_arquivo(tmp_path):
    assert carregar_feriados(tmp_path,2026) is None
    assert carregar_mercado(tmp_path,'pib_municipal') is None


def test_schema_invalido(tmp_path):
    _csv(tmp_path/'data/reference/indicadores_regionais.csv','x,y\n1,2\n')
    assert carregar_mercado(tmp_path,'populacao_estimada') is None
