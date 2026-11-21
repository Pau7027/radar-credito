"""Classe Dashboard para orquestração da interface visual no Streamlit."""

import pandas as pd
import streamlit as st

from src.analisador import AnalisadorDados
from src.indicadores import Indicador
from src.visualizador import Visualizador


class Dashboard:
    """Coordena e renderiza o painel interativo Streamlit do RadarCrédito.

    Princípios SOLID aplicados:
        - S (Single Responsibility): A classe Dashboard responsabiliza-se
          estritamente pela orquestração visual e layout da interface com o
          usuário no Streamlit, delegando cálculos matemáticos, transformações
          de dados e plotagem para outras classes especializadas.
        - O (Open/Closed): Indicadores econômicos são injetados como tipos em um
          dicionário extensível, permitindo adicionar novos indicadores sem
          alterar o código da classe Dashboard.
        - D (Dependency Inversion): Depende de abstrações (classe base Indicador)
          e recebe AnalisadorDados e Visualizador por injeção de dependência no
          construtor, sem instanciar fontes de dados ou serviços externos.
    """

    def __init__(
        self,
        analisador: AnalisadorDados,
        indicadores: dict[str, type[Indicador]],
        visualizador: Visualizador | type[Visualizador],
        titulo: str = "RadarCrédito",
        descricao: str = (
            "Painel interativo de análise da inadimplência e risco de crédito no Brasil "
            "com dados do Banco Central (API SGS)."
        ),
        series_folha: list[str] | None = None,
        series_macro: pd.DataFrame | None = None,
    ) -> None:
        """Inicializa o Dashboard com suas dependências e configurações.

        Parâmetros:
            analisador: Instância de AnalisadorDados no formato longo.
            indicadores: Dicionário {rótulo: classe_de_indicador} herdando de Indicador.
                Exemplo:
                    {
                        "Variação vs. média de 12 meses": VariacaoVsMedia12m,
                        "Volatilidade (12 meses)": Volatilidade12m,
                        "Z-score": ZScore,
                    }
            visualizador: Instância ou classe Visualizador para geração de gráficos.
            titulo: Título principal exibido no cabeçalho do painel.
            descricao: Texto descritivo exibido logo abaixo do título.
            series_folha: Lista opcional de séries desagregadas sem sobreposição
                para uso nos gráficos de ranking e treemap da aba Comparação.
            series_macro: DataFrame mensal opcional contendo séries macroeconômicas
                (como a taxa 'selic').
        """
        if not isinstance(analisador, AnalisadorDados):
            raise TypeError("O parâmetro 'analisador' deve ser uma instância de AnalisadorDados.")

        if not isinstance(indicadores, dict):
            raise TypeError("O parâmetro 'indicadores' deve ser um dicionário.")

        if len(indicadores) == 0:
            raise ValueError("O parâmetro 'indicadores' não pode ser um dicionário vazio.")

        for rotulo, classe in indicadores.items():
            if not isinstance(classe, type) or not issubclass(classe, Indicador):
                raise TypeError(
                    f"O valor de '{rotulo}' em 'indicadores' deve ser uma classe que herda de Indicador."
                )

        if series_folha is not None:
            if not isinstance(series_folha, (list, tuple, set)):
                raise TypeError("O parâmetro 'series_folha' deve ser uma lista ou tupla.")
            modalidades_dados = set(
                analisador.dados[analisador.coluna_modalidade].dropna().unique()
            )
            ausentes = []
            for s in series_folha:
                if s not in modalidades_dados:
                    ausentes.append(s)
            if ausentes:
                raise ValueError(
                    f"As seguintes séries em 'series_folha' não estão presentes nos dados: {', '.join(ausentes)}."
                )

        if series_macro is not None and not isinstance(series_macro, pd.DataFrame):
            raise TypeError("O parâmetro 'series_macro' deve ser um pandas.DataFrame.")

        if not isinstance(titulo, str):
            raise TypeError("O parâmetro 'titulo' deve ser uma string.")

        if not isinstance(descricao, str):
            raise TypeError("O parâmetro 'descricao' deve ser uma string.")

        self._analisador = analisador
        self._indicadores = dict(indicadores)
        self._visualizador = visualizador
        self._titulo = titulo
        self._descricao = descricao
        self._series_folha = list(series_folha) if series_folha is not None else None
        self._series_macro = series_macro.copy() if series_macro is not None else None

    # --- Propriedades de leitura ---

    @property
    def analisador(self) -> AnalisadorDados:
        """Instância do analisador de dados interno."""
        return self._analisador

    @property
    def indicadores(self) -> dict[str, type[Indicador]]:
        """Dicionário de classes de indicadores configuradas."""
        return self._indicadores.copy()

    @property
    def visualizador(self) -> Visualizador | type[Visualizador]:
        """Objeto ou classe visualizadora de gráficos."""
        return self._visualizador

    @property
    def titulo(self) -> str:
        """Título do painel."""
        return self._titulo

    @property
    def descricao(self) -> str:
        """Descrição textual do painel."""
        return self._descricao

    @property
    def series_folha(self) -> list[str] | None:
        """Lista de modalidades folha sem sobreposição."""
        return list(self._series_folha) if self._series_folha is not None else None

    @property
    def series_macro(self) -> pd.DataFrame | None:
        """DataFrame com séries macroeconômicas ou None."""
        return self._series_macro.copy() if self._series_macro is not None else None

    # --- Método público principal ---

    def renderizar(self) -> None:
        """Orquestra e renderiza a estrutura completa do painel no Streamlit."""
        self._renderizar_cabecalho()
        inicio, fim, series_selecionadas = self._renderizar_filtros()
        serie_referencia = self._renderizar_kpis(inicio, fim, series_selecionadas)
        self._renderizar_abas(inicio, fim, series_selecionadas, serie_referencia)

    # --- Métodos privados de apoio ---

    def _renderizar_cabecalho(self) -> None:
        """Renderiza o título principal e a descrição do projeto."""
        st.title(self._titulo)
        st.caption(self._descricao)

    def _renderizar_filtros(self) -> tuple:
        """Renderiza filtros na barra lateral e devolve (inicio, fim, series_selecionadas)."""
        dados = self._analisador.dados
        datas = pd.to_datetime(dados[self._analisador.coluna_data], errors="coerce").dropna()
        if datas.empty:
            st.error("Não há datas válidas disponíveis nos dados.")
            st.stop()

        primeira_data = datas.min().date()
        ultima_data = datas.max().date()

        todas_series = list(dados[self._analisador.coluna_modalidade].dropna().unique())

        st.sidebar.header("Filtros")
        inicio = st.sidebar.date_input(
            "Data inicial",
            value=primeira_data,
            min_value=primeira_data,
            max_value=ultima_data,
        )
        fim = st.sidebar.date_input(
            "Data final",
            value=ultima_data,
            min_value=primeira_data,
            max_value=ultima_data,
        )
        series_selecionadas = st.sidebar.multiselect(
            "Séries",
            options=todas_series,
            default=todas_series,
        )

        if inicio > fim:
            st.warning("A data inicial deve ser anterior ou igual à data final.")
            st.stop()

        if not series_selecionadas:
            st.warning("Selecione ao menos uma série.")
            st.stop()

        filtrados = self._analisador.filtrar(
            inicio=inicio, fim=fim, modalidade=series_selecionadas
        )
        if filtrados.empty:
            st.info("Não há registros para os filtros selecionados.")
            st.stop()

        return inicio, fim, series_selecionadas

    def _encontrar_classe_indicador(self, nome_classe: str):
        """Localiza a classe de indicador registrada correspondente ao nome informado."""
        for rotulo, classe in self._indicadores.items():
            if classe.__name__ == nome_classe:
                return classe
        return None

    def _renderizar_kpis(
        self, inicio, fim, series_selecionadas: list[str]
    ) -> str:
        """Calcula e renderiza os 4 cartões de métricas principais."""
        idx_padrao = 0
        if "Total" in series_selecionadas:
            idx_padrao = series_selecionadas.index("Total")

        serie_referencia = st.selectbox(
            "Série de referência dos KPIs",
            options=series_selecionadas,
            index=idx_padrao,
        )

        dados_completos = self._analisador.dados
        dados_ref = dados_completos[
            dados_completos[self._analisador.coluna_modalidade] == serie_referencia
        ].copy()
        dados_ref["_dt"] = pd.to_datetime(
            dados_ref[self._analisador.coluna_data], errors="coerce"
        )
        dados_ref = dados_ref.dropna(subset=["_dt"]).sort_values("_dt")

        serie_historica = pd.Series(
            pd.to_numeric(dados_ref[self._analisador.coluna_valor], errors="coerce").values,
            index=pd.DatetimeIndex(dados_ref["_dt"]),
        ).dropna()

        serie_ate_fim = serie_historica.loc[:pd.to_datetime(fim)].dropna()

        # KPI 1: Inadimplência no fim do período
        if not serie_ate_fim.empty:
            val_atual = float(serie_ate_fim.iloc[-1])
            val_kpi1 = f"{self._formatar_numero(val_atual)}%"
            if len(serie_ate_fim) >= 2:
                val_anterior = float(serie_ate_fim.iloc[-2])
                diff = val_atual - val_anterior
                sinal = "+" if diff > 0 else ""
                delta_kpi1 = f"{sinal}{self._formatar_numero(diff)} p.p."
            else:
                delta_kpi1 = None
        else:
            val_kpi1 = "—"
            delta_kpi1 = None

        # KPI 2: Variação vs. média de 12 meses
        val_kpi2 = "—"
        classe_var = self._encontrar_classe_indicador("VariacaoVsMedia12m")
        if classe_var is not None and len(serie_historica) >= 2:
            try:
                indicador_var = classe_var(serie_historica)
                res_var = indicador_var.calcular().loc[:pd.to_datetime(fim)].dropna()
                if not res_var.empty:
                    v2 = float(res_var.iloc[-1])
                    sinal2 = "+" if v2 > 0 else ""
                    val_kpi2 = f"{sinal2}{self._formatar_numero(v2)} p.p."
            except ValueError:
                val_kpi2 = "—"

        # KPI 3: Volatilidade (12 meses)
        val_kpi3 = "—"
        classe_vol = self._encontrar_classe_indicador("Volatilidade12m")
        if classe_vol is not None and len(serie_historica) >= 2:
            try:
                indicador_vol = classe_vol(serie_historica)
                res_vol = indicador_vol.calcular().loc[:pd.to_datetime(fim)].dropna()
                if not res_vol.empty:
                    v3 = float(res_vol.iloc[-1])
                    val_kpi3 = f"{self._formatar_numero(v3)} p.p."
            except ValueError:
                val_kpi3 = "—"

        # KPI 4: Z-score histórico
        val_kpi4 = "—"
        classe_z = self._encontrar_classe_indicador("ZScore")
        if classe_z is not None and len(serie_historica) >= 2:
            try:
                indicador_z = classe_z(serie_historica)
                res_z = indicador_z.calcular().loc[:pd.to_datetime(fim)].dropna()
                if not res_z.empty:
                    v4 = float(res_z.iloc[-1])
                    sinal4 = "+" if v4 > 0 else ""
                    val_kpi4 = f"{sinal4}{self._formatar_numero(v4)}"
            except ValueError:
                val_kpi4 = "—"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            label="Inadimplência no fim do período",
            value=val_kpi1,
            delta=delta_kpi1,
            delta_color="inverse",
            help=(
                "Taxa de inadimplência da série de referência na data final selecionada "
                "e variação em relação ao mês anterior (em pontos percentuais)."
            ),
        )
        col2.metric(
            label="Variação vs. média de 12m",
            value=val_kpi2,
            help=(
                "Diferença em pontos percentuais entre a taxa atual e a média dos "
                "12 meses anteriores. Exige ao menos 12 meses de histórico prévio."
            ),
        )
        col3.metric(
            label="Volatilidade (12 meses)",
            value=val_kpi3,
            help=(
                "Desvio padrão amostral móvel de 12 meses da taxa de inadimplência "
                "em pontos percentuais. Exige ao menos 12 meses de histórico."
            ),
        )
        col4.metric(
            label="Z-score histórico",
            value=val_kpi4,
            help=(
                "Número de desvios padrão que a taxa do mês final está afastada "
                "da média histórica. Utiliza a média e o desvio padrão de todo o "
                "histórico da série, e não apenas do período filtrado."
            ),
        )

        return serie_referencia

    def _renderizar_abas(
        self,
        inicio,
        fim,
        series_selecionadas: list[str],
        serie_referencia: str,
    ) -> None:
        """Renderiza as abas com visualizações dinâmicas e tabela de dados."""
        dados_filtrados = self._analisador.filtrar(
            inicio=inicio, fim=fim, modalidade=series_selecionadas
        )

        aba_evolucao, aba_comparacao, aba_correlacoes, aba_tabela = st.tabs(
            ["Evolução", "Comparação", "Correlações", "Tabela de dados"]
        )

        with aba_evolucao:
            try:
                fig_linhas = self._visualizador.grafico_linhas(dados_filtrados)
                st.plotly_chart(fig_linhas, width="stretch")
            except ValueError as erro:
                st.warning(str(erro))
            # TODO (issue #9): texto interpretativo

        with aba_comparacao:
            series_folha_validas = []
            if self._series_folha is not None:
                for s in self._series_folha:
                    if s in series_selecionadas:
                        series_folha_validas.append(s)

            if not series_folha_validas:
                st.info(
                    "Nenhuma modalidade desagregada (série folha) selecionada para comparação. "
                    "Total, Pessoa física e Pessoa jurídica são agregadas e não entram nesta comparação."
                )
            else:
                dados_folha = dados_filtrados[
                    dados_filtrados[self._analisador.coluna_modalidade].isin(series_folha_validas)
                ]
                try:
                    fig_barras = self._visualizador.grafico_barras(dados_folha)
                    st.plotly_chart(fig_barras, width="stretch")
                    # TODO (issue #9): texto interpretativo

                    fig_treemap = self._visualizador.grafico_treemap(dados_folha)
                    st.plotly_chart(fig_treemap, width="stretch")
                    st.caption(
                        "No treemap, a área compara taxas médias de inadimplência; "
                        "não representa volume de crédito nem participação de mercado."
                    )
                    # TODO (issue #9): texto interpretativo
                except ValueError as erro:
                    st.warning(str(erro))

        with aba_correlacoes:
            tabela_larga = self._tabela_larga(
                dados_filtrados,
                coluna_data=self._analisador.coluna_data,
                coluna_modalidade=self._analisador.coluna_modalidade,
                coluna_valor=self._analisador.coluna_valor,
            )

            colunas_validas = []
            for col in tabela_larga.columns:
                if tabela_larga[col].dropna().shape[0] >= 3:
                    colunas_validas.append(col)

            if len(colunas_validas) < 2:
                st.info(
                    "São necessárias pelo menos 2 séries com no mínimo 3 observações contemporâneas "
                    "no período filtrado para calcular correlações."
                )
            else:
                try:
                    fig_heat = self._visualizador.grafico_heatmap_correlacao(tabela_larga)
                    st.plotly_chart(fig_heat, width="stretch")
                    # TODO (issue #9): texto interpretativo
                except ValueError as erro:
                    st.warning(str(erro))

            # Relação com a taxa Selic
            if self._series_macro is not None and "selic" in self._series_macro.columns:
                try:
                    macro_df = self._series_macro.copy()
                    if not isinstance(macro_df.index, pd.DatetimeIndex) and "data" in macro_df.columns:
                        macro_df = macro_df.set_index(pd.to_datetime(macro_df["data"]))
                    elif not isinstance(macro_df.index, pd.DatetimeIndex):
                        macro_df.index = pd.to_datetime(macro_df.index)

                    serie_selic = (
                        pd.to_numeric(macro_df["selic"], errors="coerce").dropna().sort_index()
                    )

                    dados_ref = dados_filtrados[
                        dados_filtrados[self._analisador.coluna_modalidade] == serie_referencia
                    ].copy()
                    dados_ref["_dt"] = pd.to_datetime(
                        dados_ref[self._analisador.coluna_data], errors="coerce"
                    )
                    dados_ref = dados_ref.dropna(subset=["_dt"]).sort_values("_dt")
                    serie_ref = pd.Series(
                        pd.to_numeric(dados_ref[self._analisador.coluna_valor], errors="coerce").values,
                        index=pd.DatetimeIndex(dados_ref["_dt"]),
                    ).dropna()

                    from src.indicadores import DefasagemOtima

                    indicador_def = DefasagemOtima(serie_selic, serie_ref)
                    def_otima = indicador_def.defasagem_otima
                    corr_otima = indicador_def.correlacao_otima

                    st.markdown("### Relação entre Selic e Inadimplência")
                    corr_fmt = self._formatar_numero(corr_otima)
                    st.write(
                        f"**Defasagem ótima encontrada:** {def_otima} meses "
                        f"(correlação de Pearson: {corr_fmt})"
                    )

                    slider_def = st.slider(
                        "Defasagem da Selic (meses)",
                        min_value=0,
                        max_value=24,
                        value=def_otima,
                    )

                    df_macro_par = pd.DataFrame(
                        {"selic": serie_selic, "inadimplencia": serie_ref}
                    ).dropna()

                    fig_disp = self._visualizador.grafico_dispersao_defasada(
                        df_macro_par,
                        coluna_x="selic",
                        coluna_y="inadimplencia",
                        defasagem=slider_def,
                        rotulo_x="Selic meta (% a.a.)",
                        rotulo_y=f"Inadimplência - {serie_referencia} (%)",
                    )
                    st.plotly_chart(fig_disp, width="stretch")
                    # TODO (issue #9): texto interpretativo
                except ValueError as erro:
                    st.warning(str(erro))
            else:
                st.info(
                    "A relação entre Selic e inadimplência será exibida quando a série da Selic "
                    "for integrada ao projeto."
                )
                # TODO (issue #9): texto interpretativo

        with aba_tabela:
            dados_tabela = dados_filtrados.copy()
            dados_tabela["_dt"] = pd.to_datetime(
                dados_tabela[self._analisador.coluna_data], errors="coerce"
            )
            dados_tabela = dados_tabela.sort_values(
                by=["_dt", self._analisador.coluna_modalidade], ascending=[False, True]
            )

            textos_data = []
            for d in dados_tabela["_dt"]:
                if pd.notna(d):
                    textos_data.append(d.strftime("%m/%Y"))
                else:
                    textos_data.append("")

            textos_valor = []
            for v in pd.to_numeric(
                dados_tabela[self._analisador.coluna_valor], errors="coerce"
            ):
                if pd.notna(v):
                    textos_valor.append(f"{self._formatar_numero(v)}%")
                else:
                    textos_valor.append("—")

            df_exibicao = pd.DataFrame(
                {
                    "Data": textos_data,
                    "Série": dados_tabela[self._analisador.coluna_modalidade].astype(str).values,
                    "Taxa de inadimplência (%)": textos_valor,
                }
            )

            st.dataframe(df_exibicao, width="stretch", hide_index=True)
            st.caption(f"Total de registros exibidos: {len(df_exibicao)}.")

    @staticmethod
    def _tabela_larga(
        dados: pd.DataFrame,
        coluna_data: str = "data",
        coluna_modalidade: str = "modalidade",
        coluna_valor: str = "valor",
    ) -> pd.DataFrame:
        """Converte dados no formato longo para tabela larga indexada por data."""
        tabela = dados.pivot_table(
            index=coluna_data,
            columns=coluna_modalidade,
            values=coluna_valor,
            aggfunc="mean",
        )
        tabela.index = pd.to_datetime(tabela.index)
        return tabela.sort_index()

    @staticmethod
    def _formatar_numero(valor: float | int | None, casas: int = 2) -> str:
        """Formata um valor numérico com vírgula decimal e casas decimais fixas."""
        if valor is None or pd.isna(valor):
            return "—"
        formato = f"{{:.{casas}f}}"
        return formato.format(float(valor)).replace(".", ",")
