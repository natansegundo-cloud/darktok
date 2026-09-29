# Production board — Revenge Republic · ep01

> Use `studio next` para executar somente a próxima ação. `MISSING` indica que o caminho foi registrado, mas o arquivo ainda não está na pasta.

| Ordem | Plano | Etapa | Status | Imagem de origem | Vídeo | Prompt | Créditos | Próxima ação |
| ---: | --- | --- | --- | --- | --- | --- | ---: | --- |
| 0 | **P01i** | IMAGE | approved | `assets/images/EP01_P01i_image.jpg` (MISSING) | — | `prompts/P01.md` | 0 | Colocar imagem em assets/images/EP01_P01i_image.jpg |
| 1 | **P01** | VIDEO | imagem approved / vídeo approved | `assets/images/EP01_P01i_image.jpg` (MISSING) | `assets/videos/EP01_P01_video.mp4` (MISSING) | `prompts/P01.md` | 6 | Colocar imagem aprovada de P01i em assets/images/EP01_P01i_image.jpg |
| 2 | **P02i** | IMAGE | approved | `assets/images/EP01_P02i_image.jpg` (MISSING) | — | `prompts/P02.md` | 0 | Colocar imagem em assets/images/EP01_P02i_image.jpg |
| 3 | **P02** | VIDEO | imagem approved / vídeo approved | `assets/images/EP01_P02i_image.jpg` (MISSING) | `assets/videos/EP01_P02_video.mp4` (MISSING) | `prompts/P02.md` | 6 | Colocar imagem aprovada de P02i em assets/images/EP01_P02i_image.jpg |
| 4 | **P03i** | IMAGE | approved | `assets/images/EP01_P03i_image.jpg` (MISSING) | — | `prompts/P03.md` | 0 | Colocar imagem em assets/images/EP01_P03i_image.jpg |
| 5 | **P03** | VIDEO | imagem approved / vídeo approved | `assets/images/EP01_P03i_image.jpg` (MISSING) | `assets/videos/EP01_P03_video.mp4` (MISSING) | `prompts/P03.md` | 6 | Colocar imagem aprovada de P03i em assets/images/EP01_P03i_image.jpg |
| 6 | **P04i** | IMAGE | todo | — | — | `prompts/P04.md` | 0 | Gerar imagem · copiar prompts/P04.md, seção IMAGEM |
| 7 | **P04** | VIDEO | imagem todo / vídeo todo | — | — | `prompts/P04.md` | 6 | Aguardar aprovação de P04i |
| 8 | **P05i** | IMAGE | todo | — | — | `prompts/P05.md` | 0 | Gerar imagem · copiar prompts/P05.md, seção IMAGEM |
| 9 | **P05** | VIDEO | imagem todo / vídeo todo | — | — | `prompts/P05.md` | 6 | Aguardar aprovação de P05i |
| 10 | **P06i** | IMAGE | todo | — | — | `prompts/P06.md` | 0 | Gerar imagem · copiar prompts/P06.md, seção IMAGEM |
| 11 | **P06** | VIDEO | imagem todo / vídeo todo | — | — | `prompts/P06.md` | 7 | Aguardar aprovação de P06i |

## Regra do fluxo

`P03i` é a imagem. `P03` é o vídeo que deve anexar a imagem `P03i`.
O vídeo só deve ser gerado depois que a imagem de origem estiver aprovada.
