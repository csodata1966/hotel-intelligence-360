from datetime import datetime, timezone, timedelta
from src.ingestion.sidra import consultar_indicador,processar_resposta
from src.storage.market_store import salvar_indicadores,consultar_mercado

def resposta(valor='125000'):
    return [{'V':'Valor'}, {'D1C':'3554102','D2C':'9324','D3C':'2025','V':valor},
            {'D1C':'3554805','D2C':'9324','D3C':'2025','V':'50000'},
            {'D1C':'3554805','D2C':'999','D3C':'2025','V':'999'}]

def test_parser_valida_variavel_e_municipio():
    r=processar_resposta(resposta(),'populacao_estimada')
    assert len(r)==2 and {x.municipio for x in r}=={'Taubaté','Tremembé'}

def test_valores_ausentes_nao_inventados():
    assert len(processar_resposta(resposta('...'),'populacao_estimada'))==1

def test_endpoint_autenticacao_nao_necessaria():
    class Resp:
        def raise_for_status(self): pass
        def json(self): return resposta()
    class Client:
        def get(self,url,timeout):
            assert '/t/6579/n6/3554102,3554805/v/9324/' in url
            return Resp()
    assert len(consultar_indicador('populacao_estimada',Client()))==2

def test_persistencia_e_utc(tmp_path):
    dados=processar_resposta(resposta(),'populacao_estimada')
    salvar_indicadores('populacao_estimada',dados,tmp_path,
                      datetime(2026,10,27,15,tzinfo=timezone(timedelta(hours=-3))))
    assert len(list((tmp_path/'bronze'/'mercado'/'populacao_estimada').glob('*.json')))==1
    assert len(list((tmp_path/'silver'/'mercado'/'populacao_estimada').glob('*.parquet')))==1
    df=consultar_mercado(tmp_path)
    assert len(df)==2
    assert '18:00:00+00:00' in str(df.iloc[0]['coletado_em_utc'])

def test_gold_mais_recente(tmp_path):
    dados=processar_resposta(resposta(),'populacao_estimada')
    salvar_indicadores('populacao_estimada',dados,tmp_path,datetime(2026,10,27,15,tzinfo=timezone.utc))
    depois=processar_resposta(resposta('145000'),'populacao_estimada')
    salvar_indicadores('populacao_estimada',depois,tmp_path,datetime(2026,10,27,16,tzinfo=timezone.utc))
    df=consultar_mercado(tmp_path)
    assert len(df)==2
    assert df.loc[df['municipio']=='Taubaté','valor'].iloc[0]==145000
