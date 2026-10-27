from datetime import date,datetime,timedelta,timezone
from src.ingestion.brasilapi import Feriado
from src.storage.holiday_store import salvar_feriados, consultar_feriados_gold, total_coletas_feriados

def test_camadas_feriados(tmp_path):
    f=[Feriado(date(2026,12,25),'Natal','national')]
    salvar_feriados(2026,f,tmp_path,datetime(2026,10,27,15,tzinfo=timezone(timedelta(hours=-3))))
    assert len(list((tmp_path/'bronze'/'feriados'/'2026').glob('*.json')))==1
    assert len(list((tmp_path/'silver'/'feriados'/'2026').glob('*.parquet')))==1
    tabela=consultar_feriados_gold(tmp_path,2026)
    assert len(tabela)==1
    assert tabela.iloc[0]['coletado_em_utc'].hour == 18
    assert tabela.iloc[0]['coletado_em_utc'].utcoffset() == timedelta(0)
    assert total_coletas_feriados(tmp_path,2026)==1

def test_gold_mais_recente_e_isolamento(tmp_path):
    f=[Feriado(date(2026,12,25),'Natal','national')]
    salvar_feriados(2026,f,tmp_path,datetime(2026,10,27,15,tzinfo=timezone.utc))
    salvar_feriados(2026,f,tmp_path,datetime(2026,10,27,16,tzinfo=timezone.utc))
    assert len(consultar_feriados_gold(tmp_path,2026))==1
    assert consultar_feriados_gold(tmp_path,2027).empty


def test_migracao_gold_antiga_com_silver(tmp_path):
    import pandas as pd
    instante = datetime(2026, 10, 27, 18, tzinfo=timezone.utc)
    salvar_feriados(2026, [Feriado(date(2026, 12, 25), 'Natal', 'national')], tmp_path, instante)
    gold = tmp_path / 'gold' / 'feriados_atuais.parquet'
    pd.read_parquet(gold).drop(columns=['classificacao','referencia_classificacao']).to_parquet(gold, index=False)
    tabela = consultar_feriados_gold(tmp_path, 2026)
    assert tabela.iloc[0]['classificacao'] == 'Feriado nacional'
    assert 'referencia_classificacao' in pd.read_parquet(gold).columns
    assert len(list((tmp_path / 'bronze' / 'feriados' / '2026').glob('*.json'))) == 1


def test_migracao_gold_antiga_sem_silver(tmp_path):
    import pandas as pd
    gold = tmp_path / 'gold' / 'feriados_atuais.parquet'
    gold.parent.mkdir(parents=True)
    pd.DataFrame([{'ano':2026,'dia':date(2026,12,25),'nome':'Natal',
                   'tipo':'national','coletado_em_utc':datetime(2026,10,27,18,tzinfo=timezone.utc),
                   'coleta_id':'antiga'}]).to_parquet(gold,index=False)
    tabela = consultar_feriados_gold(tmp_path, 2026)
    assert tabela.iloc[0]['classificacao'] == 'Feriado nacional'
    assert tabela.iloc[0]['coletado_em_utc'].hour == 18
