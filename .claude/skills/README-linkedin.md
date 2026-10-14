# LinkedIn agent skills (vendored)

Os onze skills `li-*` desta pasta vêm de
https://github.com/Jakeschincariol/linkedin-agent-skill (licença MIT, ver
`LICENSE-linkedin-agent-skill`), commit `add2c23`.

Comandos: `/li-post`, `/li-comment`, `/li-reply`, `/li-profile`, `/li-plan`,
`/li-human`, `/li-carousel`, `/li-repurpose`, `/li-dm`, `/li-inbox`, `/li-audit`.

Nenhum deles publica no LinkedIn: todos geram texto pronto para colar.

Antes de usar, preencha `templates/linkedin/voice.md` e copie-o para
`~/.claude/linkedin/voice.md` (todos os skills leem esse arquivo).

Observação: o léxico de `li-human/slop.json` e as checagens de `detect.py` são
em inglês; textos em português terão pontuações menos confiáveis.
