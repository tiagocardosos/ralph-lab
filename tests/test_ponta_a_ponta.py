import hashlib
import subprocess
import sys

import pytest

from pipeline import join, pagina, pivot

ENTREGAVEIS = [join.SAIDA, pivot.SAIDA, pagina.SAIDA]


def rodar_pipeline():
    # sys.executable: a correcao roda sem uv, com o mesmo Python do pytest.
    return subprocess.run(
        [sys.executable, "-m", "pipeline"],
        cwd=join.RAIZ, capture_output=True, text=True, check=True,
    )


def impressoes():
    return {c.name: hashlib.sha256(c.read_bytes()).hexdigest() for c in ENTREGAVEIS}


@pytest.fixture(scope="module")
def execucoes():
    primeira = rodar_pipeline()
    antes = impressoes()
    segunda = rodar_pipeline()
    return primeira.stdout, antes, segunda.stdout, impressoes()


def test_python_m_pipeline_gera_os_tres_arquivos(execucoes):
    for caminho in ENTREGAVEIS:
        assert caminho.parent == join.RAIZ
        assert caminho.is_file() and caminho.stat().st_size > 0
    assert [c.name for c in ENTREGAVEIS] == [
        "vendas_lojas.csv", "pivot_receita.csv", "index.html",
    ]


def test_etapas_rodam_em_ordem(execucoes):
    saida, _, _, _ = execucoes
    etapas = [linha.split("]")[0] + "]" for linha in saida.splitlines()]
    primeira_de = {etapa: etapas.index(etapa) for etapa in ["[join]", "[pivot]", "[pagina]"]}
    assert primeira_de["[join]"] < primeira_de["[pivot]"] < primeira_de["[pagina]"]


def test_rodar_duas_vezes_nao_muda_nenhum_byte(execucoes):
    primeira, antes, segunda, depois = execucoes
    assert antes == depois
    assert primeira == segunda
