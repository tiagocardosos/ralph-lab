import contextlib
import csv
import io
import re
from decimal import Decimal

import pytest

from pipeline import join, pivot


@pytest.fixture(scope="module")
def execucao():
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        join.main()
        pivot.main()
    with open(pivot.SAIDA, newline="", encoding="utf-8") as f:
        linhas = list(csv.reader(f))
    return linhas[0], linhas[1:], saida.getvalue()


def test_cabecalho_exato(execucao):
    cabecalho, _, _ = execucao
    assert cabecalho == [
        "regiao", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
    ]


def test_forma_4_por_7_em_ordem_alfabetica(execucao):
    _, dados, _ = execucao
    assert len(dados) == 4
    assert all(len(linha) == 7 for linha in dados)
    assert [linha[0] for linha in dados] == ["Centro-Oeste", "Nordeste", "Sudeste", "Sul"]


def test_valores_com_duas_casas(execucao):
    _, dados, _ = execucao
    assert all(re.fullmatch(r"\d+\.\d{2}", v) for linha in dados for v in linha[1:])


def test_receita_total_do_pivot(execucao):
    _, dados, _ = execucao
    total = sum(Decimal(v) for linha in dados for v in linha[1:])
    assert abs(total - Decimal("931274.06")) <= Decimal("0.50")


def test_sudeste(execucao):
    _, dados, _ = execucao
    sudeste = next(linha for linha in dados if linha[0] == "Sudeste")
    assert sum(Decimal(v) for v in sudeste[1:]) == Decimal("265077.49")


def test_pivot_le_o_join(execucao):
    _, _, saida = execucao
    assert pivot.ENTRADA == join.SAIDA
    assert "4 regioes x 6 meses" in saida
