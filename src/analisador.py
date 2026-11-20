"""Utilitários para processamento e análise de séries de crédito com Pandas."""

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd


class Analisador:
	"""Analisa um DataFrame com colunas de data, modalidade e valor."""

	def __init__(
		self,
		dados: pd.DataFrame,
		coluna_data: str = "data",
		coluna_modalidade: str = "modalidade",
		coluna_valor: str = "valor",
	) -> None:
		self.dados = dados.copy()
		self.coluna_data = coluna_data
		self.coluna_modalidade = coluna_modalidade
		self.coluna_valor = coluna_valor

	def filtrar(
		self,
		inicio: Any = None,
		fim: Any = None,
		modalidade: Any = None,
	) -> pd.DataFrame:
		"""Filtra por intervalo de datas (inclusive) e/ou modalidade."""
		resultado = self.dados.copy()
		if inicio is not None or fim is not None:
			datas = pd.to_datetime(resultado[self.coluna_data], errors="coerce")
			mascara = datas.notna()
			if inicio is not None:
				mascara &= datas >= pd.to_datetime(inicio)
			if fim is not None:
				mascara &= datas <= pd.to_datetime(fim)
			resultado = resultado.loc[mascara]
		if modalidade is not None:
			modalidades = modalidade if isinstance(modalidade, (list, tuple, set)) else [modalidade]
			resultado = resultado[resultado[self.coluna_modalidade].isin(modalidades)]
		return resultado.copy()

	def tratar_nulos(self, estrategia: str = "remover", valor: Any = None) -> pd.DataFrame:
		"""Trata valores ausentes: remove linhas, preenche com valor ou usa método Pandas."""
		if estrategia == "remover":
			self.dados = self.dados.dropna().copy()
		elif estrategia == "preencher":
			self.dados = self.dados.fillna(valor).copy()
		elif estrategia in {"ffill", "bfill"}:
			self.dados = self.dados.fillna(method=estrategia).copy()
		else:
			raise ValueError("Estratégia deve ser 'remover', 'preencher', 'ffill' ou 'bfill'.")
		return self.dados.copy()

	def remover_duplicados(self, subset: Sequence[str] | None = None) -> pd.DataFrame:
		"""Remove linhas duplicadas, opcionalmente considerando apenas algumas colunas."""
		self.dados = self.dados.drop_duplicates(subset=subset).copy()
		return self.dados.copy()

	def agrupar_por_modalidade(self, operacao: str = "sum") -> pd.DataFrame:
		"""Agrupa por modalidade e aplica a operação à coluna de valor."""
		return self._agrupar([self.coluna_modalidade], operacao)

	def agrupar_por_ano(self, operacao: str = "sum") -> pd.DataFrame:
		"""Agrupa por ano, derivado da coluna de data."""
		dados = self.dados.copy()
		dados[self.coluna_data] = pd.to_datetime(dados[self.coluna_data], errors="coerce")
		dados = dados.dropna(subset=[self.coluna_data])
		dados["ano"] = dados[self.coluna_data].dt.year
		return self._agrupar(["ano"], operacao, dados=dados)

	def ordenar(self, por: str | list[str], crescente: bool = True) -> pd.DataFrame:
		"""Ordena os dados por uma ou mais colunas."""
		return self.dados.sort_values(by=por, ascending=crescente).reset_index(drop=True)

	def estatisticas_descritivas(self, coluna: str | None = None) -> pd.DataFrame | pd.Series:
		"""Retorna estatísticas descritivas gerais ou de uma coluna específica."""
		alvo = self.dados if coluna is None else self.dados[coluna]
		return alvo.describe()

	@staticmethod
	def unir_series(series: Mapping[str, Any] | Sequence[Any]) -> pd.DataFrame:
		"""Une séries ou DataFrames por índice em um único DataFrame."""
		if isinstance(series, Mapping):
			itens = series.items()
		else:
			itens = ((getattr(item, "name", None) or f"serie_{i + 1}", item)
					 for i, item in enumerate(series))

		colunas = {}
		for nome, item in itens:
			if isinstance(item, pd.Series):
				colunas[nome] = item.rename(nome)
			elif isinstance(item, pd.DataFrame):
				if item.shape[1] == 1:
					colunas[nome] = item.iloc[:, 0].rename(nome)
				else:
					colunas[nome] = item
			else:
				colunas[nome] = pd.Series(item, name=nome)
		if not colunas:
			return pd.DataFrame()
		return pd.concat(colunas.values(), axis=1, join="outer")

	def _agrupar(
		self,
		chaves: list[str],
		operacao: str,
		dados: pd.DataFrame | None = None,
	) -> pd.DataFrame:
		dados = self.dados if dados is None else dados
		if operacao not in {"sum", "mean", "median", "min", "max", "count"}:
			raise ValueError("Operação deve ser sum, mean, median, min, max ou count.")
		agrupamento = dados.groupby(chaves, dropna=False)[self.coluna_valor]
		return getattr(agrupamento, operacao)().reset_index(name=self.coluna_valor)
