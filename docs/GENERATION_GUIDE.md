# Guia de geração — Novelinha Studio

Este é o manual de uso diário. A regra principal é simples:

> Primeiro a imagem. Depois o vídeo usando a imagem aprovada.

O Studio prepara os textos e organiza os arquivos. A geração acontece manualmente no Google
Flow. O áudio já vem dentro do vídeo gerado pelo Flow; não crie áudio externo para o fluxo padrão.

## 1. Entenda os nomes

Cada momento da história é um plano.

| Nome | Significado |
| --- | --- |
| `P03i` | imagem do plano 03 (`i` = image) |
| `P03` | vídeo que anima a imagem `P03i` |
| `anchor_image` | imagem nova, com o cenário e os personagens |
| `derived_image` | nova imagem baseada em uma imagem já existente |
| `video_from_image` | vídeo criado animando uma imagem aprovada |
| `parent` | imagem que deve ser usada como origem/referência |
| `lock_block` | descrição fixa do personagem, copiada sem alterar |
| `status: approved` | humano conferiu e aprovou o resultado |
| `expected_result_pt` | resumo do que precisa aparecer no resultado final |

Exemplo mental:

```text
P03i = foto congelada da cena na mesa
P03  = essa foto ganhando movimento, fala e áudio
```

## 2. Antes de começar

Confira os dados do plano em `shots.yaml`:

- personagens corretos;
- local correto;
- ação principal;
- falas curtas e na ordem certa;
- `parent` apontando para a imagem de origem;
- duração do vídeo (`6`, `8` ou `10` segundos);
- status atual.

Depois rode:

```text
studio brief check revenge_republic
studio bible check revenge_republic
studio validate revenge_republic ep01
studio lint revenge_republic ep01
studio prompts revenge_republic ep01
studio board revenge_republic ep01
```

O lint é obrigatório antes de gerar vídeo. Todo clipe precisa carregar diálogo ou voz off; um
silêncio só pode ser marcado como `intentional_silence` e o episódio aceita no máximo um.
Revise a tabela Rich: ela mostra palavras, segundos de fala, preenchimento e segundos vazios.
Ela também mostra o runtime estimado contra a meta do episódio. Corrija qualquer ERROR de
preenchimento, silêncio excessivo, delivery contraditório ou gancho antes de gerar.
No prompt de vídeo, confira também a sequência `Scene setup` → `Starting state` → `Timed
direction` → `End state`. Ela é a direção para o modelo econômico, não um resumo opcional.

Antes de gerar, confira `studio profile show`. O perfil ativo define a resolução e a faixa de
duração do episódio. `studio profile set monetize` só seleciona a configuração; custos `null`
de 1080p precisam ser preenchidos manualmente em `config/production.yaml` antes de qualquer
comando que calcule custo.

## 3. Gerar uma imagem

1. Abra o documento da cena, por exemplo `prompts/P03.md`, e procure a seção `IMAGEM:`.
2. Copie somente o texto dentro do bloco de código.
3. Gere a imagem no Flow.
4. Se não ficou boa, tente novamente. Imagem não gasta créditos.
5. Quando aprovar, baixe o arquivo com o nome padrão:

```text
series/revenge_republic/episodes/ep01/assets/images/EP01_P03i_image.jpg
```

Se houver tentativas, preserve-as:

```text
EP01_P03i_image_v1.jpg
EP01_P03i_image_v2.jpg
EP01_P03i_image.jpg          ← versão aprovada
```

O `lock_block` deve ser atualizado se a imagem aprovada mostrar cabelo, roupa ou detalhe
 diferente do planejado. Ao mudar o `lock_block`, incremente `lock_version` e registre a decisão
 em `docs/LESSONS.md`.

## 4. Gerar o vídeo

Só faça isso depois de aprovar a imagem de origem.

1. No mesmo documento `prompts/P03.md`, desça até a seção `VIDEO:`.
2. Confira no cabeçalho qual imagem deve ser anexada.
3. No Flow, anexe exatamente o arquivo indicado, como `EP01_P03i_image.jpg`.
4. Copie o prompt inteiro dentro do bloco de código.
5. Gere o vídeo mantendo a duração indicada.
6. Confira rosto, roupa, cenário, movimento, fala e áudio.
7. Baixe o resultado em:

```text
series/revenge_republic/episodes/ep01/assets/videos/EP01_P03_video.mp4
```

Antes de aprovar, compare o vídeo com a linha `Resultado esperado`. Ela é o teste de intenção
do plano: confirma se a ação, a câmera e a fala realmente apareceram.

Tentativas podem ser preservadas assim:

```text
EP01_P03_video_v1.mp4
EP01_P03_video_v2.mp4
EP01_P03_video.mp4          ← versão aprovada
```

O vídeo já deve conter o áudio nativo gerado pelo Flow. Não crie `assets/audio/` nem arquivo de
voz separado para esse fluxo.

## 5. O que fazer depois de baixar

Edite `shots.yaml` e atualize o status do resultado:

```yaml
status: approved
files:
  image: assets/images/EP01_P03i_image.jpg
  video: assets/videos/EP01_P03_video.mp4
```

Para um plano de imagem, preencha apenas `files.image`. Para um plano de vídeo, o `parent` aponta
para o plano cuja imagem será anexada.

## 6. Como acompanhar sem se perder

Use estes comandos:

```text
studio board revenge_republic ep01
```

Mostra a fila inteira, a imagem de origem, o vídeo, o prompt e o próximo passo.

```text
studio next revenge_republic ep01
```

Mostra uma única próxima ação. Se a imagem ainda não estiver aprovada, ele bloqueia o vídeo e
manda gerar/aprovar a imagem primeiro.

### Estados

- `todo`: ainda não começou;
- `prompt_ready`: prompt pronto para copiar;
- `generated`: resultado baixado, ainda não aprovado;
- `approved`: resultado conferido e aprovado;
- `rejected`: resultado não serve e precisa de nova tentativa;
- `edited`: resultado já foi usado na edição.

## 7. Checklist antes de gerar um vídeo

```text
[ ] A imagem parent existe em assets/images/
[ ] A imagem parent está aprovada
[ ] O arquivo anexado é exatamente o indicado no prompt
[ ] O lock_block está consistente com a imagem
[ ] A ação principal é uma só
[ ] Há no máximo duas falas curtas
[ ] A duração está correta
[ ] O custo foi conferido no cabeçalho do prompt
```

## 8. Checklist de ritmo antes de gerar o vídeo

```text
[ ] Há fala ou voice_over_pt; silêncio está marcado apenas como golpe intencional
[ ] Há no máximo duas linhas faladas, com no máximo 15 palavras cada
[ ] Cada fala tem um delivery único; `voice_notes` não deve aparecer no prompt
[ ] beat_pt diz o que muda na história e não repete o beat anterior
[ ] A timeline descreve ações visíveis com início, reação e estado final
[ ] Sound e Do not estão coerentes com a continuidade da cena
[ ] Campos em inglês usados no prompt têm seus espelhos _pt
[ ] studio lint não retorna ERROR
[ ] O runtime estimado está dentro de 10% da meta, ou o aviso foi revisado
```

## 9. Checklist antes de editar o episódio

```text
[ ] Todas as imagens necessárias foram aprovadas
[ ] Todos os vídeos necessários foram aprovados
[ ] Os caminhos em shots.yaml apontam para arquivos reais
[ ] O cold open está configurado em episode.yaml
[ ] A ordem dos planos está correta
[ ] O vídeo final será montado no CapCut
```
