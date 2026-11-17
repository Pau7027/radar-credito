

from src.fonte_dados import FonteBCB

fonte = FonteBCB()

series = {
    "Total": 21082,
    "Pessoa física": 21084,
    "Cheque especial": 21113,
    "Cartão de crédito": 21129,
}

for nome, codigo in series.items():
    tabela = fonte.obter_series(codigo, "01/11/2016", "31/10/2026")
    print(f"\n{nome} (série {codigo}): {len(tabela)} registros")
    print(tabela.head(3))
    print(tabela.tail(3))