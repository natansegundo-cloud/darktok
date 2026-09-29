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
studio lint revenge_republic ep01
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

## Autoria e ritmo

O agente pode trabalhar dentro do projeto a partir de um brief em português:

```text
studio brief new revenge_republic
studio brief check revenge_republic
studio scaffold revenge_republic ep02
studio validate revenge_republic ep01
studio lint revenge_republic ep01
```

`studio lint` calcula a fala estimada, o preenchimento de cada clipe, o silêncio restante,
beats repetidos e traduções `_pt` ausentes. Consulte `docs/AUTHORING_GUIDE.md` antes de criar
uma série ou episódio. A geração de mídia continua manual e offline.

Para vídeos, os prompts agora carregam direção por tempo: contexto, estado inicial, ações em
ordem, estado final, som e restrições. Escreva o que a câmera deve ver, não apenas a intenção
dramática.

## Fase 1

Esta primeira implementação cobre estrutura, modelos, criação de séries e episódios, validação
geração de prompts e acompanhamento visual da produção. Créditos/alocação, sessão completa,
tentativas avançadas e publicação ficam para fases posteriores.
