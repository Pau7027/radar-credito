"""Testes da interface entre DataFrames analisados e figuras Plotly."""

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.visualizador import Visualizador


@pytest.fixture
def dados():
    return pd.DataFrame(
        {
            "data": ["2026-02-01", "2026-01-01", "2026-01-01", "2026-02-01"],
            "modalidade": ["Cartão", "Cartão", "Cartão", "Cheque especial"],
            "valor": [6.0, 2.0, 4.0, 8.0],
        }
    )


def test_linhas_agrupam_repeticoes_e_ordenam_datas_sem_alterar_entrada(dados):
    original = dados.copy(deep=True)

    figura = Visualizador.grafico_linhas(dados)

    assert isinstance(figura, go.Figure)
    assert len(figura.data) == 2
    cartao = next(serie for serie in figura.data if serie.name == "Cartão")
    assert list(cartao.y) == [3.0, 6.0]
    assert list(cartao.x) == list(pd.to_datetime(["2026-01-01", "2026-02-01"]))
    pd.testing.assert_frame_equal(dados, original)


def test_linhas_aceitam_serie_sem_modalidade():
    dados = pd.DataFrame({"data": ["2026-01-01"], "valor": [3.5]})

    figura = Visualizador.grafico_linhas(dados)

    assert len(figura.data) == 1
    assert figura.data[0].name == "Inadimplência"


def test_barras_ordenam_taxa_media_por_modalidade(dados):
    figura = Visualizador.grafico_barras(dados)

    assert isinstance(figura, go.Figure)
    assert list(figura.data[0].y) == ["Cartão", "Cheque especial"]
    assert list(figura.data[0].x) == [4.0, 8.0]


def test_treemap_usa_taxas_medias_e_rejeita_taxas_negativas(dados):
    figura = Visualizador.grafico_treemap(dados)

    assert isinstance(figura, go.Figure)
    assert dict(zip(figura.data[0].labels, figura.data[0].values)) == {
        "Cheque especial": 8.0,
        "Cartão": 4.0,
    }
    with pytest.raises(ValueError, match="não negativas"):
        Visualizador.grafico_treemap(
            pd.DataFrame({"modalidade": ["Cartão"], "valor": [-1]})
        )


@pytest.mark.parametrize(
    "metodo,dados",
    [
        (Visualizador.grafico_linhas, pd.DataFrame({"valor": [1]})),
        (Visualizador.grafico_barras, pd.DataFrame({"valor": [1]})),
        (Visualizador.grafico_treemap, pd.DataFrame({"valor": [1]})),
    ],
)
def test_colunas_obrigatorias_geram_erro_claro(metodo, dados):
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        metodo(dados)


def test_dados_sem_valores_validos_geram_erro():
    dados = pd.DataFrame({"modalidade": ["Cartão"], "valor": [None]})

    with pytest.raises(ValueError, match="valores numéricos válidos"):
        Visualizador.grafico_barras(dados)

