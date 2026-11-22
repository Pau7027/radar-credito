"""Análise interpretativa do painel RadarCrédito.

Reúne os textos que explicam cada gráfico, as respostas às cinco perguntas do
projeto, as conclusões e as limitações.

Os textos fixos descrevem o período completo (11/2016 a 09/2026) e foram
conferidos contra as séries do Banco Central (SGS 21082, 21083, 21084, 21112,
21113, 21129, 21145, 432 e 433). Os métodos "resumo_*" geram frases dinâmicas
a partir do período e das séries selecionados nos filtros do painel.
"""

import pandas as pd

PERIODO_COMPLETO = "11/2016 a 09/2026"

NOMES_MACRO = {"selic": "Selic meta", "ipca": "IPCA mensal"}

PERGUNTAS = (
    "Como a inadimplência evoluiu em 10 anos e quais foram os picos e vales?",
    "Qual modalidade de crédito pessoa física é mais inadimplente e volátil?",
    "A alta da Selic antecede aumentos de inadimplência? Com qual defasagem?",
    "Os juros reais e a inflação (IPCA) ajudam a explicar a inadimplência? "
    "Qual dos dois tem mais poder explicativo?",
    "Pessoa física e pessoa jurídica seguem o mesmo ciclo?",
)

TEXTO_EVOLUCAO = """**Leitura do gráfico (período completo: 11/2016 a 09/2026)**

- **Ciclo em "U".** A inadimplência total caiu de 3,86% (11/2016) para a mínima de 2,16% (12/2020) e depois subiu até 5,05% em 08/2026, a máxima do período (4,98% em 09/2026). Pela média anual, o Total foi de 3,77% em 2017, 2,31% em 2021 (a menor) e 4,72% em 2026 (até setembro).
- **Vale sincronizado.** Total, pessoa física, pessoa jurídica e crédito direcionado tiveram a mínima no mesmo mês, 12/2020. PF livres (03/2021), cartão (04/2021) e cheque especial (04/2021) chegaram ao fundo pouco depois.
- **Alta recente e generalizada.** Entre 09/2025 e 09/2026, o Total subiu 0,89 p.p. (de 4,09% para 4,98%), a pessoa física 1,10 p.p. (de 4,89% para 5,99%) e a pessoa jurídica 0,51 p.p. (de 2,77% para 3,28%). Pessoa física, PF livres, cartão e direcionados têm suas máximas do período em 08/2026 ou 09/2026.
- **Exceções.** O cheque especial teve o pico em 12/2019 (17,57%) e está em 15,96% em 09/2026. A pessoa jurídica teve o pico em 05/2017 (4,06%) e está em 3,28%.
- **Sinal de estresse.** Em relação à média do período completo, o z-score do Total em 09/2026 é +2,61, e ele passou de +2 em seis meses de 2026 (fevereiro, abril, maio, julho, agosto e setembro).
"""

TEXTO_RANKING = """**Leitura do gráfico (período completo: 11/2016 a 09/2026)**

- **Ranking de risco.** Entre as modalidades desagregadas, o cheque especial tem a maior taxa média (13,69%), seguido do cartão de crédito (6,97%) e dos recursos direcionados (1,84%). A taxa média do cheque especial é 1,96 vez a do cartão e 7,5 vezes a do crédito direcionado.
- **A média esconde o presente.** Em 09/2026 o cartão está em 10,04% (3,07 p.p. acima da sua média), o cheque especial em 15,96% (2,27 p.p. acima) e os direcionados em 3,41% (quase o dobro da média).
- **Volatilidade em pontos percentuais.** O cheque especial também oscila mais (desvio padrão de 1,99 p.p.; de 9,44% a 17,57%), seguido do cartão (1,48 p.p.; de 3,79% a 10,04%) e dos direcionados (0,52 p.p.; de 1,25% a 3,60%). Nos últimos 12 meses, o desvio padrão móvel é maior no cheque especial (0,47 p.p.), contra 0,40 no cartão e 0,28 nos direcionados.
- **Volatilidade relativa.** O ranking se inverte ao dividir o desvio padrão pela média (coeficiente de variação): direcionados 28,4%, cartão 21,3% e cheque especial 14,6%. O crédito direcionado tem as menores taxas, mas oscila bastante em proporção ao seu nível.
"""

TEXTO_TREEMAP = """**Leitura do gráfico (período completo: 11/2016 a 09/2026)**

- A **área** de cada bloco é proporcional à **taxa média** de inadimplência da modalidade (cheque especial 13,69%, cartão 6,97% e direcionados 1,84%). Ela **não** representa volume de crédito nem participação de mercado.
- Como as três taxas somam 22,50 pontos, o cheque especial ocupa cerca de 61% da área, o cartão 31% e os direcionados 8%. Esses percentuais comparam taxas entre si; não são a composição da carteira.
- Pessoa física, pessoa jurídica e Total ficam de fora porque agregam as modalidades (entrariam em duplicidade), e as demais modalidades de crédito não fazem parte do painel.
"""

TEXTO_HEATMAP = """**Leitura do gráfico (período completo: 11/2016 a 09/2026; correlação de Pearson entre os níveis das séries, sem defasagem)**

- **Séries que se sobrepõem.** As maiores correlações ocorrem entre séries aninhadas: PF e PF livres (0,97), cartão e PF livres (0,96), Total e PF (0,94). Isso é em parte mecânico, porque o Total contém a PF, que contém os recursos livres, que contêm o cartão e o cheque especial.
- **Cheque especial.** É o menos alinhado com as demais séries de inadimplência (0,48 a 0,62) e quase não se correlaciona com a Selic (0,08).
- **Selic.** A correlação sem defasagem é positiva: 0,80 com PF livres e cartão, 0,71 com PF, 0,67 com o Total, 0,40 com PJ e 0,32 com direcionados. A relação com atraso aparece no gráfico de dispersão.
- **IPCA mensal.** A correlação com a inadimplência é negativa e fraca (de -0,19 a -0,38). O sinal reflete o calendário dos ciclos (a inflação foi maior antes da alta da inadimplência) e não indica que a inflação reduza a inadimplência.
- **Cuidado.** Correlação não implica causalidade, e séries com tendência podem se correlacionar por coincidência.
"""

TEXTO_DISPERSAO = """**Leitura do gráfico (período completo: 11/2016 a 09/2026)**

Cada ponto é um mês: o eixo X mostra a Selic meta de alguns meses antes (a defasagem) e o eixo Y, a inadimplência do mês. A reta é uma regressão linear simples, e o R² indica a fração da variação da inadimplência associada à Selic defasada.

Defasagem de maior correlação (testadas de 0 a 24 meses) no período completo:

| Série | Defasagem (meses) | Correlação (r) | R² | Observações |
|---|---|---|---|---|
| Total | 8 | +0,86 | 0,74 | 111 |
| Pessoa física | 6 | +0,80 | 0,64 | 113 |
| Pessoa jurídica | 14 | +0,87 | 0,76 | 105 |
| PF recursos livres | 5 | +0,89 | 0,80 | 114 |
| Cartão de crédito | 5 | +0,90 | 0,81 | 114 |
| Cheque especial | 10 | +0,39 | 0,15 | 109 |
| PF recursos direcionados | 10 | +0,50 | 0,25 | 109 |

- **Selic alta antecede inadimplência alta.** Para Total, PF, PF livres e cartão, a correlação é máxima com defasagem de 5 a 8 meses. Para PJ, a defasagem é mais longa (14 meses). O cheque especial quase não responde à Selic.
- **Robustez.** Em variações de 12 meses (que retiram a tendência comum), a relação continua: Total +0,83 (7 meses), PF +0,76 (6), PJ +0,79 (10), PF livres +0,85 (6), cartão +0,81 (6), cheque especial +0,58 (7) e direcionados +0,41 (8).
- **Mecanismo plausível (hipótese).** Juros mais altos encarecem o crédito e o serviço das dívidas, e o efeito sobre os atrasos se acumula com defasagem. O painel mostra associação, não prova esse mecanismo.
- **Cuidados.** A defasagem foi escolhida olhando os dados, são pouco mais de 100 observações e o período contém essencialmente um grande ciclo (queda até 2020 e alta depois). Os números mudam com a série de referência e com o período selecionado.
"""

TEXTO_JUROS_REAIS = """**Leitura do gráfico (período completo: 11/2016 a 09/2026)**

- **O que mede.** Juros reais ex-post pela equação de Fisher: (1 + Selic) / (1 + IPCA acumulado em 12 meses) - 1, usando a Selic meta no fim de cada mês. Mostram quanto os juros superam a inflação.
- **Trajetória.** Os juros reais eram de 6,55% a.a. em 11/2016, ficaram negativos em 20 dos 119 meses (entre 07/2020 e 04/2022, com mínima de -4,35% em 07/2021) e subiram até 10,78% a.a. em 02/2026, a máxima do período (8,77% em 09/2026). A média do período é de 4,31% a.a.
- **De onde vem.** A Selic meta ficou em 2,00% de 08/2020 a 02/2021 e em 15,00% de 06/2025 a 02/2026, enquanto o IPCA em 12 meses chegou a 12,13% em 04/2022 e estava em 4,58% em 09/2026.
- **Relação com a inadimplência.** O mínimo da inadimplência (12/2020 a 04/2021) ocorreu durante o período de juros reais negativos, e a alta veio depois que eles se tornaram elevados. A correlação sem defasagem entre juros reais e inadimplência é de 0,86 para o Total, 0,81 para PF, 0,69 para PJ, 0,91 para cartão, 0,41 para cheque especial e 0,49 para direcionados.
- **Limite.** O cálculo usa a inflação já observada, não a esperada pelo mercado.
"""

RESPOSTAS = (
    """A inadimplência total seguiu um ciclo em "U": caiu de 3,86% (11/2016) para a mínima de 2,16% (12/2020), subiu e chegou a 5,05% em 08/2026, a máxima do período (4,98% em 09/2026). O vale foi quase simultâneo em todas as séries (12/2020 a 04/2021). A alta começou em 2022 e se acelerou em 2025 e 2026 (média anual do Total: 3,32% em 2024, 3,85% em 2025 e 4,72% em 2026). Os picos da pessoa jurídica (05/2017, 4,06%) e do cheque especial (12/2019, 17,57%) são anteriores ao vale; os das demais séries são de 2026.""",
    """O **cheque especial** é a modalidade mais inadimplente (média de 13,69%; 15,96% em 09/2026) e a mais volátil em pontos percentuais (desvio padrão de 1,99 p.p.; amplitude de 8,13 p.p.). O **cartão de crédito** vem a seguir (média de 6,97%; 10,04% em 09/2026, máxima do período). Em volatilidade relativa (desvio padrão dividido pela média), o crédito direcionado lidera (28,4%), mas com as menores taxas (média de 1,84%). Hoje, o cartão é a modalidade que mais se afasta da própria média em pontos percentuais (+3,07 p.p.).""",
    """**Sim, há associação positiva com defasagem:** Selic mais alta antecede inadimplência mais alta. A correlação é máxima com defasagem de 8 meses para o Total (r = +0,86; R² = 0,74), 6 meses para a pessoa física (+0,80), 5 meses para PF livres e cartão (+0,89 e +0,90) e 14 meses para a pessoa jurídica (+0,87). Em variações de 12 meses, a relação persiste (Total: +0,83 com 7 meses). O cheque especial é a exceção (r = +0,39, com 10 meses). Trata-se de associação, não de causalidade: a defasagem foi escolhida olhando os dados e o período contém essencialmente um ciclo.""",
    """**Os juros reais explicam muito mais do que a inflação.** Para o Total, o IPCA em 12 meses sozinho tem R² de 0,17 e sinal negativo (-0,11 p.p. de inadimplência por ponto de inflação). Os juros reais defasados em 6 meses têm R² de 0,75 (cada ponto percentual a mais de juro real se associa a +0,135 p.p. de inadimplência). Com os dois juntos (R² = 0,77), os juros reais seguem significativos (+0,150; p < 0,001) e o IPCA perde importância (+0,044; p = 0,12). Em variações de 12 meses o resultado é parecido (Total: R² = 0,51; IPCA com p = 0,47). Para a pessoa física, o IPCA tem efeito pequeno nos níveis (+0,089; p = 0,036) e nulo nas variações (p = 0,98); para a pessoa jurídica, é pequeno nas variações (+0,050; p = 0,024). O sinal negativo da inflação isolada vem do calendário: o IPCA subiu antes da alta da inadimplência, e a resposta foi elevar a Selic. O endividamento das famílias não foi incluído (ver limitações).""",
    """**Em parte.** Há um ciclo comum: o vale ocorreu no mesmo mês (12/2020), e a correlação entre PF e PJ é de 0,60 nos níveis e 0,64 nas variações de 12 meses. Mas as trajetórias diferem: a pessoa jurídica caiu mais e subiu menos (média anual de 3,55% em 2017, 1,43% em 2021 e 3,17% em 2026), enquanto a pessoa física foi de 3,97% para 2,97% e 5,64%. A PF esteve acima da PJ nos 119 meses, e a diferença foi de 0,10 p.p. (05/2017) a 2,71 p.p. (09/2026): a alta recente está concentrada na pessoa física. A PJ também reage mais tarde à Selic (14 meses contra 6 da PF). Não há evidência clara de que uma antecipe a outra: nas variações de 12 meses, a correlação é 0,64 sem defasagem e sobe só para 0,65 no melhor deslocamento (3 meses).""",
)

CONCLUSOES = """- A inadimplência está no maior patamar da década (Total em 4,98% em 09/2026, com máxima de 5,05% em 08/2026), puxada pela pessoa física, em especial pelo cartão de crédito (10,04%) e pelo crédito livre (8,09%).
- O ciclo acompanha, com defasagem de cerca de 5 a 8 meses, o ciclo de juros: a Selic meta foi de 2,00% (2020-2021) a 15,00% (06/2025 a 02/2026), e os juros reais chegaram a 10,78% a.a. em 02/2026.
- Entre inflação e juros reais, os juros reais têm muito mais associação com a inadimplência; o IPCA acrescenta pouco.
- O cheque especial tem as maiores taxas e a maior volatilidade, mas não está no seu recorde (17,57% em 12/2019) e é pouco sensível à Selic.
- Pessoa física e pessoa jurídica compartilham o ciclo só em parte; a alta recente é da pessoa física.
- A Selic meta recuou de 15,00% para 13,75% em 09/2026. Se a relação com defasagem se mantiver, o efeito sobre a inadimplência só apareceria depois; isso é uma hipótese a acompanhar, não uma previsão do painel.
"""

LIMITACOES = """- **Definição da taxa.** É o percentual da carteira com ao menos uma parcela em atraso há mais de 90 dias: o saldo inteiro do contrato conta, e a taxa não mede perda efetiva nem valores em reais.
- **Taxas não se somam.** As séries são taxas, não volumes; o treemap compara taxas e não representa participação de mercado.
- **Séries aninhadas.** Total, PF, PF livres, cartão e cheque especial se sobrepõem, então parte das correlações altas é mecânica. Só três modalidades desagregadas estão no painel.
- **Amostra pequena.** São 119 meses e essencialmente um grande ciclo (queda até 2020 e alta depois). As defasagens foram escolhidas olhando os dados, o que favorece ajustes otimistas, e o número de observações varia com a defasagem.
- **Correlação não é causalidade.** Séries com tendência podem se correlacionar por coincidência. Nas regressões, a autocorrelação dos resíduos é alta (Durbin-Watson entre 0,03 e 0,42), então os p-valores são otimistas. A defasagem de 6 meses dos juros reais foi fixada para simplificar; a de maior correlação varia (Total: 3 meses; PF: 0; PJ: 8).
- **Juros reais ex-post.** Usam a inflação já observada (IPCA acumulado em 12 meses) e a Selic meta no fim do mês, e não as expectativas do mercado nem a Selic efetiva.
- **Variáveis ausentes.** Endividamento e comprometimento de renda das famílias, desemprego, renda, mudanças regulatórias e medidas de apoio durante a pandemia não foram modelados e podem explicar parte dos ciclos (hipótese não testada).
- **Dados.** Fonte: Banco Central do Brasil (SGS). A inadimplência vai até 09/2026 e a Selic e o IPCA até 10/2026. O z-score usa média e desvio padrão do período completo (inclui dados posteriores a cada mês), e os indicadores móveis precisam de 12 meses de histórico.
- **Textos fixos x dinâmicos.** Os textos fixos descrevem o período completo e não mudam com os filtros; só as frases iniciadas por "No período selecionado" são recalculadas.
"""


class AnaliseInterpretativa:
    """Fornece textos interpretativos fixos e resumos dinâmicos para o painel.

    A classe não depende do Streamlit nem das fontes de dados: recebe
    DataFrames e Series prontos e devolve texto em formato Markdown.
    """

    CHAVES = ("evolucao", "ranking", "treemap", "heatmap", "dispersao", "juros_reais")

    def __init__(self, periodo_referencia: str = PERIODO_COMPLETO) -> None:
        """Define o período descrito pelos textos fixos."""
        self._periodo_referencia = periodo_referencia
        self._textos = {
            "evolucao": TEXTO_EVOLUCAO,
            "ranking": TEXTO_RANKING,
            "treemap": TEXTO_TREEMAP,
            "heatmap": TEXTO_HEATMAP,
            "dispersao": TEXTO_DISPERSAO,
            "juros_reais": TEXTO_JUROS_REAIS,
        }

    @property
    def periodo_referencia(self) -> str:
        """Período a que se referem os textos fixos."""
        return self._periodo_referencia

    # --- textos fixos ---

    def texto(self, chave: str) -> str:
        """Devolve o texto interpretativo fixo de um gráfico."""
        if chave not in self._textos:
            raise ValueError(
                f"Chave desconhecida: '{chave}'. Use uma destas: {', '.join(self.CHAVES)}."
            )
        return self._textos[chave]

    def perguntas_e_respostas(self) -> list:
        """Devolve uma lista de pares (pergunta, resposta) do projeto."""
        pares = []
        for i in range(len(PERGUNTAS)):
            pares.append((PERGUNTAS[i], RESPOSTAS[i]))
        return pares

    def conclusoes(self) -> str:
        """Devolve as conclusões principais da análise."""
        return CONCLUSOES

    def limitacoes(self) -> str:
        """Devolve as limitações da análise."""
        return LIMITACOES

    # --- resumos dinâmicos ---

    def resumo_evolucao(
        self,
        dados: pd.DataFrame,
        coluna_data: str = "data",
        coluna_modalidade: str = "modalidade",
        coluna_valor: str = "valor",
    ) -> str:
        """Resume as séries do período filtrado (formato longo)."""
        tabela = self._tabela_valida(dados, coluna_data, coluna_modalidade, coluna_valor)
        if tabela.empty:
            return ""

        medias = tabela.groupby(coluna_modalidade)[coluna_valor].mean()
        maior = medias.idxmax()
        menor = medias.idxmin()
        linha_pico = tabela.loc[tabela[coluna_valor].idxmax()]
        periodo = self._periodo_texto(tabela[coluna_data])

        if maior == menor:
            medias_txt = f"a taxa média de {maior} foi de {self._fmt(medias[maior])}%"
        else:
            medias_txt = (
                f"a maior taxa média é a de {maior} ({self._fmt(medias[maior])}%) "
                f"e a menor é a de {menor} ({self._fmt(medias[menor])}%)"
            )
        return (
            f"No período selecionado ({periodo}), {medias_txt}; o maior valor mensal "
            f"foi {self._fmt(linha_pico[coluna_valor])}% "
            f"({linha_pico[coluna_modalidade]}, {self._mes(linha_pico[coluna_data])})."
        )

    def resumo_comparacao(
        self,
        dados: pd.DataFrame,
        coluna_data: str = "data",
        coluna_modalidade: str = "modalidade",
        coluna_valor: str = "valor",
    ) -> str:
        """Compara as taxas médias das modalidades exibidas (formato longo)."""
        tabela = self._tabela_valida(dados, coluna_data, coluna_modalidade, coluna_valor)
        if tabela.empty:
            return ""

        medias = tabela.groupby(coluna_modalidade)[coluna_valor].mean()
        if len(medias) < 2:
            nome = medias.index[0]
            return (
                f"No período selecionado, a taxa média de {nome} foi de "
                f"{self._fmt(medias.iloc[0])}%."
            )

        maior = medias.idxmax()
        menor = medias.idxmin()
        texto = (
            f"No período selecionado, entre as modalidades exibidas, {maior} tem a maior "
            f"taxa média ({self._fmt(medias[maior])}%) e {menor} a menor "
            f"({self._fmt(medias[menor])}%)"
        )
        if medias[menor] > 0:
            razao = medias[maior] / medias[menor]
            texto += f", ou seja, {self._fmt(razao, 1)} vezes a taxa da menor"
        return texto + "."

    def resumo_heatmap(self, tabela_larga: pd.DataFrame) -> str:
        """Indica os pares mais e menos correlacionados do período filtrado."""
        colunas = []
        for coluna in tabela_larga.columns:
            if pd.to_numeric(tabela_larga[coluna], errors="coerce").dropna().shape[0] >= 3:
                colunas.append(coluna)
        if len(colunas) < 2:
            return ""

        numerica = tabela_larga[colunas].apply(pd.to_numeric, errors="coerce")
        correlacoes = numerica.corr()
        maior = None
        menor = None
        for i in range(len(colunas)):
            for j in range(i + 1, len(colunas)):
                valor = correlacoes.iloc[i, j]
                if pd.isna(valor):
                    continue
                if maior is None or valor > maior[0]:
                    maior = (valor, colunas[i], colunas[j])
                if menor is None or valor < menor[0]:
                    menor = (valor, colunas[i], colunas[j])
        if maior is None:
            return ""

        return (
            "No período selecionado, o par mais correlacionado é "
            f"{self._nome_coluna(maior[1])} e {self._nome_coluna(maior[2])} "
            f"(r = {self._fmt(maior[0])}) e o menos correlacionado é "
            f"{self._nome_coluna(menor[1])} e {self._nome_coluna(menor[2])} "
            f"(r = {self._fmt(menor[0])})."
        )

    def resumo_dispersao(
        self,
        serie_referencia: str,
        defasagem_otima: int,
        correlacao_otima: float,
        defasagem_exibida: int,
    ) -> str:
        """Resume a defasagem ótima da Selic para a série de referência."""
        if pd.isna(correlacao_otima):
            return ""
        determinacao = correlacao_otima * correlacao_otima
        return (
            f"No período selecionado, para a série {serie_referencia}, a correlação máxima "
            f"ocorre com a Selic defasada em {int(defasagem_otima)} meses "
            f"(r = {self._fmt(correlacao_otima)}; R² = {self._fmt(determinacao)}). "
            f"O gráfico mostra a defasagem de {int(defasagem_exibida)} meses."
        )

    def resumo_juros_reais(self, juros: pd.Series) -> str:
        """Resume os juros reais do período filtrado (Series com índice de datas)."""
        validos = pd.to_numeric(juros, errors="coerce").dropna()
        if validos.empty:
            return ""

        negativos = int((validos < 0).sum())
        return (
            "No período selecionado, os juros reais variaram de "
            f"{self._fmt(validos.min())}% a.a. ({self._mes(validos.idxmin())}) a "
            f"{self._fmt(validos.max())}% a.a. ({self._mes(validos.idxmax())}); em "
            f"{self._mes(validos.index[-1])} foram de {self._fmt(validos.iloc[-1])}% a.a., "
            f"e {negativos} de {len(validos)} meses tiveram juros reais negativos."
        )

    # --- apoio ---

    @staticmethod
    def _tabela_valida(dados, coluna_data, coluna_modalidade, coluna_valor) -> pd.DataFrame:
        tabela = dados[[coluna_data, coluna_modalidade, coluna_valor]].copy()
        tabela[coluna_data] = pd.to_datetime(tabela[coluna_data], errors="coerce")
        tabela[coluna_valor] = pd.to_numeric(tabela[coluna_valor], errors="coerce")
        return tabela.dropna()

    @staticmethod
    def _fmt(valor, casas: int = 2) -> str:
        """Formata número com vírgula decimal."""
        return f"{float(valor):.{casas}f}".replace(".", ",")

    @staticmethod
    def _mes(data) -> str:
        """Formata uma data como mm/aaaa."""
        return pd.Timestamp(data).strftime("%m/%Y")

    def _periodo_texto(self, datas: pd.Series) -> str:
        return f"{self._mes(datas.min())} a {self._mes(datas.max())}"

    @staticmethod
    def _nome_coluna(coluna: str) -> str:
        return NOMES_MACRO.get(coluna, str(coluna))
