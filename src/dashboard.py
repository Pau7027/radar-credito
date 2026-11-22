"""Classe Dashboard para orquestração da interface visual no Streamlit."""

import pandas as pd
import streamlit as st

from src.analisador import AnalisadorDados
from src.indicadores import DefasagemOtima, Indicador, JurosReais
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

    def _serie_historica(self, serie_referencia: str) -> pd.Series:
        """Monta a série completa (todo o histórico) da série de referência."""
        dados = self._analisador.dados
        dados_ref = dados[dados[self._analisador.coluna_modalidade] == serie_referencia].copy()
        dados_ref["_dt"] = pd.to_datetime(
            dados_ref[self._analisador.coluna_data], errors="coerce"
        )
        dados_ref = dados_ref.dropna(subset=["_dt"]).sort_values("_dt")
        valores = pd.to_numeric(dados_ref[self._analisador.coluna_valor], errors="coerce")
        serie = pd.Series(valores.values, index=pd.DatetimeIndex(dados_ref["_dt"]))
        return serie.dropna()

    def _valor_do_indicador(self, classe, serie_historica: pd.Series, fim) -> tuple:
        """Calcula um indicador com o histórico completo e devolve (texto, ajuda).

        O indicador é lido na data final do filtro. Só funciona com indicadores
        cujo construtor recebe uma única série; os demais aparecem como '—'.
        """
        try:
            indicador = classe(serie_historica)
            resultado = indicador.calcular()
        except (TypeError, ValueError):
            return "—", None

        descricao = indicador.descrever()
        ajuda = (
            f"{descricao['descricao']} Calculado com todo o histórico da série "
            "e lido na data final selecionada."
        )
        if not isinstance(resultado, pd.Series):
            return "—", ajuda

        validos = resultado.dropna()
        ate_fim = validos.loc[:pd.to_datetime(fim)]
        if ate_fim.empty:
            return "—", ajuda

        valor = float(ate_fim.iloc[-1])
        pode_ser_negativo = bool((validos < 0).any())
        sinal = "+" if (valor > 0 and pode_ser_negativo) else ""
        texto = f"{sinal}{self._formatar_numero(valor)} {descricao['unidade']}"
        return texto, ajuda

    def _renderizar_kpis(self, inicio, fim, series_selecionadas: list[str]) -> str:
        """Renderiza o KPI de inadimplência e um cartão para cada indicador injetado."""
        idx_padrao = 0
        if "Total" in series_selecionadas:
            idx_padrao = series_selecionadas.index("Total")

        serie_referencia = st.selectbox(
            "Série de referência dos KPIs",
            options=series_selecionadas,
            index=idx_padrao,
        )

        serie_historica = self._serie_historica(serie_referencia)
        serie_ate_fim = serie_historica.loc[:pd.to_datetime(fim)]

        valor_inad = "—"
        delta_inad = None
        if not serie_ate_fim.empty:
            atual = float(serie_ate_fim.iloc[-1])
            valor_inad = f"{self._formatar_numero(atual)}%"
            if len(serie_ate_fim) >= 2:
                diferenca = atual - float(serie_ate_fim.iloc[-2])
                sinal = "+" if diferenca > 0 else ""
                delta_inad = f"{sinal}{self._formatar_numero(diferenca)} p.p."

        colunas = st.columns(1 + len(self._indicadores))
        colunas[0].metric(
            label="Inadimplência no fim do período",
            value=valor_inad,
            delta=delta_inad,
            delta_color="inverse",
            help=(
                "Taxa de inadimplência da série de referência na data final "
                "selecionada e variação em relação ao mês anterior (em p.p.)."
            ),
        )

        # Polimorfismo: todos os indicadores são tratados do mesmo jeito.
        posicao = 1
        for rotulo, classe in self._indicadores.items():
            texto, ajuda = self._valor_do_indicador(classe, serie_historica, fim)
            colunas[posicao].metric(label=rotulo, value=texto, help=ajuda)
            posicao += 1

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
            tabela_larga = self._juntar_macro(tabela_larga)
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
                    fig_heat = self._visualizador.grafico_heatmap_correlacao(
                        tabela_larga[colunas_validas],
                        rotulos={"selic": "Selic meta (% a.a.)", "ipca": "IPCA (% a.m.)"},
                    )
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
            self._renderizar_juros_reais(inicio, fim)
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
    
    
    def _macro_com_indice(self) -> pd.DataFrame:
        """Devolve as séries macro com índice de datas (ou DataFrame vazio)."""
        if self._series_macro is None:
            return pd.DataFrame()
        macro = self._series_macro.copy()
        if not isinstance(macro.index, pd.DatetimeIndex):
            if "data" in macro.columns:
                macro = macro.set_index(pd.to_datetime(macro["data"]))
            else:
                macro.index = pd.to_datetime(macro.index)
        return macro.sort_index()

    def _juntar_macro(self, tabela_larga: pd.DataFrame) -> pd.DataFrame:
        """Acrescenta Selic e IPCA (se existirem) à tabela larga, pelas datas."""
        macro = self._macro_com_indice()
        colunas = []
        for nome in ("selic", "ipca"):
            if nome in macro.columns:
                colunas.append(nome)
        if not colunas:
            return tabela_larga
        return tabela_larga.join(macro[colunas], how="left")

    def _renderizar_juros_reais(self, inicio, fim) -> None:
        """Mostra os juros reais (Fisher) quando Selic e IPCA estão disponíveis."""
        macro = self._macro_com_indice()
        if "selic" not in macro.columns or "ipca" not in macro.columns:
            return

        st.markdown("### Juros reais (equação de Fisher)")
        try:
            selic = pd.to_numeric(macro["selic"], errors="coerce").dropna()
            ipca = pd.to_numeric(macro["ipca"], errors="coerce").dropna()
            juros = JurosReais(selic, ipca).calcular().dropna()
        except ValueError as erro:
            st.warning(str(erro))
            return

        juros = juros.loc[pd.to_datetime(inicio):pd.to_datetime(fim)]
        if juros.empty:
            st.info("Não há juros reais calculados para o período selecionado.")
            return

        tabela = pd.DataFrame(
            {"data": juros.index, "modalidade": "Juros reais ex-post", "valor": juros.values}
        )
        try:
            figura = self._visualizador.grafico_linhas(
                tabela,
                titulo="Juros reais (Selic meta descontada do IPCA em 12 meses)",
                rotulo_y="Juros reais (% a.a.)",
                titulo_legenda="Indicador",
            )
            st.plotly_chart(figura, width="stretch")
        except ValueError as erro:
            st.warning(str(erro))
        st.caption(
            "Juros reais ex-post: (1 + Selic) / (1 + IPCA acumulado em 12 meses) - 1, "
            "usando a Selic meta no fim de cada mês."
        )
        # TODO (issue #9): texto interpretativo    
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
