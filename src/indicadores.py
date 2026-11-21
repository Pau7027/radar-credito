"""Módulo de indicadores financeiros e estatísticos para séries de crédito.

# TODO: Obtenção das séries Selic (código 432, diária com limite de 10 anos) e
# IPCA (código 433, variação mensal) via API do BCB será integrada em etapa futura.
"""

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd


class Indicador(ABC):
    """Classe base abstrata para indicadores econômicos e estatísticos de crédito."""

    def __init__(self, nome: str, descricao: str, unidade: str) -> None:
        """Inicializa o indicador com metadados descritivos."""
        self._nome = nome
        self._descricao = descricao
        self._unidade = unidade

    @property
    def nome(self) -> str:
        """Nome do indicador."""
        return self._nome

    @property
    def descricao(self) -> str:
        """Descrição textual do indicador."""
        return self._descricao

    @property
    def unidade(self) -> str:
        """Unidade de medida do indicador."""
        return self._unidade

    @staticmethod
    def _validar_serie(serie: pd.Series, nome_parametro: str = "serie") -> pd.Series:
        """Valida se o parâmetro é uma Series válida com DatetimeIndex e valores numéricos."""
        if not isinstance(serie, pd.Series):
            raise TypeError(
                f"O parâmetro '{nome_parametro}' deve ser uma instância de pandas.Series."
            )
        if serie.empty:
            raise ValueError(
                f"A série '{nome_parametro}' não pode estar vazia."
            )
        if not isinstance(serie.index, pd.DatetimeIndex):
            raise TypeError(
                f"O índice da série '{nome_parametro}' deve ser do tipo DatetimeIndex."
            )
        if not pd.api.types.is_numeric_dtype(serie):
            raise TypeError(
                f"Os valores da série '{nome_parametro}' devem ser numéricos."
            )
        return serie.sort_index().copy()

    @abstractmethod
    def calcular(self):
        """Calcula e retorna a série ou tabela do indicador."""
        pass

    def valor_atual(self):
        """Retorna o último valor não nulo do indicador calculado."""
        resultado = self.calcular()
        if isinstance(resultado, pd.Series):
            serie_valida = resultado.dropna()
            if not serie_valida.empty:
                return float(serie_valida.iloc[-1])
            return float("nan")
        return resultado

    def descrever(self) -> dict:
        """Retorna metadados do indicador em formato de dicionário."""
        return {
            "nome": self._nome,
            "descricao": self._descricao,
            "unidade": self._unidade,
        }

    def __repr__(self) -> str:
        """Representação textual do indicador."""
        return f"<{self.__class__.__name__}(nome='{self._nome}', unidade='{self._unidade}')>"


class VariacaoVsMedia12m(Indicador):
    """Mede o desvio da taxa atual em relação à média dos 12 meses anteriores.

    O que mede:
        Quanto a taxa de inadimplência do mês atual está acima ou abaixo
        do padrão histórico recente dos últimos 12 meses.

    Fórmula:
        variacao_t = x_t - media(x_{t-12}, ..., x_{t-1})
        Implementada como: serie - serie.rolling(12).mean().shift(1)

    Unidade:
        Pontos percentuais (p.p.).

    Como interpretar:
        - Valores positivos indicam aceleração recente da inadimplência (piora).
        - Valores negativos indicam arrefecimento ou alívio (melhora).
        - Valores próximos a zero indicam estabilidade em relação ao ano recente.

    Limitação:
        Exige 12 meses de histórico prévio (os 12 primeiros meses resultam em NaN)
        e não diferencia se a oscilação decorre de choque atípico ou tendência estrutural.
    """

    def __init__(self, serie: pd.Series) -> None:
        """Inicializa o indicador com a série temporal de inadimplência."""
        super().__init__(
            nome="Variação vs. Média de 12 Meses",
            descricao="Desvio da taxa de inadimplência em relação à média dos 12 meses anteriores.",
            unidade="p.p.",
        )
        self._serie = self._validar_serie(serie, "serie")

    @property
    def serie(self) -> pd.Series:
        """Cópia da série temporal de entrada."""
        return self._serie.copy()

    def calcular(self) -> pd.Series:
        """Calcula a variação mensal em relação à média móvel defasada de 12 meses."""
        media_movel_12m = self._serie.rolling(12).mean().shift(1)
        return self._serie - media_movel_12m


class Volatilidade12m(Indicador):
    """Mede a volatilidade e o risco de oscilação em janela móvel de 12 meses.

    O que mede:
        A dispersão e a incerteza da taxa de inadimplência medida pelo
        desvio padrão amostral dos últimos 12 meses.

    Fórmula:
        vol_t = desvio_padrao(x_{t-11}, ..., x_t) com ddof=1
        Implementada como: serie.rolling(12).std()

    Unidade:
        Pontos percentuais (p.p.).

    Como interpretar:
        - Valores elevados indicam períodos de instabilidade e oscilações bruscas.
        - Valores baixos ou próximos a zero indicam trajetórias previsíveis e estáveis.
        - Uma série estritamente constante resulta em volatilidade igual a zero.

    Limitação:
        Por ser calculada em pontos percentuais absolutos, não permite comparação
        direta de volatilidade entre modalidades de patamares médios muito distintos
        (para tal comparação, o coeficiente de variação relativo seria mais adequado).
    """

    def __init__(self, serie: pd.Series) -> None:
        """Inicializa o indicador com a série temporal de inadimplência."""
        super().__init__(
            nome="Volatilidade Móvel de 12 Meses",
            descricao="Desvio padrão amostral móvel de 12 meses da taxa de inadimplência.",
            unidade="p.p.",
        )
        self._serie = self._validar_serie(serie, "serie")

    @property
    def serie(self) -> pd.Series:
        """Cópia da série temporal de entrada."""
        return self._serie.copy()

    def calcular(self) -> pd.Series:
        """Calcula o desvio padrão amostral móvel em janela de 12 meses."""
        return self._serie.rolling(12).std()
