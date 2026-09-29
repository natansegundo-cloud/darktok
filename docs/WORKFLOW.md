# Fluxo de trabalho

1. Salve o roteiro em `script.md` e quebre o episódio em planos em `shots.yaml`.
2. Rode `studio board <series> <episode>` para enxergar a fila.
3. Rode `studio next <series> <episode>` para saber a próxima ação.
4. Gere a imagem primeiro, baixe-a em `assets/images/` e marque o plano como aprovado.
5. Só depois copie o prompt de vídeo, anexe a imagem aprovada e gere o vídeo.
6. Baixe o vídeo em `assets/videos/` e marque o plano como aprovado.
7. Ajuste o `lock_block` para refletir a imagem aprovada, incrementando `lock_version`.
8. Rode `studio validate` e `studio prompts` novamente quando necessário.

Antes de gerar vídeos, rode `studio plan <series> <episode>` para reservar custo e conta; compare
o caso esperado com o pior caso de tentativas. Use `studio plan-day` para a capacidade diária e
`studio session <series> <episode> [--account conta1]` para a fila manual, com imagens antes dos
vídeos e os anexos indicados.

## Regra visual simples

Um plano de imagem termina em `i`: `P03i`. O plano de vídeo usa essa imagem: `P03`.

```text
P03i → gerar imagem → salvar em assets/images → aprovar
 P03 → anexar P03i → gerar vídeo com áudio nativo → salvar em assets/videos → aprovar
```

Não crie arquivos de áudio externos no fluxo padrão.

O Studio não acessa contas, não gera mídia e não faz chamadas de rede.
