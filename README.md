# RadarCrédito

Painel interativo sobre a inadimplência da carteira de crédito no Brasil entre 2016 e 2026. Desenvolvido para a disciplina de Programação Orientada a Objetos do curso de Ciência de Dados e Inteligência Artificial da PUC-SP, com Python, Pandas, Plotly e Streamlit.

[Abrir o painel no Streamlit](https://radar-credito-9bkrsgposq2fxw9fxmappcm.streamlit.app/)

## Integrantes

| Nº | Nome completo | RA |
| --- | --- | --- |
| 1 | Paulo Enrique Pérez González | 00370839 |
| 2 | Thiago Laurino Silva | 00372259 |
| 3 | Giovana Lordello Guimarães | 00376042 |
| 4 | Gabriel Sousa de Carvalho | 00369956 |
| 5 | Julia Amy Yoshioka | 00370507 |

## Problema e objetivo

A taxa de inadimplência da carteira do Sistema Financeiro Nacional mede o percentual do saldo de crédito de operações com pelo menos uma parcela em atraso há mais de 90 dias. A taxa agregada pode esconder diferenças importantes entre o crédito a pessoas físicas e jurídicas e entre modalidades como cartão de crédito e cheque especial. O RadarCrédito permite comparar essas trajetórias e investigar como elas se relacionam com a Selic e a inflação.

O painel responde a cinco perguntas.

1. Como a inadimplência evoluiu no período e quando ocorreram os principais picos e vales?
2. Entre as modalidades de pessoa física comparadas, qual tem a maior inadimplência e a maior volatilidade?
3. Altas da Selic antecedem aumentos da inadimplência? Em quantos meses?
4. Como o IPCA e os juros reais se associam à inadimplência? Qual tem maior poder explicativo na amostra?
5. Pessoas físicas e jurídicas seguem o mesmo ciclo de inadimplência?

## Como executar

Na raiz do repositório, com Python 3.11 ou superior disponível, execute:

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Abra `http://localhost:8501` no navegador. A API é pública e dispensa credenciais. Se a consulta falhar, o aplicativo recorre aos CSVs versionados em `data/`.

Execute a suíte de testes automatizados com o comando abaixo. Ela usa respostas simuladas da API e CSVs locais.

```bash
python -m pytest
```

## Dados e variáveis

A fonte é a API pública do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil. O painel solicita dados de crédito de novembro de 2016 a outubro de 2026. A análise interpretativa usa os 119 meses de inadimplência disponíveis na amostra versionada, de novembro de 2016 a setembro de 2026. A coleta de Selic e IPCA começa em novembro de 2015 para dar histórico ao cálculo da inflação acumulada em 12 meses.

| Código SGS | Série | Frequência e unidade |
| --- | --- | --- |
| 21082 | Inadimplência total | Mensal, % da carteira |
| 21083 | Inadimplência de pessoas jurídicas | Mensal, % da carteira |
| 21084 | Inadimplência de pessoas físicas | Mensal, % da carteira |
| 21112 | Inadimplência de PF com recursos livres | Mensal, % da carteira |
| 21113 | Inadimplência de PF no cheque especial | Mensal, % da carteira |
| 21129 | Inadimplência de PF no cartão de crédito | Mensal, % da carteira |
| 21145 | Inadimplência de PF com recursos direcionados | Mensal, % da carteira |
| 432 | Meta da taxa Selic | Diária, % ao ano |
| 433 | Variação do IPCA | Mensal, % no mês |

Os dados de crédito são organizados em formato longo. `data` é a data de referência, `modalidade` identifica a série e `valor` é a taxa numérica em escala percentual (por exemplo, `5.2` corresponde a `5,2%`). As diferenças entre taxas são medidas em pontos percentuais (p.p.). As análises de correlação usam uma tabela com uma coluna por série e uma linha por mês.

## Tratamento e análise com Pandas

1. **Coleta e limpeza.** O aplicativo consulta o SGS em blocos, converte datas e valores numéricos, ordena os registros e consolida duplicidades por data em cada série. Valores inválidos são excluídos dos cálculos e gráficos que dependem deles.
2. **Exploração.** O notebook verifica tipos, nulos, duplicidades, continuidade mensal e valores fora do domínio esperado. As sete séries de crédito da amostra têm 119 meses consecutivos sem nulos ou duplicidades. Média, mediana, mínimo, máximo e desvio padrão ajudam a comparar as modalidades.
3. **Alinhamento temporal.** A meta Selic é representada pelo último valor de cada mês e alinhada ao IPCA e à inadimplência pelo mês de referência. Meses sem observação para alguma série ficam ausentes na junção.
4. **Comparações.** Os filtros selecionam datas e séries. O ranking agrupa por modalidade e calcula a média das taxas no período. O mapa de calor usa correlações de Pearson e o gráfico de dispersão ajusta uma regressão linear simples para a Selic defasada.

## Arquitetura orientada a objetos

`streamlit_app.py` conecta as classes e inicia o painel.

| Classe | Responsabilidade |
| --- | --- |
| `FonteDados` e `FonteBCB` | Definem o contrato de coleta e implementam a consulta ao SGS e o cache local. |
| `AnalisadorDados` | Encapsula o DataFrame e oferece filtros, agrupamentos, ordenação, tratamento de nulos, estatísticas e conversão entre formatos. |
| `Indicador` e subclasses | Padronizam o cálculo dos indicadores e os metadados exibidos no painel. |
| `Visualizador` | Recebe tabelas processadas e cria figuras Plotly. |
| `AnaliseInterpretativa` | Reúne respostas, conclusões, limitações e resumos calculados para os filtros ativos. |
| `Dashboard` | Recebe os componentes pelo construtor e organiza filtros, cartões, gráficos e tabela. |

A divisão das classes por responsabilidade aplica o princípio da responsabilidade única. `FonteBCB` herda de `FonteDados`. As subclasses de `Indicador` implementam o mesmo método `calcular()`, o que permite ao painel percorrer os indicadores dos cartões de forma polimórfica. O encapsulamento aparece, por exemplo, em `AnalisadorDados`, que guarda o DataFrame em um atributo interno e fornece cópias para consulta.

## Indicadores

| Indicador | Como é calculado |
| --- | --- |
| Inadimplência no fim do período | Última taxa disponível até a data final selecionada, com a diferença para o mês anterior em p.p. |
| Variação em relação à média de 12 meses | Taxa do mês menos a média dos 12 meses anteriores, em p.p. |
| Volatilidade de 12 meses | Desvio padrão amostral da taxa nos últimos 12 meses, incluindo o mês de referência, em p.p. |
| Z-score histórico | Distância entre a taxa e a média do histórico, medida em desvios padrão. |
| Juros reais ex-post | Equação de Fisher aplicada à meta Selic de fim de mês e ao IPCA observado, acumulado em 12 meses. |
| Defasagem da Selic | Número de meses, de 0 a 24, que maximiza o módulo da correlação de Pearson entre a Selic defasada e a taxa de inadimplência. |

## Como usar o painel

Escolha o intervalo e as séries na barra lateral. Em seguida, escolha a série de referência dos quatro cartões no topo. Os indicadores de janela móvel consideram o histórico anterior ao início do intervalo quando disponível.

| Aba | O que mostra |
| --- | --- |
| **Evolução** | Linhas mensais para localizar altas, quedas, picos e vales nas séries selecionadas. |
| **Comparação** | Barras horizontais e treemap com as taxas médias de cheque especial, cartão e recursos direcionados selecionados. A área do treemap é proporcional à taxa média de cada modalidade. |
| **Correlações** | Mapa de calor de Pearson, dispersão com regressão linear e evolução dos juros reais. Cada ponto da dispersão relaciona a inadimplência de um mês à meta Selic de acordo com a defasagem escolhida. |
| **Análise e conclusões** | Respostas às cinco perguntas, síntese dos resultados e limitações. |
| **Tabela de dados** | Observações filtradas por data e série, com as taxas em percentual. |

Os textos que citam o recorte de 11/2016 a 09/2026 descrevem a amostra completa. Os resumos do período selecionado acompanham os filtros.

## Resultados e limitações

- Na aba **Evolução**, a inadimplência total recuou de 3,86% em novembro de 2016 para 2,16% em dezembro de 2020 e atingiu 5,05% em agosto de 2026. Pessoas físicas e jurídicas atingiram o mínimo em dezembro de 2020. A alta posterior foi mais forte entre pessoas físicas.
- As barras e o treemap mostram que o **cheque especial** teve a maior taxa média (13,69%) entre as três modalidades comparadas. Também teve o maior desvio padrão em pontos percentuais (1,99 p.p.).
- No mapa de calor, as taxas de inadimplência total e de pessoas físicas tiveram correlação de 0,94. A taxa de pessoas físicas compõe a taxa total, o que ajuda a entender a proximidade entre as séries.
- Na dispersão, a maior correlação da **Selic com a inadimplência total** ocorreu com oito meses de defasagem (`r = 0,86`). Na análise do período completo, os juros reais mostraram associação mais forte com a inadimplência total do que o IPCA acumulado em 12 meses.

A amostra cobre essencialmente um ciclo de queda e alta. Tendências em comum e a escolha da defasagem na própria amostra podem elevar as correlações observadas. A sobreposição entre séries agregadas e suas modalidades também influencia o mapa de calor. Como as taxas se referem a carteiras distintas, a área do treemap indica apenas a proporção entre as taxas médias exibidas. Os resultados descrevem associações. Fatores como endividamento, renda e desemprego ficaram fora da análise.

## Estrutura do repositório

| Caminho | Conteúdo |
| --- | --- |
| `streamlit_app.py` | Entrada do Streamlit e configuração das séries |
| `src/` | Coleta, análise, indicadores, gráficos e interface |
| `data/` | Cache CSV por código SGS |
| `notebooks/` | Exploração inicial das séries de crédito |
| `tests/` | Testes da coleta, do analisador, dos indicadores, dos gráficos e do painel, além do roteiro manual da coleta |
| `requirements.txt` | Dependências Python |

## Referências

- Banco Central do Brasil. [Portal de Dados Abertos](https://dadosabertos.bcb.gov.br/) e [metadados da série de inadimplência total (SGS 21082)](https://dadosabertos.bcb.gov.br/dataset/21082-inadimplencia-da-carteira-de-credito---total).
- RadarCrédito. [Notebook de exploração inicial dos dados](https://github.com/Pau7027/radar-credito/blob/main/notebooks/01_exploracao_inicial.ipynb) e [análise interpretativa do painel](https://github.com/Pau7027/radar-credito/blob/main/src/analise_interpretativa.py).
