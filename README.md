# Novelinha Studio

CLI offline para organizar a produção de novelinhas verticais feitas manualmente no Google Flow.
O Studio monta prompts, valida arquivos e mantém o estado da produção; ele não gera mídia,
não chama APIs e não automatiza contas.

O áudio é gerado pelo próprio Google Flow dentro do vídeo. O projeto não usa uma etapa de
áudio externo no fluxo padrão.

## Começo rápido

```text
python -m pip install -e ".[dev]"
studio init
studio validate revenge_republic ep01
studio prompts revenge_republic ep01
studio board revenge_republic ep01
studio next revenge_republic ep01
```

O projeto usa a pasta atual como raiz. Dados ficam em YAML/Markdown e mídia fica fora do Git.
Consulte `ofcNOVELINHA_STUDIO_SPEC.md` para a especificação completa.

## Custos atuais em 360p

Imagens custam 0 créditos. Vídeos custam 5 créditos em 6 segundos, 6 créditos em 8 segundos
e 7 créditos em 10 segundos. Esses valores ficam em `config/production.yaml` e podem ser
alterados sem mudar o código.

## Fase 1

Esta primeira implementação cobre estrutura, modelos, criação de séries e episódios, validação
geração de prompts e acompanhamento visual da produção. Créditos/alocação, sessão completa,
tentativas avançadas e publicação ficam para fases posteriores.
