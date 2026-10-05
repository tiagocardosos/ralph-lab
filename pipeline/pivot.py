"""Etapa 2: pivot da receita por regiao x mes a partir de vendas_lojas.csv."""

import csv
from collections import defaultdict
from decimal import Decimal

from pipeline import join

ENTRADA = join.SAIDA
SAIDA = join.RAIZ / "pivot_receita.csv"


def pivotar(linhas):
    """Devolve (meses, {regiao: {mes: receita}}) com somas exatas em Decimal.

    Meses (data[:7]) e regioes saem em ordem crescente; uma regiao sem venda
    num mes recebe Decimal(0), para a tabela ficar sempre retangular.
    """
    somas = defaultdict(lambda: defaultdict(Decimal))
    for linha in linhas:
        somas[linha["regiao"]][linha["data"][:7]] += Decimal(linha["receita_brl"])
    meses = sorted({mes for por_mes in somas.values() for mes in por_mes})
    tabela = {
        regiao: {mes: somas[regiao][mes] for mes in meses}
        for regiao in sorted(somas)
    }
    return meses, tabela


def main():
    meses, tabela = pivotar(join.ler_csv(ENTRADA))
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["regiao"] + meses)
        for regiao, por_mes in tabela.items():
            escritor.writerow(
                [regiao] + [str(por_mes[mes].quantize(join.CENTAVO)) for mes in meses]
            )

    total = sum((v for por_mes in tabela.values() for v in por_mes.values()), Decimal(0))
    print(f"[pivot] {len(tabela)} regioes x {len(meses)} meses -> {SAIDA.name}")
    print(f"[pivot] receita no pivot: R$ {total.quantize(join.CENTAVO)}")


if __name__ == "__main__":
    main()
