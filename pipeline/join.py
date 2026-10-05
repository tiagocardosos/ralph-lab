"""Etapa 1: inner join de vendas.csv com lojas.csv por id_loja."""

import csv
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VENDAS = RAIZ / "vendas.csv"
LOJAS = RAIZ / "lojas.csv"
SAIDA = RAIZ / "vendas_lojas.csv"

CAMPOS_VENDA = ["id_venda", "data", "id_loja", "categoria", "unidades", "receita_brl"]
CAMPOS_LOJA = ["nome_loja", "regiao", "uf"]
CABECALHO = CAMPOS_VENDA + CAMPOS_LOJA

CENTAVO = Decimal("0.01")


def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def inner_join(vendas, lojas):
    """Devolve (linhas do join, vendas orfas, lojas sem venda).

    So entram vendas cujo id_loja existe em lojas; o que fica de fora e
    devolvido para ser reportado, nunca descartado em silencio.
    """
    por_id = {loja["id_loja"]: loja for loja in lojas}
    linhas, orfas = [], []
    for venda in vendas:
        loja = por_id.get(venda["id_loja"])
        if loja is None:
            orfas.append(venda)
            continue
        linha = {c: venda[c] for c in CAMPOS_VENDA}
        linha.update({c: loja[c] for c in CAMPOS_LOJA})
        linhas.append(linha)
    com_venda = {venda["id_loja"] for venda in vendas}
    sem_venda = [loja for loja in lojas if loja["id_loja"] not in com_venda]
    return linhas, orfas, sem_venda


def soma_receita(linhas):
    return sum((Decimal(l["receita_brl"]) for l in linhas), Decimal(0))


def auditoria():
    """Le os CSVs de origem e devolve tudo o que o join usa e descarta."""
    vendas = ler_csv(VENDAS)
    lojas = ler_csv(LOJAS)
    linhas, orfas, sem_venda = inner_join(vendas, lojas)
    return vendas, linhas, orfas, sem_venda


def main():
    vendas, linhas, orfas, sem_venda = auditoria()
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CABECALHO)
        escritor.writeheader()
        escritor.writerows(linhas)

    ids_orfas = ", ".join(v["id_venda"] for v in orfas)
    valor_orfas = soma_receita(orfas).quantize(CENTAVO)
    lojas_vazias = ", ".join(f'{l["id_loja"]} {l["nome_loja"]}' for l in sem_venda)
    print(f"[join] {len(vendas)} vendas lidas")
    print(f"[join] {len(linhas)} no join (inner por id_loja) -> {SAIDA.name}")
    print(f"[join] receita no join: R$ {soma_receita(linhas).quantize(CENTAVO)}")
    print(f"[join] {len(orfas)} orfas descartadas ({ids_orfas}; R$ {valor_orfas})")
    print(f"[join] lojas sem venda: {lojas_vazias or 'nenhuma'}")


if __name__ == "__main__":
    main()
