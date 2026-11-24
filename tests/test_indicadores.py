"""Testes das janelas, da equação de Fisher e da defasagem da Selic."""

from statistics import mean, stdev

import pandas as pd
import pytest

from src.indicadores import DefasagemOtima, JurosReais, VariacaoVsMedia12m, Volatilidade12m, ZScore


@pytest.fixture
def inadimplencia():
    datas = pd.date_range("2025-01-01", periods=13, freq="MS")
    return pd.Series(range(1, 14), index=datas, dtype=float)


def test_variacao_compara_mes_atual_com_os_doze_anteriores(inadimplencia):
    resultado = VariacaoVsMedia12m(inadimplencia).calcular()

    assert resultado.iloc[:12].isna().all()
    assert resultado.iloc[-1] == pytest.approx(13 - mean(range(1, 13)))


def test_volatilidade_amostral_inclui_mes_atual(inadimplencia):
    resultado = Volatilidade12m(inadimplencia).calcular()

    assert resultado.iloc[:11].isna().all()
    assert resultado.iloc[11] == pytest.approx(stdev(range(1, 13)))
    assert resultado.iloc[12] == pytest.approx(stdev(range(2, 14)))


def test_zscore_usa_media_e_desvio_amostral_do_historico(inadimplencia):
    resultado = ZScore(inadimplencia).calcular()

    assert resultado.iloc[-1] == pytest.approx((13 - mean(range(1, 14))) / stdev(range(1, 14)))
    assert resultado.mean() == pytest.approx(0)
    assert resultado.std(ddof=1) == pytest.approx(1)


@pytest.mark.parametrize("janela", [None, 3])
def test_zscore_de_serie_constante_e_indefinido(inadimplencia, janela):
    constante = pd.Series(3.0, index=inadimplencia.index)

    assert ZScore(constante, janela=janela).calcular().isna().all()


def test_juros_reais_usam_ipca_composto_em_janela_de_doze_meses(inadimplencia):
    selic = pd.Series(12.0, index=inadimplencia.index)
    ipca = pd.Series([-1.0] + [0.5] * 12, index=inadimplencia.index)

    resultado = JurosReais(selic, ipca).calcular()

    assert resultado.iloc[:11].isna().all()
    assert resultado.iloc[11] == pytest.approx(100 * (1.12 / (0.99 * 1.005**11) - 1))
    assert resultado.iloc[12] == pytest.approx(100 * (1.12 / 1.005**12 - 1))


def test_defasagem_maximiza_modulo_e_preserva_sinal_da_correlacao():
    datas = pd.date_range("2025-01-01", periods=10, freq="MS")
    selic = pd.Series([10, 2, 7, 5, 18, 25, 11, 4, 21, 27], index=datas, dtype=float)
    inadimplencia = 30 - selic.shift(3)
    indicador = DefasagemOtima(selic, inadimplencia, defasagem_maxima=5)

    resultado = indicador.calcular().set_index("defasagem")

    assert resultado.index.tolist() == list(range(6))
    assert resultado.loc[3, "observacoes"] == 7
    assert indicador.defasagem_otima == 3
    assert indicador.correlacao_otima == pytest.approx(-1)
