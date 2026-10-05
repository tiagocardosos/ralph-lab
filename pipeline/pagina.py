"""Etapa 3: index.html com o grafico SVG da receita mensal por regiao e a conclusao."""

import csv
import math
from decimal import Decimal
from html import escape

from pipeline import join, pivot

ENTRADA = pivot.SAIDA
SAIDA = join.RAIZ / "index.html"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# Paleta categorica (claro, escuro) validada com o validate_palette.js da skill
# dataviz. A regiao pega o slot pela posicao no pivot (ordem alfabetica), nunca
# pelo ranking; os slots nao sao reciclados.
CORES = [
    ("#2a78d6", "#3987e5"),
    ("#eb6834", "#d95926"),
    ("#1baf7a", "#199e70"),
    ("#eda100", "#c98500"),
    ("#e87ba4", "#d55181"),
    ("#008300", "#008300"),
    ("#4a3aa7", "#9085e9"),
    ("#e34948", "#e66767"),
]

# Geometria do SVG (viewBox) e margens da area de plotagem.
LARGURA, ALTURA = 760, 380
ESQ, DIR, TOPO, BASE = 64, 112, 48, 36

ESTILO = """\
:root {
  color-scheme: light dark;
  --plano: #f9f9f7; --superficie: #fcfcfb; --borda: rgba(11,11,11,0.10);
  --tinta: #0b0b0b; --tinta-2: #52514e; --tinta-3: #898781;
  --grade: #e1e0d9; --eixo: #c3c2b7;
%s
}
@media (prefers-color-scheme: dark) {
  :root {
    --plano: #0d0d0d; --superficie: #1a1a19; --borda: rgba(255,255,255,0.10);
    --tinta: #ffffff; --tinta-2: #c3c2b7; --tinta-3: #898781;
    --grade: #2c2c2a; --eixo: #383835;
%s
  }
}
body { margin: 0; background: var(--plano); color: var(--tinta);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 820px; margin: 0 auto; padding: 32px 20px 48px; }
h1 { font-size: 1.6rem; margin: 0 0 4px; }
.subtitulo, .nota { color: var(--tinta-2); margin: 0; }
.nota { font-size: 0.85rem; margin-top: 24px; }
figure { margin: 24px 0; padding: 16px; background: var(--superficie);
  border: 1px solid var(--borda); border-radius: 8px; }
svg { display: block; width: 100%%; height: auto; }
svg text { fill: var(--tinta-3); font-size: 12px; font-variant-numeric: tabular-nums; }
svg .legenda text, svg .rotulo { fill: var(--tinta-2); }
.grade line { stroke: var(--grade); stroke-width: 1; }
.eixo { stroke: var(--eixo); stroke-width: 1; }
.serie polyline, .chave-linha { fill: none; stroke: var(--cor); stroke-width: 2;
  stroke-linejoin: round; stroke-linecap: round; }
.serie circle { fill: var(--cor); stroke: var(--superficie); stroke-width: 2; }
.coluna rect { fill: transparent; }
.coluna line { stroke: var(--tinta-3); stroke-width: 1; opacity: 0; }
.coluna:hover line, .coluna:focus line { opacity: 1; }
.coluna:focus { outline: none; }
table { width: 100%%; border-collapse: collapse; font-size: 0.9rem;
  font-variant-numeric: tabular-nums; }
caption { text-align: left; color: var(--tinta-2); padding-bottom: 8px; }
th, td { padding: 6px 8px; border-bottom: 1px solid var(--grade); text-align: right; }
th:first-child { text-align: left; white-space: nowrap; }
tfoot th, tfoot td { font-weight: 600; border-bottom: none; }
.chave { display: inline-block; width: 16px; height: 2px; margin-right: 8px;
  vertical-align: middle; background: var(--cor); }
.conclusao { margin: 24px 0 0; }
"""


def ler_pivot(caminho):
    """Devolve (meses, {regiao: [receita de cada mes]}) lidos do pivot_receita.csv."""
    with open(caminho, newline="", encoding="utf-8") as f:
        cabecalho, *linhas = csv.reader(f)
    return cabecalho[1:], {l[0]: [Decimal(v) for v in l[1:]] for l in linhas}


def numero(valor):
    """1234567.8 -> '1.234.567,80' (padrao brasileiro, 2 casas)."""
    texto = f"{valor.quantize(join.CENTAVO):,.2f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def brl(valor):
    return f"R$ {numero(valor)}"


def rotulo_mes(mes):
    """'2026-03' -> 'mar/26'."""
    ano, m = mes.split("-")
    return f"{MESES[int(m) - 1]}/{ano[2:]}"


def juntar(itens):
    """['a', 'b', 'c'] -> 'a, b e c'."""
    itens = list(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1] if len(itens) > 1 else "".join(itens)


def passo_eixo(maximo, faixas=5):
    """Menor passo redondo (1, 2 ou 5 x 10^k) que cobre o maximo em ate `faixas` faixas."""
    bruto = maximo / faixas
    potencia = Decimal(10) ** (len(str(int(bruto))) - 1)
    return next(f * potencia for f in (1, 2, 5, 10) if f * potencia >= bruto)


def grafico(meses, tabela):
    """SVG inline de linhas: uma linha por regiao, legenda, meses no eixo x."""
    maximo = max(v for valores in tabela.values() for v in valores)
    passo = passo_eixo(maximo)
    topo = passo * max(1, math.ceil(maximo / passo))
    larg = LARGURA - ESQ - DIR
    alt = ALTURA - TOPO - BASE
    xs = [ESQ + (larg * i / (len(meses) - 1) if len(meses) > 1 else larg / 2)
          for i in range(len(meses))]

    def y(valor):
        return TOPO + alt * (1 - float(valor / topo))

    p = [
        f'<svg viewBox="0 0 {LARGURA} {ALTURA}" role="img" '
        'aria-labelledby="grafico-titulo grafico-desc">',
        '<title id="grafico-titulo">Receita mensal por região (R$)</title>',
        f'<desc id="grafico-desc">Gráfico de linhas com {len(tabela)} regiões '
        f'de {rotulo_mes(meses[0])} a {rotulo_mes(meses[-1])}; '
        'os valores estão na tabela abaixo.</desc>',
        '<g class="legenda">',
    ]
    for i, regiao in enumerate(tabela):
        x = ESQ + 140 * i
        p.append(
            f'<line class="chave-linha" style="--cor: var(--serie-{i + 1})" '
            f'x1="{x}" y1="16" x2="{x + 20}" y2="16"/>'
            f'<text x="{x + 26}" y="20">{escape(regiao)}</text>'
        )
    p.append('</g>\n<g class="grade">')
    for k in range(int(topo / passo) + 1):
        valor = passo * k
        yk = y(valor)
        p.append(
            f'<line x1="{ESQ}" y1="{yk:.1f}" x2="{LARGURA - DIR}" y2="{yk:.1f}"/>'
            f'<text x="{ESQ - 8}" y="{yk + 4:.1f}" text-anchor="end">'
            f'{numero(valor)[:-3]}</text>'
        )
    p.append(
        f'</g>\n<line class="eixo" x1="{ESQ}" y1="{y(0):.1f}" '
        f'x2="{LARGURA - DIR}" y2="{y(0):.1f}"/>'
    )
    for x, mes in zip(xs, meses):
        p.append(
            f'<text x="{x:.1f}" y="{ALTURA - BASE + 22}" text-anchor="middle">'
            f'{rotulo_mes(mes)}</text>'
        )
    for i, (regiao, valores) in enumerate(tabela.items()):
        pontos = [(x, y(v)) for x, v in zip(xs, valores)]
        p.append(f'<g class="serie" style="--cor: var(--serie-{i + 1})">')
        p.append('<polyline points="%s"/>' % " ".join(f"{x:.1f},{yv:.1f}" for x, yv in pontos))
        p.extend(f'<circle cx="{x:.1f}" cy="{yv:.1f}" r="4"/>' for x, yv in pontos)
        x, yv = pontos[-1]
        p.append(f'<text class="rotulo" x="{x + 10:.1f}" y="{yv + 4:.1f}">{escape(regiao)}</text>')
        p.append("</g>")
    # Colunas de hover: mira vertical + tooltip nativo com todas as regioes do mes.
    meia = larg / max(1, len(meses) - 1) / 2
    for j, (x, mes) in enumerate(zip(xs, meses)):
        x0, x1 = max(ESQ, x - meia), min(LARGURA - DIR, x + meia)
        dica = "\n".join(
            [rotulo_mes(mes)] + [f"{brl(v[j])} · {r}" for r, v in tabela.items()]
        )
        p.append(
            f'<g class="coluna" tabindex="0"><title>{escape(dica)}</title>'
            f'<rect x="{x0:.1f}" y="{TOPO}" width="{x1 - x0:.1f}" height="{alt}"/>'
            f'<line x1="{x:.1f}" y1="{TOPO}" x2="{x:.1f}" y2="{TOPO + alt}"/></g>'
        )
    p.append("</svg>")
    return "\n".join(p)


def tabela_html(meses, tabela):
    """Tabela com os mesmos numeros do grafico (acessivel sem hover)."""
    cab = "".join(f"<th>{rotulo_mes(m)}</th>" for m in meses)
    p = [
        "<table>",
        "<caption>Receita por região e mês (R$)</caption>",
        f"<thead><tr><th>Região</th>{cab}<th>Total</th></tr></thead>",
        "<tbody>",
    ]
    for i, (regiao, valores) in enumerate(tabela.items()):
        celulas = "".join(f"<td>{numero(v)}</td>" for v in valores)
        p.append(
            f'<tr><th scope="row"><span class="chave" style="--cor: var(--serie-{i + 1})">'
            f"</span>{escape(regiao)}</th>{celulas}"
            f"<td>{numero(sum(valores, Decimal(0)))}</td></tr>"
        )
    por_mes = [sum(col, Decimal(0)) for col in zip(*tabela.values())]
    total = sum(por_mes, Decimal(0))
    rodape = "".join(f"<td>{numero(v)}</td>" for v in por_mes + [total])
    p += ["</tbody>", f"<tfoot><tr><th>Total</th>{rodape}</tr></tfoot>", "</table>"]
    return "\n".join(p)


def conclusao(meses, tabela, linhas, orfas, sem_venda):
    """Paragrafo de conclusao; todo numero vem do pivot ou da auditoria do join."""
    totais = {r: sum(v, Decimal(0)) for r, v in tabela.items()}
    total = sum(totais.values(), Decimal(0))
    ranking = sorted(totais, key=lambda r: (-totais[r], r))
    lider = ranking[0]
    fatia = str((totais[lider] * 100 / total).quantize(Decimal("0.1"))).replace(".", ",")
    mes_pico, regiao_pico = max(
        ((m, r) for r in tabela for m in range(len(meses))),
        key=lambda mr: tabela[mr[1]][mr[0]],
    )

    texto = (
        f"Entre {rotulo_mes(meses[0])} e {rotulo_mes(meses[-1])}, a receita do relatório "
        f"somou {brl(total)}. O {lider} lidera o semestre com {brl(totais[lider])} "
        f"({fatia}% do total); na sequência vêm "
        f"{juntar(f'{r} ({brl(totais[r])})' for r in ranking[1:])}. "
        f"O melhor mês de uma região foi {rotulo_mes(meses[mes_pico])} no {regiao_pico}, "
        f"com {brl(tabela[regiao_pico][mes_pico])}."
    )
    if orfas:
        ids = juntar(v["id_venda"] for v in orfas)
        lojas = juntar(sorted({v["id_loja"] for v in orfas}))
        texto += (
            f" Ficaram fora desse total as {len(orfas)} vendas órfãs ({ids}), com id_loja "
            f"{lojas} inexistente em lojas.csv, que somam {brl(join.soma_receita(orfas))}."
        )
    for loja in sem_venda:
        regiao = loja["regiao"]
        com_venda = {l["id_loja"] for l in linhas if l["regiao"] == regiao}
        cadastradas = len(com_venda) + sum(1 for s in sem_venda if s["regiao"] == regiao)
        texto += (
            f" Já a loja {loja['id_loja']} {loja['nome_loja']} ({regiao}/{loja['uf']}) não "
            f"registrou nenhuma venda: o {regiao} tem vendas de só {len(com_venda)} das "
            f"{cadastradas} lojas cadastradas e aparece menor do que a operação real."
        )
    return texto


def main():
    meses, tabela = ler_pivot(ENTRADA)
    if len(tabela) > len(CORES):
        raise ValueError(f"{len(tabela)} regioes para {len(CORES)} cores da paleta")
    _, linhas, orfas, sem_venda = join.auditoria()
    texto = conclusao(meses, tabela, linhas, orfas, sem_venda)

    def variaveis(modo, recuo):
        return "\n".join(
            f"{recuo}--serie-{i + 1}: {CORES[i][modo]};" for i in range(len(tabela))
        )

    pagina = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Receita mensal por região</title>
<style>
{ESTILO % (variaveis(0, "  "), variaveis(1, "    "))}</style>
</head>
<body>
<main>
<h1>Receita mensal por região</h1>
<p class="subtitulo">Vendas de {rotulo_mes(meses[0])} a {rotulo_mes(meses[-1])}, \
em R$, a partir do inner join de vendas.csv com lojas.csv.</p>
<figure>
{grafico(meses, tabela)}
</figure>
{tabela_html(meses, tabela)}
<p class="conclusao">{escape(texto)}</p>
<p class="nota">Gerado por pipeline/pagina.py a partir de {ENTRADA.name}.</p>
</main>
</body>
</html>
"""
    with open(SAIDA, "w", encoding="utf-8", newline="\n") as f:
        f.write(pagina)

    print(f"[pagina] grafico {len(tabela)} regioes x {len(meses)} meses -> {SAIDA.name}")
    print(f"[pagina] conclusao com {len(texto)} caracteres")


if __name__ == "__main__":
    main()
