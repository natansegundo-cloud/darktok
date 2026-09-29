# Lessons

- Todo clipe carrega fala ou voz off; silêncio só como golpe, no máximo 1 por episódio.
- O board já mostra o resumo em português; `studio session` permanece na Fase 2, que não foi
  antecipada nesta fase de autoria.
- Um beat abstrato não basta para o modo econômico: cada vídeo precisa de estado inicial,
  ações temporizadas, reação visível, estado final, som e restrições de continuidade.

- Imagens derivadas devem começar com a instrução de referência para preservar rosto, cabelo,
  roupa, sala e iluminação.
- O `lock_block` deve acompanhar exatamente a imagem aprovada e ser copiado literalmente.
- Imagem é gratuita; todos os custos de vídeo, por resolução e duração, vêm exclusivamente de
  `config/production.yaml`. Custo `null` é desconhecido e deve bloquear o cálculo.
- Perfil de produção segue a precedência episódio → série → `active_profile`; a resolução e a
  faixa de duração devem ser verificadas antes de gerar mídia.
- `voice_notes` pode registrar contexto de autoria, mas nunca deve virar instrução no prompt:
  use `delivery` da fala e, como fallback, um único `default_delivery` do personagem; mantenha
  sempre o espelho `_pt`.
- O ritmo econômico precisa bloquear fala curta demais quando configurado: o lint informa quantos
  segundos faltam preencher, valida o gancho antes de 2 s, o cliffhanger e o runtime com cold open.
- `series/revenge_republic` é apenas fixture pausada de testes; a série real ainda não existe.
