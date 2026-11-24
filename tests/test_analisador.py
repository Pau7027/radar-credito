"""Testes dos filtros e do alinhamento mensal do analisador."""

import pandas as pd
import pytest

from src.analisador import AnalisadorDados


def test_filtro_combina_datas_inclusivas_e_modalidades_sem_alterar_dados():
    dados = pd.DataFrame(
        {
            "data": ["2026-01-01", "2026-02-01", "2026-02-01", "2026-03-01", "inválida"],
            "modalidade": ["Total", "Total", "Pessoa física", "Pessoa jurídica", "Total"],
            "valor": [3.5, 4.0, 5.5, 2.5, 9.9],
        }
    )
    analisador = AnalisadorDados(dados)

    resultado = analisador.filtrar(
        inicio="2026-01-01", fim="2026-02-01", modalidade=["Total", "Pessoa física"]
    )

    pd.testing.assert_frame_equal(resultado, dados.iloc[:3])
    pd.testing.assert_frame_equal(analisador.dados, dados)


@pytest.mark.parametrize(("operacao", "valor_janeiro"), [("ultimo", 12.0), ("media", 11.0)])
def test_agregacao_mensal_ordena_datas_e_usa_primeiro_dia(operacao, valor_janeiro):
    diaria = pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-01-30", "2026-02-20", "2026-01-02"]),
            "valor": [12.0, 13.0, 10.0],
        }
    )

    mensal = AnalisadorDados.agregar_mensal(diaria, operacao)

    assert mensal["data"].tolist() == list(pd.to_datetime(["2026-01-01", "2026-02-01"]))
    assert mensal["valor"].tolist() == [valor_janeiro, 13.0]


def test_juncao_preserva_meses_presentes_em_apenas_uma_serie():
    datas = pd.to_datetime(["2026-01-01", "2026-02-01", "2026-03-01"])
    selic = pd.DataFrame({"data": datas[[2, 0]], "valor": [13.0, 12.0]})
    ipca = pd.DataFrame({"data": datas[[1, 2]], "valor": [0.2, 0.3]})

    tabela = AnalisadorDados.unir_series({"selic": selic, "ipca": ipca})

    esperado = pd.DataFrame(
        {"selic": [12.0, float("nan"), 13.0], "ipca": [float("nan"), 0.2, 0.3]},
        index=datas.rename("data"),
    )
    pd.testing.assert_frame_equal(tabela, esperado, check_freq=False)
