"""Gráficos interativos para tabelas de inadimplência.

Os métodos recebem DataFrames prontos, no formato longo usado por
``AnalisadorDados`` (data, modalidade, valor). Nenhum método consulta a API.
``valor`` representa uma taxa percentual: 5.2 significa 5,2%.
"""

import pandas as pd
import plotly.graph_objects as go


class Visualizador:
    """Cria figuras Plotly a partir de DataFrames, sem alterar a entrada."""

    @staticmethod
    def _preparar(dados: pd.DataFrame, colunas: tuple[str, ...]) -> pd.DataFrame:
        if not isinstance(dados, pd.DataFrame):
            raise TypeError("dados deve ser um pandas.DataFrame.")

        ausentes = [coluna for coluna in colunas if coluna not in dados.columns]
        if ausentes:
            raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(ausentes)}.")

        tabela = dados.loc[:, colunas].copy()
        return tabela

    @staticmethod
    def _valores_numericos(tabela: pd.DataFrame, coluna_valor: str) -> pd.DataFrame:
        tabela[coluna_valor] = pd.to_numeric(tabela[coluna_valor], errors="coerce")
        tabela = tabela.dropna(subset=[coluna_valor])
        if tabela.empty:
            raise ValueError("Não há valores numéricos válidos para o gráfico.")
        return tabela

    @staticmethod
    def grafico_linhas(
        dados: pd.DataFrame,
        coluna_data: str = "data",
        coluna_modalidade: str = "modalidade",
        coluna_valor: str = "valor",
    ) -> go.Figure:
        """Mostra a evolução temporal de cada modalidade.

        Linhas repetidas para a mesma data e modalidade são resumidas pela
        média. Se ``modalidade`` não existir, desenha uma única série.
        """
        tem_modalidade = isinstance(dados, pd.DataFrame) and coluna_modalidade in dados
        colunas = (coluna_data, coluna_valor)
        if tem_modalidade:
            colunas += (coluna_modalidade,)
        tabela = Visualizador._preparar(dados, colunas)
        tabela[coluna_data] = pd.to_datetime(tabela[coluna_data], errors="coerce")
        tabela = tabela.dropna(subset=[coluna_data])
        tabela = Visualizador._valores_numericos(tabela, coluna_valor)

        if not tem_modalidade:
            tabela[coluna_modalidade] = "Inadimplência"
        else:
            tabela = tabela.dropna(subset=[coluna_modalidade])
        if tabela.empty:
            raise ValueError("Não há datas e modalidades válidas para o gráfico.")

        agrupado = (
            tabela.groupby([coluna_modalidade, coluna_data], as_index=False)[coluna_valor]
            .mean()
            .sort_values(coluna_data)
        )
        figura = go.Figure()
        for modalidade, serie in agrupado.groupby(coluna_modalidade, sort=True):
            figura.add_trace(
                go.Scatter(
                    x=serie[coluna_data],
                    y=serie[coluna_valor],
                    mode="lines+markers",
                    name=str(modalidade),
                    hovertemplate="%{x|%m/%Y}<br>%{y:.2f}%<extra>%{fullData.name}</extra>",
                )
            )
        figura.update_layout(
            title="Evolução da inadimplência",
            xaxis_title="Data",
            yaxis_title="Taxa de inadimplência (%)",
            hovermode="x unified",
            legend_title="Modalidade",
        )
        return figura

    @staticmethod
    def _media_por_modalidade(
        dados: pd.DataFrame, coluna_modalidade: str, coluna_valor: str
    ) -> pd.DataFrame:
        tabela = Visualizador._preparar(dados, (coluna_modalidade, coluna_valor))
        tabela = tabela.dropna(subset=[coluna_modalidade])
        tabela = Visualizador._valores_numericos(tabela, coluna_valor)
        agrupado = (
            tabela.groupby(coluna_modalidade, as_index=False)[coluna_valor]
            .mean()
            .sort_values(coluna_valor, ascending=False)
        )
        if agrupado.empty:
            raise ValueError("Não há modalidades válidas para o gráfico.")
        return agrupado

    @staticmethod
    def grafico_barras(
        dados: pd.DataFrame,
        coluna_modalidade: str = "modalidade",
        coluna_valor: str = "valor",
    ) -> go.Figure:
        """Ordena as modalidades pela taxa média no DataFrame recebido."""
        agrupado = Visualizador._media_por_modalidade(
            dados, coluna_modalidade, coluna_valor
        )
        agrupado = agrupado.sort_values(coluna_valor)
        figura = go.Figure(
            go.Bar(
                x=agrupado[coluna_valor],
                y=agrupado[coluna_modalidade].astype(str),
                orientation="h",
                text=[f"{valor:.2f}%" for valor in agrupado[coluna_valor]],
                textposition="outside",
                hovertemplate="%{y}<br>Taxa média: %{x:.2f}%<extra></extra>",
            )
        )
        figura.update_layout(
            title="Ranking da inadimplência por modalidade",
            xaxis_title="Taxa média de inadimplência (%)",
            yaxis_title="Modalidade",
        )
        return figura

    @staticmethod
    def grafico_treemap(
        dados: pd.DataFrame,
        coluna_modalidade: str = "modalidade",
        coluna_valor: str = "valor",
    ) -> go.Figure:
        """Compara visualmente as taxas médias por modalidade.

        A área representa a taxa média, não o volume de crédito nem uma
        participação de mercado. Taxas negativas não formam áreas válidas.
        """
        agrupado = Visualizador._media_por_modalidade(
            dados, coluna_modalidade, coluna_valor
        )
        if (agrupado[coluna_valor] < 0).any():
            raise ValueError("O treemap requer taxas não negativas.")
        if (agrupado[coluna_valor] == 0).all():
            raise ValueError("O treemap requer ao menos uma taxa maior que zero.")

        figura = go.Figure(
            go.Treemap(
                labels=agrupado[coluna_modalidade].astype(str),
                parents=[""] * len(agrupado),
                values=agrupado[coluna_valor],
                texttemplate="%{label}<br>%{value:.2f}%",
                hovertemplate="%{label}<br>Taxa média: %{value:.2f}%<extra></extra>",
            )
        )
        figura.update_layout(title="Taxa média por modalidade")
        return figura

