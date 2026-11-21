"""Testes da interface entre DataFrames analisados e figuras Plotly."""

import numpy as np
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


def test_dispersao_reta_correta():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0 * val + 1.0 for val in x]
    dados = pd.DataFrame({"selic": x, "inadimplencia": y})

    figura = Visualizador.grafico_dispersao_defasada(dados)

    assert isinstance(figura, go.Figure)
    assert len(figura.data) == 2
    reta = figura.data[1]
    assert "R² = 1,00" in reta.name
    x0, x1 = reta.x[0], reta.x[1]
    y0, y1 = reta.y[0], reta.y[1]
    inclinacao = (y1 - y0) / (x1 - x0)
    intercepto = y0 - inclinacao * x0
    assert inclinacao == pytest.approx(2.0)
    assert intercepto == pytest.approx(1.0)


def test_dispersao_defasagem_ajuste():
    datas = pd.date_range("2024-01-01", periods=24, freq="MS")
    valores_x = [float(i * 1.5 + (i % 4)) for i in range(24)]
    serie_x = pd.Series(valores_x, index=datas)
    serie_y = serie_x.shift(3)
    dados = pd.DataFrame({"selic": serie_x, "inadimplencia": serie_y}, index=datas)

    fig_defasada = Visualizador.grafico_dispersao_defasada(dados, defasagem=3)
    assert "R² = 1,00" in fig_defasada.data[1].name

    fig_sem_defasagem = Visualizador.grafico_dispersao_defasada(dados, defasagem=0)
    assert "R² = 1,00" not in fig_sem_defasagem.data[1].name


def test_dispersao_numero_de_pontos():
    n = 20
    k = 4
    x = [float(i) for i in range(n)]
    y = [float(i * 2 + 1) for i in range(n)]
    dados = pd.DataFrame({"selic": x, "inadimplencia": y})

    figura = Visualizador.grafico_dispersao_defasada(dados, defasagem=k)
    pontos = figura.data[0]

    assert len(pontos.x) == n - k
    assert len(pontos.y) == n - k


def test_dispersao_data_no_indice_e_em_coluna_equivalentes():
    datas = pd.date_range("2025-01-01", periods=6, freq="MS")
    x = [1.0, 2.0, 3.5, 4.0, 5.2, 6.1]
    y = [2.1, 4.0, 6.8, 8.1, 10.5, 12.0]
    dados_indice = pd.DataFrame({"selic": x, "inadimplencia": y}, index=datas)
    dados_coluna = pd.DataFrame({"data": datas, "selic": x, "inadimplencia": y})

    fig_indice = Visualizador.grafico_dispersao_defasada(dados_indice)
    fig_coluna = Visualizador.grafico_dispersao_defasada(dados_coluna)

    assert list(fig_indice.data[0].x) == list(fig_coluna.data[0].x)
    assert list(fig_indice.data[0].y) == list(fig_coluna.data[0].y)
    assert list(fig_indice.data[0].customdata) == list(fig_coluna.data[0].customdata)
    assert list(fig_indice.data[1].x) == list(fig_coluna.data[1].x)
    assert list(fig_indice.data[1].y) == list(fig_coluna.data[1].y)
    assert fig_indice.layout.title.text == fig_coluna.layout.title.text
    assert fig_indice.layout.xaxis.title.text == fig_coluna.layout.xaxis.title.text


def test_dispersao_erros_claros():
    dados_ok = pd.DataFrame({"selic": [1.0, 2.0, 3.0, 4.0], "inadimplencia": [2.0, 3.0, 4.0, 5.0]})

    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        Visualizador.grafico_dispersao_defasada(pd.DataFrame({"x": [1, 2, 3]}))

    with pytest.raises((ValueError, TypeError)):
        Visualizador.grafico_dispersao_defasada(dados_ok, defasagem=-1)

    with pytest.raises((ValueError, TypeError)):
        Visualizador.grafico_dispersao_defasada(dados_ok, defasagem=1.5)

    with pytest.raises((ValueError, TypeError)):
        Visualizador.grafico_dispersao_defasada(dados_ok, defasagem=True)

    with pytest.raises(ValueError, match="observações suficientes"):
        Visualizador.grafico_dispersao_defasada(pd.DataFrame({"selic": [1.0, 2.0], "inadimplencia": [3.0, 4.0]}))

    with pytest.raises(ValueError, match="variância zero"):
        Visualizador.grafico_dispersao_defasada(
            pd.DataFrame({"selic": [2.0, 2.0, 2.0, 2.0], "inadimplencia": [1.0, 2.0, 3.0, 4.0]})
        )

    with pytest.raises(TypeError, match="pandas.DataFrame"):
        Visualizador.grafico_dispersao_defasada([1, 2, 3])


def test_dispersao_textos_em_portugues():
    dados = pd.DataFrame(
        {
            "tx_juros": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "inad": [2.0, 3.0, 5.0, 7.0, 8.0, 10.0],
        }
    )

    fig_sem_def = Visualizador.grafico_dispersao_defasada(
        dados, "tx_juros", "inad", defasagem=0, rotulo_x="Taxa Selic", rotulo_y="Inadimplência PF"
    )
    assert "Taxa Selic" in fig_sem_def.layout.title.text
    assert "Inadimplência PF" in fig_sem_def.layout.title.text
    assert "Taxa Selic" in fig_sem_def.layout.xaxis.title.text
    assert "Inadimplência PF" in fig_sem_def.layout.yaxis.title.text

    fig_com_def = Visualizador.grafico_dispersao_defasada(
        dados, "tx_juros", "inad", defasagem=2, rotulo_x="Taxa Selic", rotulo_y="Inadimplência PF"
    )
    assert "Taxa Selic" in fig_com_def.layout.title.text
    assert "defasada em 2 meses" in fig_com_def.layout.title.text
    assert "defasada em 2 meses" in fig_com_def.layout.xaxis.title.text
    assert fig_com_def.layout.legend.title.text == "Legenda"


def test_heatmap_propriedades_e_filtros():
    dados = pd.DataFrame(
        {
            "data": ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01"],
            "categoria": ["A", "B", "C", "D"],
            "pf": [1.0, 2.0, 3.0, 4.0],
            "pj": [4.0, 3.0, 2.0, 1.0],
            "total": [2.0, 4.0, 6.0, 8.0],
        }
    )
    rotulos = {"pf": "Pessoa Física", "pj": "Pessoa Jurídica", "total": "Total Geral"}

    figura = Visualizador.grafico_heatmap_correlacao(dados, rotulos=rotulos)

    assert isinstance(figura, go.Figure)
    heatmap = figura.data[0]
    assert list(heatmap.x) == ["Pessoa Física", "Pessoa Jurídica", "Total Geral"]
    assert list(heatmap.y) == ["Pessoa Física", "Pessoa Jurídica", "Total Geral"]

    matriz_z = np.array(heatmap.z, dtype=float)
    assert matriz_z.shape == (3, 3)
    assert np.allclose(matriz_z, matriz_z.T)

    for i in range(3):
        assert matriz_z[i, i] == pytest.approx(1.0)

    assert np.all((matriz_z >= -1.0) & (matriz_z <= 1.0))
    assert matriz_z[0, 1] == pytest.approx(-1.0)
    assert matriz_z[0, 2] == pytest.approx(1.0)

    fig_restrita = Visualizador.grafico_heatmap_correlacao(dados, colunas=["pf", "pj"])
    assert list(fig_restrita.data[0].x) == ["pf", "pj"]
    assert list(fig_restrita.data[0].y) == ["pf", "pj"]


def test_heatmap_erros():
    dados_insuficiente = pd.DataFrame(
        {"data": ["2026-01-01", "2026-02-01", "2026-03-01"], "unica": [1.0, 2.0, 3.0]}
    )
    with pytest.raises(ValueError, match="pelo menos 2 colunas numéricas"):
        Visualizador.grafico_heatmap_correlacao(dados_insuficiente)

    dados_ok = pd.DataFrame({"pf": [1.0, 2.0, 3.0], "pj": [4.0, 5.0, 6.0]})
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        Visualizador.grafico_heatmap_correlacao(dados_ok, colunas=["pf", "inexistente"])

    with pytest.raises(TypeError, match="pandas.DataFrame"):
        Visualizador.grafico_heatmap_correlacao("não dataframe")


def test_metodos_novos_nao_alteram_entrada():
    dados_disp = pd.DataFrame({"selic": [1.0, 2.0, 3.0, 4.0], "inadimplencia": [4.0, 3.0, 2.0, 1.0]})
    copia_disp = dados_disp.copy(deep=True)
    Visualizador.grafico_dispersao_defasada(dados_disp, defasagem=1)
    pd.testing.assert_frame_equal(dados_disp, copia_disp)

    dados_heat = pd.DataFrame(
        {"s1": [1.0, 2.0, 3.0], "s2": [4.0, 5.0, 6.0], "texto": ["a", "b", "c"]}
    )
    copia_heat = dados_heat.copy(deep=True)
    Visualizador.grafico_heatmap_correlacao(dados_heat)
    pd.testing.assert_frame_equal(dados_heat, copia_heat)


