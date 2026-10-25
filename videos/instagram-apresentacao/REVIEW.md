# REVIEW — Leme Norte, apresentação Instagram

Arquivo: `leme-norte-apresentacao.mp4` (1080×1920, 30 fps, 46 s, H.264, sem áudio).

## Escolhas
- Roteiro A, "Rumo ao horizonte", escolhido pelo cliente. Os roteiros B (manifesto) e C (do número à decisão) estão em `STORYLINES.md`.
- Experiência: "Desde 2013 cuidando do financeiro de empresas" + Reunião de Rota mensal. CTA: "Siga a Leme Norte" + lemenorte.com.br.
- Quem somos: só a frente de BPO Financeiro (a plataforma não aparece, seguindo o voice.md, que diz "só BPO" nos posts).
- Números das planilhas do gancho (R$ 412 mil, 18,4%, 21 dias) são os exemplos tipográficos do Manual: textura ilustrativa, não dados de cliente.
- A assinatura final é o PNG oficial (principal, sem tagline). Estrela e agulha são redesenhadas em SVG só durante a animação e somem quando o PNG se abre por cima. A tagline foi composta em Poppins em Ouro Norte, fora da área de proteção.
- Fontes Lora e Poppins via @fontsource (npm), GSAP local em `assets/` (o CDN jsdelivr é bloqueado neste ambiente).

## Medido
- `hyperframes check`: 0 erros. 1 aviso mantido: a tagline em Ouro Norte (#B8894A) sobre #E7EFF4 tem contraste 2,69:1, porque a cor é regra do Manual.
- Quadros decodificados do MP4 conferidos em 4,9 / 5,6 / 8,9 / 9,8 / 15,5 / 19,8 / 27,6 / 27,7 / 39,4 / 41,5 s.
- Sem som: o check acusa `film_silent`. Não há fonte de música neste ambiente; a ideia é colocar a trilha no próprio app do Instagram.

## Mais fraco / com mais tempo
- O mar (metade de baixo) fica vazio na maior parte do filme. Está sob a interface do Reels, mas um reflexo discreto do ponto dourado daria vida.
- A rolagem das áreas (tecnologia → serviços) dá cerca de 0,7 s por palavra; dá para ler, mas é rápido.
