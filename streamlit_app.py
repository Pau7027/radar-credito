"""Painel Streamlit do RadarCrédito."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.analisador import AnalisadorDados
from src.dashboard import Dashboard
from src.fonte_dados import FonteBCB
from src.indicadores import VariacaoVsMedia12m, Volatilidade12m, ZScore
from src.visualizador import Visualizador

DATA_INICIO = "01/11/2016"
DATA_FIM = "31/10/2026"
PASTA_DADOS = Path(__file__).resolve().parent / "data"

SERIES = {
    "Total": 21082,
    "Pessoa jurídica": 21083,
    "Pessoa física": 21084,
    "PF recursos livres": 21112,
    "PF cheque especial": 21113,
    "PF cartão de crédito": 21129,
    "PF recursos direcionados": 21145,
}

SERIES_FOLHA = [
    "PF cheque especial",
    "PF cartão de crédito",
    "PF recursos direcionados",
]


@st.cache_data(ttl=3600)
def carregar_dados() -> pd.DataFrame:
    """Carrega as séries temporais via FonteBCB (com fallback de cache em data/)."""
    fonte = FonteBCB(pasta_cache=str(PASTA_DADOS), tempo_limite=15)
    tabelas_longas = []

    for nome_amigavel, codigo in SERIES.items():
        tabela = fonte.obter_serie(codigo, DATA_INICIO, DATA_FIM)
        tabela_copia = tabela.copy()
        tabela_copia["modalidade"] = nome_amigavel
        tabelas_longas.append(tabela_copia[["data", "modalidade", "valor"]])

    dados_completos = pd.concat(tabelas_longas, ignore_index=True)
    dados_completos["data"] = pd.to_datetime(dados_completos["data"], errors="coerce")
    dados_completos["valor"] = pd.to_numeric(dados_completos["valor"], errors="coerce")
    return dados_completos


def main() -> None:
    """Função principal que inicializa e renderiza o dashboard Streamlit."""
    st.set_page_config(page_title="RadarCrédito", layout="wide")

    dados = carregar_dados()
    analisador = AnalisadorDados(dados)

    indicadores = {
        "Variação vs. média de 12 meses": VariacaoVsMedia12m,
        "Volatilidade (12 meses)": Volatilidade12m,
        "Z-score": ZScore,
    }

    descricao = (
        "Painel interativo com séries temporais de inadimplência da carteira de crédito "
        "brasileira obtidas via API SGS do Banco Central do Brasil. A taxa de inadimplência "
        "mede o percentual da carteira de crédito do Sistema Financeiro Nacional com "
        "atrasos de pagamento superiores a 90 dias."
    )

    # TODO: series_macro será preenchida quando a Selic (código 432, diária, em blocos de 10 anos)
    # e o IPCA (código 433, variação mensal) forem integrados ao projeto.
    series_macro = None

    dashboard = Dashboard(
        analisador=analisador,
        indicadores=indicadores,
        visualizador=Visualizador(),
        titulo="RadarCrédito",
        descricao=descricao,
        series_folha=SERIES_FOLHA,
        series_macro=series_macro,
    )

    dashboard.renderizar()

    datas_validas = pd.to_datetime(dados["data"], errors="coerce").dropna()
    if not datas_validas.empty:
        ultima_data = datas_validas.max()
        st.caption(f"Última data disponível nos dados: {ultima_data.strftime('%d/%m/%Y')}.")


if __name__ == "__main__":
    main()
