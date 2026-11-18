import os
from abc import ABC, abstractmethod

import pandas as pd
import requests


class ErroFonteDados(Exception):
    """Erro ao obter dados de uma fonte"""
    pass

class FonteDados(ABC):
    """Classe abstrata para fontes de dados"""
    
    def __init__(self, nome: str):
        self._nome = nome
        
    @property
    def nome(self) -> str:
        return self._nome
    
    @abstractmethod
    def obter_series(self,codigo, data_inicio,data_fim):
        """Retorna um DataFrame com as colunas 'data' e 'valor'"""
        pass
    
class FonteBCB(FonteDados):
    """Consulta séries temporais da API SGS do Banco Central do Brasil"""
    
    
    URL_BASE = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados'
    
    def __init__(self, pasta_cache="data", tempo_limite=30):
        super().__init__("Banco Central do Brasil (SGS)")
        self.pasta_cache = pasta_cache
        self.tempo_limite = tempo_limite
        
    def obter_series(self,codigo,data_inicio,data_fim):
        """Datas no formato 'dd/mm/aaaa. Tenta a API, sse falhar usa o cache."""    
        try:
            tabela = self._consultar_api(codigo,data_inicio,data_fim)
            self._salvar_cache(tabela,codigo)
            return tabela
        except(requests.RequestException, ValueError, ErroFonteDados) as erro:
            print(f"Aviso: falha na API para a série{codigo} ({erro}). Usando o cache")
            return self._carregar_cache(codigo)
        
        
        
    def _consultar_api(self,codigo,data_inicio,data_fim):
        url = self.URL_BASE.format(codigo=codigo)
        parametros = {
            'formato':'json',
            'dataInicial':data_inicio,
            'dataFinal':data_fim
        }
        resposta = requests.get(url, params=parametros, timeout=self.tempo_limite)
        resposta.raise_for_status()
        dados= resposta.json()
        
        if not isinstance(dados,list) or len(dados)==0:
            raise ErroFonteDados(f"A série {codigo} não retornou dados.")
        return self._converter_para_tabela(dados)
    
    def _converter_para_tabela(self, dados):
        tabela = pd.DataFrame(dados)
        tabela['data'] = pd.to_datetime(tabela['data'], dayfirst=True)
        tabela['valor'] = pd.to_numeric(tabela['valor'], errors='coerce')
        return tabela

    def _caminho_cache(self,codigo):
        return os.path.join(self.pasta_cache,f"serie_{codigo}.csv")
    
    
    def _salvar_cache(self,tabela,codigo):
        os.makedirs(self.pasta_cache,exist_ok=True)
        tabela.to_csv(self._caminho_cache(codigo), index=False)

    def _carregar_cache(self,codigo):
        caminho = self._caminho_cache(codigo)
        if not os.path.exists(caminho):
            raise ErroFonteDados(
                f"Sem internet e sem cache local para a série {codigo}."
                
            )  
        return pd.read_csv(caminho, parse_dates=['data'])
      