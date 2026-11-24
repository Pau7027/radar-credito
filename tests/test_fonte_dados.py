"""Testes da coleta SGS e do cache local."""

from pathlib import Path
from unittest.mock import Mock, call

import pandas as pd
import pytest
import requests

from src.fonte_dados import ErroFonteDados, FonteBCB


def resposta_sgs(registros):
    resposta = Mock(spec=requests.Response)
    resposta.json.return_value = registros
    return resposta


def test_coleta_em_blocos_normaliza_dados_e_atualiza_cache(monkeypatch, tmp_path):
    cache = tmp_path / "serie_21082.csv"
    cache.write_text("data,valor\n2015-12-01,1.0\n2016-11-01,9.9\n", encoding="utf-8")
    primeira = resposta_sgs(
        [
            {"data": "01/12/2020", "valor": "3.2"},
            {"data": "01/11/2016", "valor": "3.86"},
            {"data": "01/12/2020", "valor": "3.2"},
        ]
    )
    segunda = resposta_sgs([{"data": "01/11/2021", "valor": "2.5"}])
    consultar = Mock(side_effect=[primeira, segunda])
    monkeypatch.setattr("src.fonte_dados.requests.get", consultar)

    fonte = FonteBCB(pasta_cache=tmp_path, tempo_limite=5)
    tabela = fonte.obter_serie(21082, "01/11/2016", "30/11/2021")

    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.21082/dados"
    assert consultar.call_args_list == [
        call(
            url,
            params={"formato": "json", "dataInicial": "01/11/2016", "dataFinal": "31/10/2021"},
            timeout=5,
        ),
        call(
            url,
            params={"formato": "json", "dataInicial": "01/11/2021", "dataFinal": "30/11/2021"},
            timeout=5,
        ),
    ]
    primeira.raise_for_status.assert_called_once_with()
    segunda.raise_for_status.assert_called_once_with()
    esperado = pd.DataFrame(
        {
            "data": pd.to_datetime(["2016-11-01", "2020-12-01", "2021-11-01"]),
            "valor": [3.86, 3.2, 2.5],
        }
    )
    pd.testing.assert_frame_equal(tabela, esperado)
    atualizado = pd.read_csv(cache, parse_dates=["data"])
    assert atualizado["data"].dt.strftime("%Y-%m-%d").tolist() == [
        "2015-12-01", "2016-11-01", "2020-12-01", "2021-11-01",
    ]
    assert atualizado["valor"].tolist() == [1.0, 3.86, 3.2, 2.5]


def test_bloco_vazio_preserva_observacoes_dos_outros_blocos(monkeypatch, tmp_path):
    respostas = [
        resposta_sgs([{"data": "01/11/2016", "valor": "3.86"}]),
        resposta_sgs([]),
    ]
    monkeypatch.setattr("src.fonte_dados.requests.get", Mock(side_effect=respostas))

    fonte = FonteBCB(pasta_cache=tmp_path)
    tabela = fonte.obter_serie(21082, "01/11/2016", "30/11/2021")

    assert tabela["data"].tolist() == [pd.Timestamp("2016-11-01")]
    assert tabela["valor"].tolist() == [3.86]
    assert (tmp_path / "serie_21082.csv").is_file()


def test_falha_de_rede_usa_cache_com_limites_inclusivos(monkeypatch, tmp_path):
    cache = tmp_path / "serie_21082.csv"
    original = "data,valor\n2026-01-01,3.5\n2026-02-01,4.0\n2026-03-01,4.5\n2026-04-01,5.0\n"
    cache.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        "src.fonte_dados.requests.get", Mock(side_effect=requests.ConnectionError("SGS indisponível"))
    )

    fonte = FonteBCB(pasta_cache=tmp_path)
    tabela = fonte.obter_serie(21082, "01/02/2026", "01/03/2026")

    assert tabela["data"].tolist() == list(pd.to_datetime(["2026-02-01", "2026-03-01"]))
    assert tabela["valor"].tolist() == [4.0, 4.5]
    assert cache.read_text(encoding="utf-8") == original


def test_falha_de_rede_sem_cache_identifica_a_serie(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.fonte_dados.requests.get", Mock(side_effect=requests.Timeout("SGS indisponível"))
    )
    fonte = FonteBCB(pasta_cache=tmp_path)

    with pytest.raises(ErroFonteDados, match="sem cache local para a série 21082"):
        fonte.obter_serie(21082, "01/02/2026", "01/03/2026")


@pytest.mark.parametrize("codigo", [21082, 21083, 21084, 21112, 21113, 21129, 21145])
def test_cache_versionado_de_credito_tem_taxas_validas_e_meses_contiguos(codigo):
    pasta_dados = Path(__file__).resolve().parents[1] / "data"
    tabela = pd.read_csv(pasta_dados / f"serie_{codigo}.csv", parse_dates=["data"])
    datas = pd.DatetimeIndex(tabela["data"])

    assert len(datas) >= 12
    assert datas.equals(pd.date_range(datas[0], datas[-1], freq="MS"))
    assert tabela["valor"].between(0, 100).all()
