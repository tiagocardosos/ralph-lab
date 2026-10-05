import contextlib
import html
import io
import re
from decimal import Decimal
from pathlib import Path

import pytest

from pipeline import join, pagina, pivot


def paragrafos(pagina_html):
    """Texto puro (sem tags, entidades resolvidas) de cada <p> da pagina."""
    return [
        html.unescape(re.sub(r"<[^>]+>", "", corpo))
        for corpo in re.findall(r"<p\b[^>]*>(.*?)</p>", pagina_html, re.S)
    ]


@pytest.fixture(scope="module")
def execucao():
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        join.main()
        pivot.main()
        pagina.main()
    return pagina.SAIDA.read_text(encoding="utf-8"), saida.getvalue()


@pytest.fixture(scope="module")
def conclusao(execucao):
    pagina_html, _ = execucao
    return max(paragrafos(pagina_html), key=len)


def test_index_html_existe_na_raiz(execucao):
    assert pagina.SAIDA == join.RAIZ / "index.html"
    assert pagina.SAIDA.is_file()
    assert pagina.ENTRADA == pivot.SAIDA


def test_grafico_svg_inline(execucao):
    pagina_html, _ = execucao
    assert "<svg" in pagina_html
    assert not re.search(r"<script\b[^>]*\bsrc=", pagina_html)
    assert not re.search(r"<link\b[^>]*stylesheet", pagina_html)


def test_uma_linha_por_regiao_com_legenda_e_meses(execucao):
    pagina_html, _ = execucao
    svg = pagina_html[pagina_html.index("<svg"):pagina_html.index("</svg>")]
    assert svg.count("<polyline") == 4
    legenda = svg[svg.index('<g class="legenda">'):]
    legenda = legenda[:legenda.index("</g>")]
    for regiao in ["Centro-Oeste", "Nordeste", "Sudeste", "Sul"]:
        assert f">{regiao}</text>" in legenda
    for mes in ["jan/26", "fev/26", "mar/26", "abr/26", "mai/26", "jun/26"]:
        assert f">{mes}</text>" in svg


def test_conclusao_com_300_caracteres_cita_sudeste(conclusao):
    assert len(conclusao) >= 300
    assert "Sudeste" in conclusao


def test_conclusao_cita_numeros_e_o_que_ficou_de_fora(conclusao):
    assert "R$ 265.077,49" in conclusao
    assert "R$ 931.274,06" in conclusao
    assert "3 vendas órfãs" in conclusao
    assert "R$ 8.120,00" in conclusao
    assert "loja 108 Batel" in conclusao


def luminancia(cor):
    """Luminancia relativa WCAG 2.x de '#rrggbb'."""
    canais = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def razao_contraste(a, b):
    claro, escuro = sorted([luminancia(a), luminancia(b)], reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def test_cores_das_series_com_contraste_3_para_1(execucao):
    pagina_html, _ = execucao
    estilo = re.search(r"<style>(.*?)</style>", pagina_html, re.S).group(1)
    claro, escuro = estilo.split("@media (prefers-color-scheme: dark)")
    for modo, bloco in [("claro", claro), ("escuro", escuro)]:
        cores = dict(re.findall(r"--(superficie|serie-\d+):\s*(#[0-9a-fA-F]{6});", bloco))
        series = [cores[f"serie-{n}"] for n in range(1, 5)]
        assert len({c.lower() for c in series}) == 4, modo
        for n, cor in enumerate(series, 1):
            razao = razao_contraste(cor, cores["superficie"])
            assert razao >= 3.0, f"{modo}: --serie-{n} {cor} tem {razao:.2f}:1"


def test_regiao_mantem_a_mesma_serie_na_linha_legenda_e_tabela(execucao):
    pagina_html, _ = execucao
    for n, regiao in enumerate(["Centro-Oeste", "Nordeste", "Sudeste", "Sul"], 1):
        var = rf'style="--cor: var\(--serie-{n}\)"'
        assert re.search(rf'class="chave-linha" {var}[^>]*/><text[^>]*>{regiao}</text>',
                         pagina_html)
        assert re.search(rf'<g class="serie" {var}>(?:(?!</g>).)*>{regiao}</text>',
                         pagina_html, re.S)
        assert re.search(rf'<span class="chave" {var}></span>{regiao}</th>', pagina_html)


def test_numeros_nao_digitados_no_codigo():
    fonte = Path(pagina.__file__).read_text(encoding="utf-8")
    for numero in ["265077", "265.077", "931274", "931.274", "8120", "8.120"]:
        assert numero not in fonte


def test_formato_brl():
    assert pagina.brl(Decimal("265077.49")) == "R$ 265.077,49"
    assert pagina.brl(Decimal("8120")) == "R$ 8.120,00"
    assert pagina.brl(Decimal("349.5")) == "R$ 349,50"
