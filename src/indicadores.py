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



class ZScore(Indicador):
    """Calcula o Z-score da taxa de inadimplência (global ou móvel).

    O que mede:
        Quantos desvios padrão uma observação mensal está afastada da média
        histórica (global de todo o período ou móvel em janela fixada).

    Fórmula:
        z_t = (x_t - mu) / sigma
        Onde mu e sigma sao calculados com ddof=1 (amostral).
        Se janela for informada, utiliza media e desvio padrao moveis dessa janela.

    Unidade:
        Desvios padrão (adimensional).

    Como interpretar:
        - Valores entre -1 e +1 representam oscilações dentro do padrão normal.
        - |z| > 2 indica meses atípicos de estresse severo ou alívio incomum.
        - Se o desvio padrão for zero, retorna NaN sem levantar exceção.

    Limitação:
        O z-score global incorpora dados futuros de todo o período amostral e
        pressupõe que a distribuição dos dados seja aproximadamente simétrica.
    """

    def __init__(self, serie: pd.Series, janela: int | None = None) -> None:
        """Inicializa o indicador com a série e opcionalmente uma janela móvel."""
        super().__init__(
            nome="Z-Score da Inadimplência",
            descricao="Afastamento padronizado em relação à média em unidades de desvio padrão.",
            unidade="desvios padrão",
        )
        self._serie = self._validar_serie(serie, "serie")
        if janela is not None:
            if not isinstance(janela, int) or isinstance(janela, bool) or janela <= 1:
                raise ValueError("O parâmetro 'janela' deve ser um número inteiro maior que 1.")
        self._janela = janela

    @property
    def serie(self) -> pd.Series:
        """Cópia da série temporal de entrada."""
        return self._serie.copy()

    @property
    def janela(self) -> int | None:
        """Tamanho da janela móvel ou None para z-score global."""
        return self._janela

    def calcular(self) -> pd.Series:
        """Calcula a série padronizada de Z-score."""
        if self._janela is None:
            media = float(self._serie.mean())
            desvio = float(self._serie.std(ddof=1))
            if pd.isna(desvio) or desvio == 0:
                return pd.Series(np.nan, index=self._serie.index)
            return (self._serie - media) / desvio
        else:
            media_movel = self._serie.rolling(self._janela).mean()
            desvio_movel = self._serie.rolling(self._janela).std(ddof=1)
            desvio_seguro = desvio_movel.replace(0, np.nan)
            return (self._serie - media_movel) / desvio_seguro



class JurosReais(Indicador):
    """Calcula a taxa de juros real ex-post anualizada pela equação de Fisher.

    O que mede:
        A taxa de remuneração do capital descontada a inflação acumulada em 12 meses,
        revelando o custo real do crédito na economia brasileira.

    Fórmula:
        Equação de Fisher: (1 + i) = (1 + r) * (1 + pi_12)
        Logo: r = ((1 + i / 100) / (1 + pi_12) - 1) * 100
        Onde:
            - i: taxa Selic meta nominal (% ao ano).
            - pi_12: inflação acumulada em 12 meses composta = prod_{m=0..11}(1 + ipca_m / 100) - 1.

    Unidade:
        Percentual ao ano (% a.a.).

    Como interpretar:
        - Valores positivos elevados indicam política monetária restritiva com
          encarecimento real das parcelas e maior pressão sobre a inadimplência.
        - Valores baixos ou negativos indicam juros reais brandos ou expansionistas.

    Limitação:
        Mede a taxa de juros real ex-post (baseada na inflação pretérita realizada),
        enquanto as decisões econômicas dependem prioritariamente das expectativas
        inflacionárias futuras (juro real ex-ante do Boletim Focus).
    """

    def __init__(self, selic: pd.Series, ipca_mensal: pd.Series) -> None:
        """Inicializa o indicador com as séries de Selic (% a.a.) e IPCA mensal (% a.m.)."""
        super().__init__(
            nome="Taxa de Juros Reais (Equação de Fisher)",
            descricao="Taxa Selic nominal descontada da inflação IPCA acumulada em 12 meses.",
            unidade="% a.a.",
        )
        self._selic = self._validar_serie(selic, "selic")
        self._ipca_mensal = self._validar_serie(ipca_mensal, "ipca_mensal")

    @property
    def selic(self) -> pd.Series:
        """Cópia da série temporal da taxa Selic."""
        return self._selic.copy()

    @property
    def ipca_mensal(self) -> pd.Series:
        """Cópia da série temporal do IPCA mensal."""
        return self._ipca_mensal.copy()

    def calcular(self) -> pd.Series:
        """Calcula a série de juros reais ex-post em % ao ano."""
        fatores_ipca = 1.0 + self._ipca_mensal / 100.0
        valores_ipca_12m = []
        n_registros = len(fatores_ipca)

        for i in range(n_registros):
            if i < 11:
                valores_ipca_12m.append(np.nan)
            else:
                janela = fatores_ipca.iloc[i - 11 : i + 1]
                fator_acumulado = 1.0
                for fator in janela:
                    fator_acumulado *= float(fator)
                valores_ipca_12m.append(fator_acumulado - 1.0)

        ipca_12m = pd.Series(valores_ipca_12m, index=self._ipca_mensal.index)
        tabela = pd.DataFrame({"selic": self._selic, "ipca_12m": ipca_12m})

        fator_nominal = 1.0 + tabela["selic"] / 100.0
        fator_inflacao = 1.0 + tabela["ipca_12m"]
        juros_reais = (fator_nominal / fator_inflacao - 1.0) * 100.0

        return juros_reais



class DefasagemOtima(Indicador):
    """Calcula a defasagem temporal de maior correlação entre a Selic e a inadimplência.

    O que mede:
        O tempo de transmissão (em meses de atraso) no qual a taxa Selic apresenta
        a maior associação linear com a taxa de inadimplência da carteira de crédito.

    Fórmula:
        Para cada defasagem k em [0, defasagem_maxima]:
            corr_k = correlacao_pearson(Selic_{t-k}, Inadimplencia_t)
        A defasagem ótima k* é o valor de k que maximiza |corr_k|.

    Unidade:
        Meses (para a defasagem) e índice adimensional de Pearson entre -1 e +1 (para a correlação).

    Como interpretar:
        - Uma correlação positiva em defasagem k indica que aumentos da Selic tendem
          a ser sucedidos por elevação da inadimplência k meses adiante.
        - O valor_atual() devolve a correlação ótima encontrada.

    Limitação:
        Correlação linear não implica relação de causa e efeito; duas séries com
        tendências macroeconômicas concomitantes podem apresentar correlação espúria;
        defasagens elevadas contam com menor número de pares de observações sincronizadas.
    """

    def __init__(
        self,
        selic: pd.Series,
        inadimplencia: pd.Series,
        defasagem_maxima: int = 24,
    ) -> None:
        """Inicializa o indicador com as séries de Selic, inadimplência e defasagem máxima."""
        super().__init__(
            nome="Defasagem Ótima Selic-Inadimplência",
            descricao="Identifica a defasagem temporal com maior correlação entre Selic e inadimplência.",
            unidade="meses",
        )
        self._selic = self._validar_serie(selic, "selic")
        self._inadimplencia = self._validar_serie(inadimplencia, "inadimplencia")
        if not isinstance(defasagem_maxima, int) or isinstance(defasagem_maxima, bool) or defasagem_maxima < 0:
            raise ValueError(
                "O parâmetro 'defasagem_maxima' deve ser um número inteiro não negativo."
            )
        self._defasagem_maxima = defasagem_maxima
        self._defasagem_otima = None
        self._correlacao_otima = None
        self._resultado_tabela = None

    @property
    def selic(self) -> pd.Series:
        """Cópia da série temporal da taxa Selic."""
        return self._selic.copy()

    @property
    def inadimplencia(self) -> pd.Series:
        """Cópia da série temporal da taxa de inadimplência."""
        return self._inadimplencia.copy()

    @property
    def defasagem_maxima(self) -> int:
        """Limite máximo de meses de defasagem testados."""
        return self._defasagem_maxima

    @property
    def defasagem_otima(self) -> int:
        """Número de meses de defasagem que maximiza o módulo da correlação."""
        if self._defasagem_otima is None:
            self.calcular()
        return self._defasagem_otima

    @property
    def correlacao_otima(self) -> float:
        """Coeficiente de correlação de Pearson na defasagem ótima (com sinal original)."""
        if self._correlacao_otima is None:
            self.calcular()
        return self._correlacao_otima

    def valor_atual(self) -> float:
        """Sobrescreve o método base para retornar a correlação ótima encontrada."""
        return self.correlacao_otima

    def calcular(self) -> pd.DataFrame:
        """Calcula a correlação de Pearson para cada defasagem de 0 até defasagem_maxima."""
        linhas = []
        maior_modulo = -1.0
        otima_def = 0
        otima_corr = np.nan

        for k in range(self._defasagem_maxima + 1):
            selic_defasada = self._selic.shift(k)
            tabela_par = pd.DataFrame(
                {"selic": selic_defasada, "inadimplencia": self._inadimplencia}
            ).dropna()

            n_observacoes = len(tabela_par)

            if n_observacoes < 3:
                correlacao = np.nan
            else:
                desvio_selic = tabela_par["selic"].std(ddof=1)
                desvio_inad = tabela_par["inadimplencia"].std(ddof=1)
                if desvio_selic == 0 or desvio_inad == 0 or pd.isna(desvio_selic) or pd.isna(desvio_inad):
                    correlacao = np.nan
                else:
                    correlacao = float(tabela_par["selic"].corr(tabela_par["inadimplencia"]))

            if pd.notna(correlacao):
                modulo_atual = abs(correlacao)
                if modulo_atual > maior_modulo:
                    maior_modulo = modulo_atual
                    otima_def = k
                    otima_corr = correlacao

            linhas.append(
                {
                    "defasagem": k,
                    "correlacao": correlacao,
                    "observacoes": n_observacoes,
                }
            )

        self._defasagem_otima = otima_def
        self._correlacao_otima = otima_corr
        self._resultado_tabela = pd.DataFrame(linhas)

        return self._resultado_tabela.copy()
