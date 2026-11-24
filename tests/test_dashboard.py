"""Testes de integração do aplicativo Streamlit com os CSVs versionados."""

import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest
import requests
from streamlit.testing.v1 import AppTest


RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def painel(monkeypatch):
    monkeypatch.setattr(
        "src.fonte_dados.requests.get", Mock(side_effect=requests.ConnectionError("SGS indisponível"))
    )
    app = AppTest.from_file(str(RAIZ / "streamlit_app.py"), default_timeout=20).run()
    assert not app.exception
    assert not app.error
    return app


def test_painel_abre_com_dados_locais(painel):
    assert painel.title[0].value == "RadarCrédito"
    assert [aba.label for aba in painel.tabs] == [
        "Evolução", "Comparação", "Correlações", "Análise e conclusões", "Tabela de dados",
    ]
    assert len(painel.get("plotly_chart")) == 6
    assert len(painel.metric) == 4
    assert painel.selectbox[0].value == "Total"
    assert not painel.warning

    modalidades = painel.dataframe[0].value["Série"]
    assert set(modalidades) == set(painel.sidebar.multiselect[0].options)
    assert modalidades.nunique() == 7


def test_filtros_atualizam_tabela_e_indicador_de_inadimplencia(painel):
    painel.sidebar.date_input[0].set_value(date(2026, 1, 1))
    painel.sidebar.date_input[1].set_value(date(2026, 6, 30))
    painel.sidebar.multiselect[0].set_value(["Total"]).run()

    assert not painel.exception
    tabela = painel.dataframe[0].value
    assert tabela["Data"].tolist() == [f"{mes:02d}/2026" for mes in range(6, 0, -1)]
    assert tabela["Série"].tolist() == ["Total"] * 6
    total = pd.read_csv(RAIZ / "data" / "serie_21082.csv", index_col="data")
    taxa_junho = f"{total.loc['2026-06-01', 'valor']:.2f}%".replace(".", ",")
    assert tabela["Taxa de inadimplência (%)"].iloc[0] == taxa_junho
    assert painel.metric[0].value == taxa_junho


def test_controle_de_defasagem_atualiza_grafico_de_dispersao(painel):
    painel.slider[0].set_value(4).run()

    assert not painel.exception
    figuras = [json.loads(grafico.proto.spec) for grafico in painel.tabs[2].get("plotly_chart")]
    dispersao = next(
        figura for figura in figuras
        if any(traco.get("mode") == "markers" for traco in figura["data"])
    )
    assert "defasada em 4 meses" in dispersao["layout"]["xaxis"]["title"]["text"]


def test_painel_pede_ao_menos_uma_serie(painel):
    painel.sidebar.multiselect[0].set_value([]).run()

    assert not painel.exception
    assert [aviso.value for aviso in painel.warning] == ["Selecione ao menos uma série."]
    assert not painel.dataframe


def test_painel_rejeita_periodo_invertido(painel):
    painel.sidebar.date_input[0].set_value(date(2026, 7, 1))
    painel.sidebar.date_input[1].set_value(date(2026, 6, 30)).run()

    assert not painel.exception
    assert [aviso.value for aviso in painel.warning] == [
        "A data inicial deve ser anterior ou igual à data final."
    ]
    assert not painel.dataframe
