# PRD: Pipeline de vendas — do CSV ao gráfico

## Introdução

O repositório `ralph-lab` tem dois CSVs sintéticos na raiz: `vendas.csv` (423 vendas, colunas `id_venda,data,id_loja,categoria,unidades,receita_brl`) e `lojas.csv` (8 lojas, colunas `id_loja,nome_loja,regiao,uf,gerente`). O objetivo é um pipeline reproduzível que produza, **na raiz do repositório**, três entregáveis:

1. `vendas_lojas.csv` — o **inner join** das vendas com as lojas por `id_loja`;
2. `pivot_receita.csv` — a receita por **região × mês**;
3. `index.html` — uma página estática com o gráfico da receita mensal por região e um parágrafo de conclusão.

Os dados têm duas armadilhas propositais, que o pipeline precisa tratar **e reportar**, não esconder:

- **3 vendas órfãs** (`V00421`, `V00422`, `V00423`) com `id_loja = 999`, que não existe em `lojas.csv` (R$ 8.120,00 no total);
- **a loja 108 (Batel/PR, região Sul)** existe em `lojas.csv` mas não tem nenhuma venda.

## Perguntas de esclarecimento e respostas

```
1. Qual tipo de join gera vendas_lojas.csv?
   A. Inner join por id_loja (só vendas com loja conhecida)
   B. Left join a partir de vendas.csv (órfãs ficam, sem região)
   C. Left join a partir de lojas.csv (loja 108 aparece com zero)
   D. Outro
   -> A. O enunciado exige o inner join (420 linhas, R$ 931.274,06). O que o
      inner join descarta (3 órfãs e a loja 108) é impresso numa auditoria e
      citado na conclusão da página, para não sumir em silêncio.

2. Com que stack o pipeline é escrito?
   A. Python, só biblioteca padrão (csv, decimal)
   B. Python com pandas
   C. JavaScript/Node
   D. Outro
   -> A. Os testes são executados pela correção com `python -m pytest` num
      ambiente que NÃO tem pandas. Qualquer import de pandas quebra a suíte lá.

3. Como o gráfico é desenhado?
   A. SVG inline gerado pelo Python dentro do index.html
   B. Chart.js carregado de CDN
   C. Imagem PNG gerada por matplotlib
   D. Outro
   -> A. Página de um arquivo só, abre offline, sem dependência de rede nem
      de biblioteca de gráfico.

4. Onde mora o código?
   A. Pacote `pipeline/` com um módulo por etapa (join, pivot, página) e um orquestrador
   B. Um script único
   C. Notebook
   D. Outro
   -> A. Uma etapa por história do Ralph; os entregáveis continuam na raiz.

5. Como os testes rodam nesta máquina?
   A. `uv run --no-project --with pytest python -m pytest -q`
   B. Instalar pytest no Python do sistema
   C. Não rodar testes
   D. Outro
   -> A. O Python local não tem pytest; o uv baixa o pytest num ambiente
      efêmero sem mexer no sistema.
```

## Objetivos

- `vendas_lojas.csv` com exatamente **420 linhas de dados** e soma de `receita_brl` = **931274.06** (tolerância 0,005).
- `pivot_receita.csv` com o cabeçalho **exato** `regiao,2026-01,2026-02,2026-03,2026-04,2026-05,2026-06`, **4 linhas de dados × 7 colunas**, soma das células = **931274.06** e Sudeste = **265077.49**.
- `index.html` com um gráfico (`<svg>`) da receita mensal por região e um `<p>` de conclusão com **pelo menos 300 caracteres**.
- Suíte `pytest` em `tests/test_*.py` **inteira verde**, com **pelo menos 4 testes**: linhas do join, receita total, forma do pivot, gráfico na página.
- Pipeline reproduzível com um comando: `python3 -m pipeline`.

## Histórias de usuário

### US-001: Inner join de vendas e lojas
**Descrição:** Como analista, quero `vendas_lojas.csv` com cada venda enriquecida com os dados da loja, para analisar a receita por região.

**Critérios de aceite:**
- [ ] `pipeline/__init__.py` existe e `pipeline/join.py` define `main()` que lê `vendas.csv` e `lojas.csv` da raiz do repositório (caminhos resolvidos a partir de `Path(__file__)`, não do cwd)
- [ ] Gera `vendas_lojas.csv` na raiz com o cabeçalho `id_venda,data,id_loja,categoria,unidades,receita_brl,nome_loja,regiao,uf`, na mesma ordem de `vendas.csv`
- [ ] A coluna se chama exatamente `receita_brl` e o valor é copiado de `vendas.csv` sem alteração
- [ ] Resultado: 420 linhas de dados; nenhuma linha com `id_loja = 999`; soma de `receita_brl` (com `decimal.Decimal`) = 931274.06
- [ ] Imprime uma auditoria: 423 vendas lidas, 420 no join, 3 órfãs descartadas (ids e R$ 8120.00) e lojas sem venda (108 Batel)
- [ ] `vendas.csv` e `lojas.csv` não são modificados (continuam com 423 e 8 linhas de dados)
- [ ] `tests/test_join.py` cobre: 420 linhas, soma 931274.06, ausência de `id_loja` 999 e fontes intactas
- [ ] `python3 -m compileall -q pipeline tests` passa
- [ ] `uv run --no-project --with pytest python -m pytest -q` passa

### US-002: Pivot de receita por região × mês
**Descrição:** Como analista, quero `pivot_receita.csv` com a receita de cada região em cada mês, para comparar regiões ao longo do semestre.

**Critérios de aceite:**
- [ ] `pipeline/pivot.py` define `main()` que lê `vendas_lojas.csv` (não os CSVs de origem) e grava `pivot_receita.csv` na raiz
- [ ] Cabeçalho exato: `regiao,2026-01,2026-02,2026-03,2026-04,2026-05,2026-06` (mês = `data[:7]`)
- [ ] 4 linhas de dados em ordem alfabética: Centro-Oeste, Nordeste, Sudeste, Sul
- [ ] Valores com ponto decimal e exatamente 2 casas (`265077.49`), sem `R$` e sem separador de milhar; somas com `Decimal`, arredondadas só na escrita
- [ ] A soma de todas as células numéricas = 931274.06 (± 0,50) e a soma da linha Sudeste = 265077.49
- [ ] `tests/test_pivot.py` cobre: cabeçalho exato, forma 4 × 7, total 931274.06 e Sudeste 265077.49
- [ ] `python3 -m compileall -q pipeline tests` passa
- [ ] `uv run --no-project --with pytest python -m pytest -q` passa

### US-003: Página com gráfico e conclusão
**Descrição:** Como gestor, quero abrir `index.html` e ver a receita mensal de cada região num gráfico, com uma conclusão escrita, para entender o semestre sem abrir planilha.

**Critérios de aceite:**
- [ ] `pipeline/pagina.py` define `main()` que lê `pivot_receita.csv` e grava `index.html` na raiz
- [ ] A página é um arquivo só: gráfico de linhas em `<svg>` inline (uma linha por região, legenda, meses no eixo x), sem `<script src>` nem CSS externo
- [ ] Um `<p>` de conclusão com pelo menos 300 caracteres, com números calculados dos dados (nada digitado à mão): região líder (Sudeste, R$ 265.077,49), receita total do relatório (R$ 931.274,06), e o que ficou de fora — as 3 vendas órfãs (R$ 8.120,00) e a loja 108 Batel, sem vendas
- [ ] `tests/test_pagina.py` cobre: `index.html` existe, contém `<svg`, tem um `<p>` com 300+ caracteres e cita Sudeste
- [ ] Verificação no navegador: se não houver ferramenta de navegador disponível, registrar no `progress.txt` que a verificação visual manual é necessária (não bloqueia a história)
- [ ] `python3 -m compileall -q pipeline tests` passa
- [ ] `uv run --no-project --with pytest python -m pytest -q` passa

### US-004: Orquestração e documentação da decisão de join
**Descrição:** Como mantenedor, quero rodar o pipeline inteiro com um comando e ler no README qual join foi usado e o que ele descartou.

**Critérios de aceite:**
- [ ] `pipeline/__main__.py` roda join → pivot → página em ordem; `python3 -m pipeline` regenera os três entregáveis de forma idêntica (rodar duas vezes não muda nenhum byte)
- [ ] `README.md` na raiz explica: como rodar, como testar, o inner join escolhido e os números da auditoria (423 → 420 linhas; 3 órfãs, R$ 8.120,00 fora; loja 108 ausente do pivot, então o Sul aparece menor do que a operação real)
- [ ] Um teste de ponta a ponta em `tests/` roda `python3 -m pipeline` num subprocesso e confere que os três arquivos existem
- [ ] A suíte inteira tem pelo menos 4 testes e todos passam
- [ ] `python3 -m compileall -q pipeline tests` passa
- [ ] `uv run --no-project --with pytest python -m pytest -q` passa

## Requisitos funcionais

- FR-1: O join usa `id_loja` como chave e é **inner**: só entram vendas cujo `id_loja` existe em `lojas.csv`.
- FR-2: `receita_brl` é lida como número (`decimal.Decimal`), nunca somada como texto. Os valores vêm em formatos como `349.5`, `1200` e `4406.88`.
- FR-3: Nenhum CSV de origem é editado, e nenhuma linha é apagada deles. Problemas de dados são tratados no pipeline e reportados.
- FR-4: Nenhum número é inventado: todo valor de saída (CSV, gráfico, conclusão) é calculado a partir dos CSVs de origem.
- FR-5: Os entregáveis `vendas_lojas.csv`, `pivot_receita.csv` e `index.html` ficam na **raiz** do repositório, com esses nomes exatos.
- FR-6: Os testes ficam em `tests/test_*.py` e usam só a biblioteca padrão + pytest.

## Fora de escopo

- Não usar pandas, numpy, matplotlib nem qualquer pacote fora da biblioteca padrão no pipeline e nos testes.
- Não "consertar" os dados: nada de mapear `id_loja = 999` para uma loja real.
- Não criar servidor web, build de frontend nem dependência de CDN.
- Não mover os entregáveis para `data/` ou `web/`.

## Considerações técnicas

- Rodar tudo a partir da raiz do repositório. O `prd.json` e o `progress.txt` do Ralph ficam em `scripts/ralph/`.
- A correção executa `python -m pytest -q --tb=no` na raiz num Python **sem pandas e sem uv**; por isso os testes não podem depender de nada além de pytest e da biblioteca padrão.
- Números de conferência: 423 vendas; 8 lojas; 420 no inner join; soma no join 931274.06; soma de todas as vendas 939394.06; órfãs `V00421`–`V00423` somam 8120.00; Sudeste 265077.49.

## Métricas de sucesso

- `uv run --no-project --with pytest python -m pytest -q` verde com ≥ 4 testes.
- Os valores de conferência acima batem nos arquivos entregues.

## Questões em aberto

- Nenhuma que bloqueie a implementação.
