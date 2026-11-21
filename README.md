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

O painel é estruturado pela classe `Dashboard` (em `src/dashboard.py`), que recebe via injeção de dependências:
- Um objeto `AnalisadorDados` com os dados no formato longo (`data`, `modalidade`, `valor`);
- Um dicionário com as classes de `Indicador` (`VariacaoVsMedia12m`, `Volatilidade12m`, `ZScore`);
- Uma instância do `Visualizador`;
- Título e descrição do projeto;
- A lista de `series_folha` desagregadas sem sobreposição para as comparações;
- Um DataFrame opcional `series_macro` para análises com a taxa Selic.

O arquivo principal `streamlit_app.py` consulta as 7 séries de crédito na API SGS do Banco Central do Brasil utilizando `FonteBCB` com cache local versionado em `data/` (garantindo funcionamento contínuo mesmo sem conexão à internet).

### Recursos da Interface:
- **Filtros interativos na barra lateral:** seleção do intervalo de datas (`Data inicial` e `Data final`) e seleção múltipla de `Séries`.
- **4 KPIs principais:** Inadimplência no fim do período (com variação mensal em p.p. e destaque semafórico), Variação vs. média de 12 meses, Volatilidade (12 meses) e Z-score histórico, calculados sobre o histórico completo de uma série de referência selecionada.
- **4 Abas dinâmicas:**
  - **Evolução:** gráfico de linhas com a trajetória temporal de todas as séries selecionadas;
  - **Comparação:** ranking em gráfico de barras horizontais e mapa proporcional em treemap comparando as taxas médias das modalidades folha selecionadas;
  - **Correlações:** matriz de correlação linear de Pearson em mapa de calor (heatmap) contemporâneo e relação com a Selic defasada (quando `series_macro` estiver configurada);
  - **Tabela de dados:** visualização paginada e ordenada com data (`mm/aaaa`), série e taxa percentual formatada, além do total de registros exibidos.

Para rodar localmente, instale as dependências e execute:

```bash
python -m streamlit run streamlit_app.py
```

No Streamlit Community Cloud, selecione o repositório, a branch `main` e o
arquivo principal `streamlit_app.py` depois de mesclar o pull request. O serviço
instala as dependências declaradas em `requirements.txt`.


