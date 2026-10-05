# Pipeline de vendas: do CSV ao gráfico

Pipeline em Python (só biblioteca padrão) que lê `vendas.csv` (423 vendas) e
`lojas.csv` (8 lojas) e gera, na raiz do repositório, três entregáveis:

| Etapa | Módulo | Lê | Grava |
| --- | --- | --- | --- |
| 1. join | `pipeline/join.py` | `vendas.csv`, `lojas.csv` | `vendas_lojas.csv` |
| 2. pivot | `pipeline/pivot.py` | `vendas_lojas.csv` | `pivot_receita.csv` (região × mês) |
| 3. página | `pipeline/pagina.py` | `pivot_receita.csv` | `index.html` (gráfico SVG + conclusão) |

## Como rodar

Da raiz do repositório:

```sh
python3 -m pipeline
```

O comando roda join → pivot → página nessa ordem, imprime a auditoria de cada
etapa e regenera os três arquivos. A saída é determinística: rodar duas vezes
não muda nenhum byte. Cada etapa também roda sozinha
(`python3 -m pipeline.join`, `python3 -m pipeline.pivot`, `python3 -m pipeline.pagina`).

Para ver a página, abra `index.html` no navegador; ela é um arquivo único, sem
JavaScript nem CSS externo.

## Como testar

```sh
python3 -m compileall -q pipeline tests          # checagem de sintaxe
python3 -m pytest -q                             # com pytest instalado
uv run --no-project --with pytest python -m pytest -q   # sem pytest local
```

Os testes ficam em `tests/test_*.py` e só usam pytest e a biblioteca padrão:
`test_join.py`, `test_pivot.py`, `test_pagina.py` e `test_ponta_a_ponta.py`
(roda `python3 -m pipeline` num subprocesso, confere os três arquivos e que
uma segunda execução não muda nenhum byte).

## Decisão de join: inner join por `id_loja`

`vendas_lojas.csv` é o **inner join** de `vendas.csv` com `lojas.csv` pela
coluna `id_loja`: só entram vendas cuja loja existe em `lojas.csv`. Os dados
de origem não são editados nem "consertados"; o que o inner join descarta é
impresso pela etapa de join e citado na conclusão da página.

Auditoria (saída de `python3 -m pipeline`):

- **423 → 420 linhas**: das 423 vendas lidas, 420 entram no join, somando
  R$ 931.274,06 de receita.
- **3 vendas órfãs fora**: `V00421`, `V00422` e `V00423` têm `id_loja = 999`,
  que não existe em `lojas.csv`. Elas somam **R$ 8.120,00** e ficam fora do
  join, do pivot e do gráfico.
- **Loja 108 (Batel/PR, Sul) ausente do pivot**: ela está em `lojas.csv` mas não
  tem nenhuma venda, então não gera linha no join nem contribui para o pivot.
  O Sul aparece só com as vendas da loja 107 (Moinhos), **menor do que a
  operação real** da região, que tem 2 lojas cadastradas.

Todos os números acima são calculados dos CSVs pelo pipeline; nenhum valor é
digitado à mão nos entregáveis.
