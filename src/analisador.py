"""Utilitários para processamento e análise de séries de crédito com Pandas.

A classe AnalisadorDados trabalha com dois formatos de DataFrame:

- **Formato longo** (colunas: data, modalidade, valor): usado em filtros,
  agrupamentos e gráficos de barras. É o formato esperado no construtor.

- **Formato largo** (índice = data, uma coluna por série): produzido por
  `unir_series`. Usado em correlações e gráficos de dispersão.
  Para converter de largo para longo, use `largo_para_longo`.
"""

import pandas as pd


class AnalisadorDados:
    """Analisa um DataFrame no formato longo (data, modalidade, valor)."""

    def __init__(
        self,
        dados: pd.DataFrame,
        coluna_data: str = "data",
        coluna_modalidade: str = "modalidade",
        coluna_valor: str = "valor",
    ) -> None:
        """Inicializa o analisador com um DataFrame e os nomes das colunas."""
        self._dados = dados.copy()
        self._coluna_data = coluna_data
        self._coluna_modalidade = coluna_modalidade
        self._coluna_valor = coluna_valor

    # --- propriedades de leitura ---

    @property
    def dados(self) -> pd.DataFrame:
        """Cópia do DataFrame interno."""
        return self._dados.copy()

    @property
    def coluna_data(self) -> str:
        """Nome da coluna de datas."""
        return self._coluna_data

    @property
    def coluna_modalidade(self) -> str:
        """Nome da coluna de modalidade."""
        return self._coluna_modalidade

    @property
    def coluna_valor(self) -> str:
        """Nome da coluna de valores numéricos."""
        return self._coluna_valor

    # --- métodos de processamento ---

    def filtrar(self, inicio=None, fim=None, modalidade=None) -> pd.DataFrame:
        """Filtra por intervalo de datas (inclusive) e/ou modalidade.

        inicio e fim aceitam qualquer formato reconhecido pelo pandas.
        modalidade pode ser uma string ou uma lista de strings.
        """
        resultado = self._dados.copy()

        if inicio is not None or fim is not None:
            datas = pd.to_datetime(resultado[self._coluna_data], errors="coerce")
            mascara = datas.notna()
            if inicio is not None:
                mascara = mascara & (datas >= pd.to_datetime(inicio))
            if fim is not None:
                mascara = mascara & (datas <= pd.to_datetime(fim))
            resultado = resultado.loc[mascara]

        if modalidade is not None:
            if isinstance(modalidade, (list, tuple, set)):
                modalidades = list(modalidade)
            else:
                modalidades = [modalidade]
            resultado = resultado[resultado[self._coluna_modalidade].isin(modalidades)]

        return resultado.copy()

    def tratar_nulos(self, estrategia: str = "remover", valor=None) -> pd.DataFrame:
        """Trata valores ausentes no DataFrame interno.

        Estratégias:
            'remover'   -- remove as linhas com NaN (padrão)
            'preencher' -- substitui NaN pelo argumento `valor`
            'ffill'     -- propagação para frente
            'bfill'     -- propagação para trás
        """
        if estrategia == "remover":
            self._dados = self._dados.dropna().copy()
        elif estrategia == "preencher":
            self._dados = self._dados.fillna(valor).copy()
        elif estrategia == "ffill":
            self._dados = self._dados.ffill().copy()
        elif estrategia == "bfill":
            self._dados = self._dados.bfill().copy()
        else:
            raise ValueError("Estrategia deve ser 'remover', 'preencher', 'ffill' ou 'bfill'.")
        return self._dados.copy()

    def remover_duplicados(self, subset=None) -> pd.DataFrame:
        """Remove linhas duplicadas, opcionalmente considerando apenas algumas colunas."""
        self._dados = self._dados.drop_duplicates(subset=subset).copy()
        return self._dados.copy()

    def agrupar_por_modalidade(self, operacao: str = "mean") -> pd.DataFrame:
        """Agrupa por modalidade e aplica a operacao à coluna de valor.

        Padrão: media (mean), pois as séries são taxas percentuais.
        """
        return self._agrupar([self._coluna_modalidade], operacao)

    def agrupar_por_ano(self, operacao: str = "mean") -> pd.DataFrame:
        """Agrupa por ano, derivado da coluna de data.

        Padrão: media (mean), pois as séries são taxas percentuais.
        """
        dados = self._dados.copy()
        dados[self._coluna_data] = pd.to_datetime(dados[self._coluna_data], errors="coerce")
        dados = dados.dropna(subset=[self._coluna_data])
        dados["ano"] = dados[self._coluna_data].dt.year
        return self._agrupar(["ano"], operacao, dados=dados)

    def ordenar(self, por, crescente: bool = True) -> pd.DataFrame:
        """Ordena os dados por uma ou mais colunas."""
        return self._dados.sort_values(by=por, ascending=crescente).reset_index(drop=True)

    def estatisticas_descritivas(self, coluna: str = None):
        """Retorna estatísticas descritivas gerais ou de uma coluna especifica."""
        if coluna is None:
            return self._dados.describe()
        return self._dados[coluna].describe()

    # --- métodos estáticos de transformação ---

    @staticmethod
    def unir_series(series: dict) -> pd.DataFrame:
        """Une várias séries (data, valor) em uma tabela larga: uma coluna por série.

        Parâmetros:
            series -- dicionário {nome_da_serie: DataFrame com colunas 'data' e 'valor'}

        Retorno:
            DataFrame largo com índice = data (datetime, ordenado) e uma coluna
            por série. Meses ausentes em alguma série ficam como NaN (join outer).
        """
        if not series:
            return pd.DataFrame()

        colunas = []
        for nome, tabela in series.items():
            if "data" not in tabela.columns or "valor" not in tabela.columns:
                raise ValueError(
                    f"A série '{nome}' precisa ter as colunas 'data' e 'valor'."
                )
            coluna = tabela.set_index("data")["valor"].rename(nome)
            colunas.append(coluna)

        return pd.concat(colunas, axis=1, join="outer").sort_index()

    @staticmethod
    def largo_para_longo(tabela_larga: pd.DataFrame) -> pd.DataFrame:
        """Converte uma tabela larga (índice=data, colunas=modalidades) para o formato longo.

        Devolve um DataFrame com as colunas 'data', 'modalidade' e 'valor',
        pronto para uso em filtros e agrupamentos do AnalisadorDados.
        """
        tabela = tabela_larga.reset_index()
        tabela = tabela.rename(columns={tabela.columns[0]: "data"})
        return tabela.melt(id_vars="data", var_name="modalidade", value_name="valor")

    # --- método interno de agrupamento ---

    def _agrupar(self, chaves: list, operacao: str, dados: pd.DataFrame = None) -> pd.DataFrame:
        """Aplica groupby nas chaves indicadas e devolve o resultado da operacao."""
        dados = self._dados if dados is None else dados
        operacoes_validas = {"sum", "mean", "median", "min", "max", "count"}
        if operacao not in operacoes_validas:
            raise ValueError(
                f"Operacao deve ser uma de: {', '.join(sorted(operacoes_validas))}."
            )
        agrupamento = dados.groupby(chaves, dropna=False)[self._coluna_valor]
        return getattr(agrupamento, operacao)().reset_index(name=self._coluna_valor)
