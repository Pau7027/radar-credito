"""Painel Streamlit com as séries de inadimplência em cache no repositório."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.analisador import AnalisadorDados
from src.visualizador import Visualizador


SERIES = {
    "Total": 21082,
    "Pessoa física": 21084,
    "Cheque especial": 21113,
    "Cartão de crédito": 21129,
}


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    """Lê apenas os CSVs locais; o Visualizador não acessa a fonte de dados."""
    pasta_dados = Path(__file__).resolve().parent / "data"
    tabelas = []
    for modalidade, codigo in SERIES.items():
        tabela = pd.read_csv(pasta_dados / f"serie_{codigo}.csv", parse_dates=["data"])
        tabela["modalidade"] = modalidade
        tabelas.append(tabela)
    return pd.concat(tabelas, ignore_index=True)


def main() -> None:
    st.set_page_config(page_title="Radar Crédito", layout="wide")
    st.title("Radar Crédito")
    st.caption("Inadimplência no Brasil · séries SGS do Banco Central salvas no repositório")

    dados = carregar_dados()
    primeira_data = dados["data"].min().date()
    ultima_data = dados["data"].max().date()

    st.sidebar.header("Filtros")
    inicio = st.sidebar.date_input(
        "Data inicial", value=primeira_data, min_value=primeira_data, max_value=ultima_data
    )
    fim = st.sidebar.date_input(
        "Data final", value=ultima_data, min_value=primeira_data, max_value=ultima_data
    )
    modalidades = st.sidebar.multiselect(
        "Modalidades", options=list(SERIES), default=list(SERIES)
    )

    if inicio > fim:
        st.warning("A data inicial deve ser anterior ou igual à data final.")
        st.stop()
    if not modalidades:
        st.warning("Selecione ao menos uma modalidade.")
        st.stop()

    filtrados = AnalisadorDados(dados).filtrar(
        inicio=inicio, fim=fim, modalidade=modalidades
    )
    if filtrados.empty:
        st.info("Não há registros para os filtros escolhidos.")
        st.stop()

    st.plotly_chart(Visualizador.grafico_linhas(filtrados), width="stretch")
    st.plotly_chart(Visualizador.grafico_barras(filtrados), width="stretch")
    st.plotly_chart(Visualizador.grafico_treemap(filtrados), width="stretch")
    st.caption(
        "No treemap, a área compara taxas médias de inadimplência; "
        "não representa volume de crédito nem participação de mercado."
    )
    st.caption(f"Última data disponível nos CSVs: {ultima_data:%d/%m/%Y}.")


if __name__ == "__main__":
    main()

