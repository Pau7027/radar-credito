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
