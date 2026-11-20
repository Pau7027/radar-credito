"""Fontes de dados para séries temporais do Banco Central do Brasil (SGS)."""

import os
from abc import ABC, abstractmethod

import pandas as pd
import requests

# TODO: séries diárias (ex: Selic, código 432) exigem consultas em blocos de
# até 10 anos por requisição. Implementar na issue futura.


class ErroFonteDados(Exception):
    """Erro ao obter dados de uma fonte."""

    pass


class FonteDados(ABC):
    """Classe abstrata para fontes de dados de séries temporais."""

    def __init__(self, nome: str):
        """Inicializa a fonte com um nome descritivo."""
        self._nome = nome

    @property
    def nome(self) -> str:
        """Nome legível da fonte de dados."""
        return self._nome

    @abstractmethod
    def obter_serie(self, codigo, data_inicio, data_fim):
        """Retorna um DataFrame com as colunas 'data' e 'valor'."""
        pass


class FonteBCB(FonteDados):
    """Consulta séries temporais da API SGS do Banco Central do Brasil.

    Atributos privados acessíveis por @property:
        url_base     -- template da URL da API SGS
        pasta_cache  -- diretório local onde os CSVs são salvos
        tempo_limite -- timeout em segundos para as requisições HTTP
    """

    def __init__(self, pasta_cache="data", tempo_limite=30):
        """Inicializa a fonte com diretório de cache e timeout."""
        super().__init__("Banco Central do Brasil (SGS)")
        self._url_base = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
        self._pasta_cache = pasta_cache
        self._tempo_limite = tempo_limite

    # --- propriedades de leitura ---

    @property
    def url_base(self) -> str:
        """Template da URL da API SGS."""
        return self._url_base

    @property
    def pasta_cache(self) -> str:
        """Diretório local onde os CSVs de cache são armazenados."""
        return self._pasta_cache

    @property
    def tempo_limite(self) -> int:
        """Timeout em segundos para as requisições HTTP."""
        return self._tempo_limite

    # --- método público principal ---

    def obter_serie(self, codigo, data_inicio, data_fim):
        """Obtém a série do BCB para o período indicado.

        Datas no formato 'dd/mm/aaaa'. Tenta a API; se falhar, usa o cache
        local e filtra pelo período pedido.
        """
        try:
            tabela = self._consultar_api(codigo, data_inicio, data_fim)
            self._salvar_cache(tabela, codigo)
            return tabela
        except (requests.RequestException, ValueError, ErroFonteDados) as erro:
            print(f"Aviso: falha na API para a série {codigo} ({erro}). Usando o cache.")
            tabela_cache = self._carregar_cache(codigo)
            return self._filtrar_periodo(tabela_cache, data_inicio, data_fim)

    # --- métodos privados de apoio ---

    def _consultar_api(self, codigo, data_inicio, data_fim):
        """Faz a requisição à API SGS e devolve um DataFrame limpo."""
        url = self._url_base.format(codigo=codigo)
        parametros = {
            "formato": "json",
            "dataInicial": data_inicio,
            "dataFinal": data_fim,
        }
        resposta = requests.get(url, params=parametros, timeout=self._tempo_limite)
        resposta.raise_for_status()
        dados = resposta.json()

        if not isinstance(dados, list) or len(dados) == 0:
            raise ErroFonteDados(f"A série {codigo} não retornou dados.")

        return self._converter_para_tabela(dados)

    def _converter_para_tabela(self, dados):
        """Converte a lista de dicionários da API em DataFrame com tipos corretos."""
        tabela = pd.DataFrame(dados)
        tabela["data"] = pd.to_datetime(tabela["data"], format="%d/%m/%Y")
        tabela["valor"] = pd.to_numeric(tabela["valor"], errors="coerce")
        return tabela

    def _filtrar_periodo(self, tabela, data_inicio, data_fim):
        """Filtra o DataFrame pelo intervalo [data_inicio, data_fim] (inclusive).

        Datas no formato 'dd/mm/aaaa'.
        """
        inicio = pd.to_datetime(data_inicio, format="%d/%m/%Y")
        fim = pd.to_datetime(data_fim, format="%d/%m/%Y")
        mascara = (tabela["data"] >= inicio) & (tabela["data"] <= fim)
        return tabela.loc[mascara].copy()

    def _caminho_cache(self, codigo):
        """Devolve o caminho completo do arquivo CSV de cache da série."""
        return os.path.join(self._pasta_cache, f"serie_{codigo}.csv")

    def _salvar_cache(self, tabela, codigo):
        """Salva o DataFrame como CSV no diretório de cache."""
        os.makedirs(self._pasta_cache, exist_ok=True)
        tabela.to_csv(self._caminho_cache(codigo), index=False)

    def _carregar_cache(self, codigo):
        """Carrega o CSV de cache da série. Lança ErroFonteDados se não existir."""
        caminho = self._caminho_cache(codigo)
        if not os.path.exists(caminho):
            raise ErroFonteDados(
                f"Sem internet e sem cache local para a série {codigo}."
            )
        return pd.read_csv(caminho, parse_dates=["data"])
