# radar-credito
Painel interativo de inadimplência e risco de crédito no Brasil (2016-2026), com dados do Banco Central (API SGS). Python, POO, Pandas, Plotly e Streamlit.

## Visualizações (issues #6 e #7)

`Visualizador` recebe tabelas Pandas prontas e devolve figuras Plotly. Ele não
consulta a API nem lê arquivos. O formato longo usado por `AnalisadorDados` tem
as colunas `data`, `modalidade` e `valor`, onde `valor` é uma taxa em pontos
percentuais (`5.2` representa `5,2%`). Datas inválidas e valores não numéricos
são descartados; se não restarem dados válidos, o método gera um `ValueError`.

```python
import pandas as pd

from src.visualizador import Visualizador

# Gráficos em formato longo (linhas, barras e treemap)
dados = pd.DataFrame({
    "data": ["2026-01-01", "2026-02-01", "2026-01-01", "2026-02-01"],
    "modalidade": ["Cartão", "Cartão", "Cheque especial", "Cheque especial"],
    "valor": [4.1, 4.3, 7.2, 7.5],
})

linhas = Visualizador.grafico_linhas(dados)
barras = Visualizador.grafico_barras(dados)
treemap = Visualizador.grafico_treemap(dados)

# Gráficos em formato largo (dispersão com regressão e heatmap)
tabela_larga = pd.DataFrame({
    "data": ["2026-01-01", "2026-02-01", "2026-03-01"],
    "selic": [11.25, 11.25, 10.75],
    "pessoa_fisica": [5.1, 5.3, 5.5],
    "pessoa_juridica": [2.2, 2.3, 2.4],
})

dispersao = Visualizador.grafico_dispersao_defasada(
    tabela_larga, coluna_x="selic", coluna_y="pessoa_fisica", defasagem=0
)
heatmap = Visualizador.grafico_heatmap_correlacao(
    tabela_larga, rotulos={"pessoa_fisica": "PF", "pessoa_juridica": "PJ"}
)

# No aplicativo Streamlit, as figuras são exibidas com st.plotly_chart(...).
```

O gráfico de linhas mostra a evolução por modalidade e calcula a média se houver
mais de um registro para a mesma modalidade e data. Barras e treemap usam a taxa
média de cada modalidade no período recebido. No treemap, a área compara essas
taxas; **não representa volume de crédito nem participação de mercado**.

O gráfico de dispersão relaciona duas variáveis contínuas com ajuste de reta linear
por mínimos quadrados e suporte a defasagem temporal no eixo X. Já o heatmap mostra
correlação entre os níveis das séries, sem defasagem, com escala divergente padronizada.
**Advertência:** correlação não é causalidade; duas séries macroeconômicas com
tendência comum podem apresentar correlação espúria.

Para usar outros nomes de coluna, passe `coluna_data`, `coluna_modalidade` e/ou
`coluna_valor` aos métodos correspondentes. A linha também aceita uma tabela
com apenas `data` e `valor`, como a devolvida por `FonteBCB`.

Instale as dependências com `python -m pip install -r requirements.txt` e rode
os testes com `python -m pytest tests/test_visualizador.py`.

## Painel Streamlit

`streamlit_app.py` mostra os três gráficos com filtros de período e modalidade.
Ele usa os CSVs de cache já versionados em `data/`; portanto, o painel pode ser
publicado sem uma chave de API, mas os valores **não se atualizam sozinhos**.

Para rodar localmente, instale as dependências e execute:

```bash
python -m streamlit run streamlit_app.py
```

No Streamlit Community Cloud, selecione o repositório, a branch `main` e o
arquivo principal `streamlit_app.py` depois de mesclar o pull request. O serviço
instala as dependências declaradas em `requirements.txt`.


