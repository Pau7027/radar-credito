# radar-credito
Painel interativo de inadimplência e risco de crédito no Brasil (2016-2026), com dados do Banco Central (API SGS). Python, POO, Pandas, Plotly e Streamlit.

## Visualizações da issue #9

`Visualizador` recebe tabelas Pandas prontas e devolve figuras Plotly. Ele não
consulta a API nem lê arquivos. O formato longo usado por `AnalisadorDados` tem
as colunas `data`, `modalidade` e `valor`, onde `valor` é uma taxa em pontos
percentuais (`5.2` representa `5,2%`). Datas inválidas e valores não numéricos
são descartados; se não restarem dados válidos, o método gera um `ValueError`.

```python
import pandas as pd

from src.visualizador import Visualizador

dados = pd.DataFrame({
    "data": ["2026-01-01", "2026-02-01", "2026-01-01", "2026-02-01"],
    "modalidade": ["Cartão", "Cartão", "Cheque especial", "Cheque especial"],
    "valor": [4.1, 4.3, 7.2, 7.5],
})

linhas = Visualizador.grafico_linhas(dados)
barras = Visualizador.grafico_barras(dados)
treemap = Visualizador.grafico_treemap(dados)

# No aplicativo Streamlit, as figuras são exibidas com st.plotly_chart(...).
```

O gráfico de linhas mostra a evolução por modalidade e calcula a média se houver
mais de um registro para a mesma modalidade e data. Barras e treemap usam a taxa
média de cada modalidade no período recebido. No treemap, a área compara essas
taxas; **não representa volume de crédito nem participação de mercado**.

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


