"""Gráficos interativos para tabelas de inadimplência.

Os métodos recebem DataFrames prontos, tanto no formato longo (data,
modalidade, valor) quanto no formato largo (índice = data, uma coluna
por série). Nenhum método consulta a API.
``valor`` representa uma taxa percentual: 5.2 significa 5,2%.
"""

import numpy as np
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

    @staticmethod
    def _ajustar_reta(
        x: pd.Series | np.ndarray, y: pd.Series | np.ndarray
    ) -> tuple[float, float, float]:
        """Ajusta reta de regressão linear simples via mínimos quadrados ordinários.

        Calcula a inclinação, o intercepto e o coeficiente de determinação (R²)
        da relação linear entre as variáveis x e y. Também calcula o coeficiente
        de correlação linear de Pearson r com numpy.corrcoef.

        Parâmetros:
            x: Série ou array com os valores da variável independente.
            y: Série ou array com os valores da variável dependente.

        Retorno:
            Tupla contendo (inclinação, intercepto, R²).
        """
        x_arr = np.asarray(x, dtype=float)
        y_arr = np.asarray(y, dtype=float)

        matriz_corr = np.corrcoef(x_arr, y_arr)
        _r = float(matriz_corr[0, 1])

        inclinacao, intercepto = np.polyfit(x_arr, y_arr, 1)

        y_pred = inclinacao * x_arr + intercepto
        sq_res = float(np.sum((y_arr - y_pred) ** 2))
        y_media = float(np.mean(y_arr))
        sq_tot = float(np.sum((y_arr - y_media) ** 2))

        if sq_tot == 0:
            r2 = 0.0
        else:
            r2 = 1.0 - (sq_res / sq_tot)

        if r2 < 0.0:
            r2 = 0.0
        elif r2 > 1.0:
            r2 = 1.0

        return float(inclinacao), float(intercepto), float(r2)

    @staticmethod
    def grafico_dispersao_defasada(
        dados: pd.DataFrame,
        coluna_x: str = "selic",
        coluna_y: str = "inadimplencia",
        defasagem: int = 0,
        rotulo_x: str = "Selic meta (% a.a.)",
        rotulo_y: str = "Inadimplência (%)",
    ) -> go.Figure:
        """Gráfico de dispersão com reta de regressão linear e defasagem temporal.

        O que mostra:
            A relação contemporânea ou defasada entre duas variáveis contínuas
            (como taxa de juros Selic e taxa de inadimplência), acompanhada
            pela reta de ajuste linear de mínimos quadrados e seu R².

        Formato de entrada:
            DataFrame no formato largo (uma coluna por série), com frequência
            mensal. As séries diárias (como a taxa Selic) devem ser agregadas
            previamente por mês antes do envio ao Visualizador. A data de
            referência pode estar no índice (DatetimeIndex) ou em uma coluna
            chamada 'data'. A data é utilizada exclusivamente para rotular
            as observações no hover do gráfico.

        Aplicação da defasagem:
            O eixo X utiliza a série informada em ``coluna_x`` defasada em
            ``defasagem`` meses (x_{t-k}), alinhada ao valor contemporâneo
            y_t em ``coluna_y`` (através da operação shift sobre as linhas
            previamente ordenadas por data).

        Interpretação da reta e do R²:
            A inclinação indica a variação esperada em pontos percentuais na
            variável Y para cada aumento de uma unidade na variável X. O R²
            (coeficiente de determinação) quantifica a proporção da variância
            amostral de Y explicada linearmente por X.

        Advertência estatística:
            Correlação não é causalidade; duas séries temporais com tendência
            concomitante (estacionalidade ou ciclo econômico) podem apresentar
            correlação espúria mesmo sem relação direta de causa e efeito.

        Exemplo de uso:
            # visualizador.grafico_dispersao_defasada(
            #     tabela_larga, "selic", "pessoa_fisica", defasagem=indicador.defasagem_otima
            # )
        """
        if not isinstance(dados, pd.DataFrame):
            raise TypeError("dados deve ser um pandas.DataFrame.")

        ausentes = []
        for col in (coluna_x, coluna_y):
            if col not in dados.columns:
                ausentes.append(col)
        if ausentes:
            raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(ausentes)}.")

        if isinstance(defasagem, bool) or not isinstance(defasagem, int):
            raise TypeError("O parâmetro 'defasagem' deve ser um número inteiro.")
        if defasagem < 0:
            raise ValueError("O parâmetro 'defasagem' deve ser um número inteiro maior ou igual a zero.")

        tabela = dados.copy()

        datas_hover = None
        if "data" in tabela.columns:
            tabela["_data_temp"] = pd.to_datetime(tabela["data"], errors="coerce")
            tabela = tabela.sort_values("_data_temp")
            datas_hover = tabela["_data_temp"]
        elif isinstance(tabela.index, pd.DatetimeIndex):
            tabela = tabela.sort_index()
            datas_hover = pd.to_datetime(tabela.index)

        serie_x = pd.to_numeric(tabela[coluna_x], errors="coerce").shift(defasagem)
        serie_y = pd.to_numeric(tabela[coluna_y], errors="coerce")

        df_pares = pd.DataFrame({"x": serie_x, "y": serie_y}, index=tabela.index)
        if datas_hover is not None:
            df_pares["data"] = datas_hover

        df_pares = df_pares.dropna(subset=["x", "y"])

        if len(df_pares) < 3:
            raise ValueError("Não há observações suficientes para o gráfico e o ajuste da reta.")

        var_x = float(df_pares["x"].var())
        var_y = float(df_pares["y"].var())
        if var_x == 0 or var_y == 0 or np.isclose(var_x, 0) or np.isclose(var_y, 0):
            raise ValueError("Não é possível ajustar a reta quando uma das séries possui variância zero.")

        inclinacao, intercepto, r2 = Visualizador._ajustar_reta(df_pares["x"], df_pares["y"])

        tem_data_valida = "data" in df_pares and df_pares["data"].notna().any()
        if tem_data_valida:
            textos_mes = []
            for d in df_pares["data"]:
                if pd.notna(d):
                    textos_mes.append(pd.to_datetime(d).strftime("%m/%Y"))
                else:
                    textos_mes.append("")
            hovertemplate_pontos = (
                f"%{{customdata}}<br>{rotulo_x}: %{{x:.2f}}<br>{rotulo_y}: %{{y:.2f}}<extra></extra>"
            )
            traco_pontos = go.Scatter(
                x=df_pares["x"],
                y=df_pares["y"],
                mode="markers",
                name="Observações mensais",
                customdata=textos_mes,
                hovertemplate=hovertemplate_pontos,
            )
        else:
            hovertemplate_pontos = (
                f"{rotulo_x}: %{{x:.2f}}<br>{rotulo_y}: %{{y:.2f}}<extra></extra>"
            )
            traco_pontos = go.Scatter(
                x=df_pares["x"],
                y=df_pares["y"],
                mode="markers",
                name="Observações mensais",
                hovertemplate=hovertemplate_pontos,
            )

        x_min = float(df_pares["x"].min())
        x_max = float(df_pares["x"].max())
        x_reta = [x_min, x_max]
        y_reta = [inclinacao * x_min + intercepto, inclinacao * x_max + intercepto]

        r2_formatado = f"{r2:.2f}".replace(".", ",")
        nome_reta = f"Regressão linear (R² = {r2_formatado})"
        traco_reta = go.Scatter(
            x=x_reta,
            y=y_reta,
            mode="lines",
            name=nome_reta,
            hovertemplate=f"{nome_reta}<extra></extra>",
        )

        figura = go.Figure()
        figura.add_trace(traco_pontos)
        figura.add_trace(traco_reta)

        if defasagem == 0:
            titulo = f"Relação entre {rotulo_x} e {rotulo_y}"
            titulo_x = rotulo_x
        else:
            titulo = f"{rotulo_x} defasada em {defasagem} meses vs. {rotulo_y}"
            titulo_x = f"{rotulo_x} (defasada em {defasagem} meses)"

        figura.update_layout(
            title=titulo,
            xaxis_title=titulo_x,
            yaxis_title=rotulo_y,
            legend_title="Legenda",
        )
        return figura

    @staticmethod
    def grafico_heatmap_correlacao(
        dados: pd.DataFrame,
        colunas: list[str] | None = None,
        rotulos: dict[str, str] | None = None,
    ) -> go.Figure:
        """Matriz de correlação linear de Pearson em formato de mapa de calor.

        O que mostra:
            O mapa de calor (heatmap) apresenta a intensidade e o sentido das
            associações lineares bivariadas (coeficiente de Pearson r) entre os
            níveis contemporâneos das séries temporais informadas, sem defasagem.

        Leitura das cores:
            A escala divergente (RdBu_r) mapeia valores no intervalo [-1, 1],
            com centro fixo em 0. Tons de azul representam correlação positiva
            (séries que se movem conjuntamente na mesma direção), tons de
            vermelho indicam correlação negativa (movimentos em direções opostas)
            e tons neutros (brancos) apontam ausência de relação linear. Células
            vazias representam séries com variância zero ou dados insuficientes.

        Advertência estatística:
            Correlação linear elevada entre os níveis de duas séries temporais
            não implica causalidade mútua; trajetórias históricas com tendência
            macroeconômica comum ou estacionalidade podem gerar correlações
            espúrias. Relações com defasagem temporal devem ser investigadas por
            meio do indicador ``DefasagemOtima`` e do gráfico de dispersão defasada.

        Parâmetros:
            dados: DataFrame no formato largo (uma coluna por série).
            colunas: Lista opcional de colunas a incluir. Se omitido, utiliza
                todas as colunas numéricas disponíveis, ignorando a coluna 'data'.
            rotulos: Dicionário opcional mapeando o identificador da série para
                um nome legível nos eixos.

        Retorno:
            Figura Plotly com o heatmap formatado.
        """
        if not isinstance(dados, pd.DataFrame):
            raise TypeError("dados deve ser um pandas.DataFrame.")

        tabela = dados.copy()

        if colunas is not None:
            if not isinstance(colunas, (list, tuple)):
                raise TypeError("O parâmetro 'colunas' deve ser uma lista de strings.")
            ausentes = []
            for col in colunas:
                if col not in tabela.columns:
                    ausentes.append(col)
            if ausentes:
                raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(ausentes)}.")
            if len(colunas) < 2:
                raise ValueError("São necessárias pelo menos 2 colunas para o heatmap de correlação.")

            colunas_selecionadas = []
            for col in colunas:
                serie_num = pd.to_numeric(tabela[col], errors="coerce")
                if serie_num.dropna().shape[0] < 3:
                    raise ValueError(
                        f"A coluna '{col}' não possui pelo menos 3 valores numéricos válidos."
                    )
                colunas_selecionadas.append(col)
        else:
            colunas_selecionadas = []
            for col in tabela.columns:
                if str(col).lower() == "data":
                    continue
                serie_num = pd.to_numeric(tabela[col], errors="coerce")
                if serie_num.dropna().shape[0] >= 3:
                    colunas_selecionadas.append(col)

            if len(colunas_selecionadas) < 2:
                raise ValueError(
                    "São necessárias pelo menos 2 colunas numéricas válidas para o heatmap de correlação."
                )

        tabela_calculo = pd.DataFrame(index=tabela.index)
        for col in colunas_selecionadas:
            tabela_calculo[col] = pd.to_numeric(tabela[col], errors="coerce")

        matriz_corr = tabela_calculo.corr(method="pearson")

        dicionario_rotulos = rotulos if rotulos is not None else {}
        rotulos_eixos = []
        for col in matriz_corr.columns:
            rotulos_eixos.append(dicionario_rotulos.get(col, str(col)))

        figura = go.Figure(
            data=go.Heatmap(
                z=matriz_corr.values,
                x=rotulos_eixos,
                y=rotulos_eixos,
                zmin=-1,
                zmax=1,
                zmid=0,
                colorscale="RdBu_r",
                texttemplate="%{z:.2f}",
                hovertemplate="Correlação entre %{x} e %{y}: %{z:.2f}<extra></extra>",
                colorbar=dict(title="Correlação de Pearson"),
            )
        )

        figura.update_layout(
            title="Matriz de correlação entre as séries",
            xaxis=dict(tickangle=-45),
            yaxis=dict(autorange="reversed"),
        )
        return figura

