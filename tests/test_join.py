import contextlib
import csv
import io
from decimal import Decimal

import pytest

from pipeline import join


def contar_linhas(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


@pytest.fixture(scope="module")
def execucao():
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        join.main()
    with open(join.SAIDA, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        return leitor.fieldnames, list(leitor), saida.getvalue()


def test_cabecalho(execucao):
    cabecalho, _, _ = execucao
    assert cabecalho == [
        "id_venda", "data", "id_loja", "categoria", "unidades", "receita_brl",
        "nome_loja", "regiao", "uf",
    ]


def test_join_tem_420_linhas(execucao):
    _, linhas, _ = execucao
    assert len(linhas) == 420


def test_receita_total_do_join(execucao):
    _, linhas, _ = execucao
    total = sum(Decimal(l["receita_brl"]) for l in linhas)
    assert total == Decimal("931274.06")


def test_sem_loja_999(execucao):
    _, linhas, _ = execucao
    assert all(l["id_loja"] != "999" for l in linhas)


def test_ordem_e_receita_iguais_a_origem(execucao):
    _, linhas, _ = execucao
    esperado = [
        (v["id_venda"], v["receita_brl"])
        for v in join.ler_csv(join.VENDAS)
        if v["id_loja"] != "999"
    ]
    assert [(l["id_venda"], l["receita_brl"]) for l in linhas] == esperado


def test_auditoria_impressa(execucao):
    _, _, saida = execucao
    assert "423 vendas lidas" in saida
    assert "420 no join" in saida
    assert "3 orfas descartadas (V00421, V00422, V00423; R$ 8120.00)" in saida
    assert "108 Batel" in saida


def test_fontes_intactas(execucao):
    assert contar_linhas(join.VENDAS) == 423
    assert contar_linhas(join.LOJAS) == 8
