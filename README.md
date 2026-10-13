# Prisssma Lab · LP do Caderno das Boas Ideias

Landing page de venda do Caderno das Boas Ideias (R$ 67, checkout Kiwify).

- `src.html`: fonte da página, com marcadores `{{GABI}}`, `{{DEPO1..8}}` e `{{S###}}` para as imagens.
- `assets/`: foto da Gabi, prints de depoimentos e páginas do caderno (`sNNN.jpg` = página NNN do PDF).
- `build.py`: gera o `index.html` com as imagens embutidas (`python3 build.py`).
- `index.html`: página final, pronta para abrir ou publicar.

Para o WordPress, use as imagens de `assets/` como arquivos separados em vez das embutidas.
