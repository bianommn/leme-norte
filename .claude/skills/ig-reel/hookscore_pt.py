#!/usr/bin/env python3
"""
hookscore_pt.py - versão em português do hookscore.py, ajustada ao voice.md
de @psicanalistafabiano.

Mesmos cinco critérios do original (TAMANHO, CONCRETO, TENSÃO, FRENTE,
ENDEREÇO), com três mudanças:

  1. Lê português: acentos, números falados ("doze", "mil"), "R$", horários
     ("19h", "22:47") e dias da semana contam como algo concreto.
  2. A tensão vem de um vocabulário em português e do nicho (culpa, medo,
     sozinho, vazio, ninguém, nunca...).
  3. ENDEREÇO segue a Regra 2 do voice.md: "para quem", "quem...", "a gente"
     e cena em primeira pessoa valem nota alta; "você está/é/se sente..."
     (afirmar algo sobre quem assiste) vira dealbreaker, porque a Meta recusa
     esse tipo de frase em anúncio.

O que isto NÃO é: previsão de alcance. O original foi validado em inglês
(AUC 0,83 para separar gancho real de gancho ruim, 0,56 para separar acerto
de erro do mesmo criador). Esta versão não foi validada com dados: use para
pegar gancho lento, abstrato ou acusatório, e confie no gráfico de retenção.

Uso
  python3 hookscore_pt.py ganchos.txt               # um gancho por linha
  python3 hookscore_pt.py --hook "Desde os 12 anos, eu resolvo tudo."
  python3 hookscore_pt.py ganchos.txt --json
"""

import argparse
import json
import re
import statistics
import sys
import unicodedata

WORD_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ$%'’-]+")
NUMBER_RE = re.compile(
    r"R\$\s?\d[\d.]*(?:,\d+)?"                        # dinheiro
    r"|\b\d{1,2}:\d{2}\b"                             # horário 22:47
    r"|\b\d{1,2}h(?:\d{2})?\b"                        # horário 19h, 19h30
    r"|\b\d[\d.]*(?:,\d+)?\s?"                        # número, com ou
    r"(?:%|mil\b|anos?\b|horas?\b|min(?:utos?)?\b"    # sem unidade
    r"|dias?\b|semanas?\b|meses\b|mês\b|vezes\b)?",
    re.IGNORECASE)
# Maiúscula no meio da frase = nome próprio. Depois de ponto não conta.
PROPER_RE = re.compile(r"(?<!^)(?<![.!?:…] )\b[A-ZÀ-Ý][a-zà-ÿ]{2,}\b")
HASHTAG_RE = re.compile(r"(?:^|\s)#\w+")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


def fold(s):
    """Minúsculas e sem acento, para comparar 'Ninguém' com 'ninguem'."""
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip("'’")


# "um", "uma" e "primeiro" ficam de fora: quase sempre são enchimento.
SPOKEN_NUMBERS = {fold(w) for w in """
    zero dois duas três quatro cinco seis sete oito nove dez onze doze treze
    quatorze catorze quinze dezesseis dezessete dezoito dezenove vinte trinta
    quarenta cinquenta sessenta setenta oitenta noventa cem cento duzentos
    trezentos quinhentos mil milhão milhões metade dobro dúzia
""".split()}
MONEY_WORDS = {fold(w) for w in """
    reais real centavos salário aluguel preço porcento
""".split()}
# Cena com dia e hora prende (auditoria: "22:47, peguei um livro").
SCENE_WORDS = {fold(w) for w in """
    domingo segunda terça quarta quinta sexta sábado madrugada natal
    aniversário réveillon
""".split()}

# Palavras que colocam algo em jogo. Vocabulário geral + o do nicho.
STAKES = {fold(w) for w in """
    nunca ninguém nada não sem nem jamais
    perdi perder perdeu perda custou custa custo
    culpa medo vergonha raiva sozinho sozinha sozinhos sozinhas solidão
    vazio vazia cansaço cansada cansado cansa esgotada esgotado
    dói dor doeu desabar desabei desabou chorar chorei chorou
    briga brigou abandono abandonada abandonado fingir fingindo finge
    erro errei errado errada mentira verdade segredo escondido escondida
    ainda já antes até mas porém exceto senão quase só
    desistir desisti fracasso falhar falhei frescura fraco fraca fraqueza
    sumir sumi trava travei aperta apertou acabou acaba deixei parei
    problema risco arrependimento arrependo deveria
""".split()}

# Aberturas que gastam o primeiro segundo sem dizer nada.
WEAK_OPENERS = [fold(w) for w in [
    "oi", "olá", "ola", "olha", "gente", "pessoal", "galera", "então", "bom",
    "hoje", "bem-vindo", "bem-vinda", "tipo", "basicamente", "sinceramente",
    "nesse", "neste", "vou te", "vou falar", "eu queria", "eu quero",
    "existe", "existem", "isso é", "é muito", "um dos", "uma das",
    "você sabia", "você já", "vocês", "será que", "quando se", "se você",
    "deixa eu", "vamos falar",
]]

IMPERATIVES = {fold(w) for w in """
    pare para salva salve guarda guarde manda mande envia envie escuta escute
    faça faz copie copia tente tenta veja vê leia lê comece começa nunca
    sempre repara repare
""".split()}

# Identificação sem acusação (voice.md, Regra 2).
IDENTIFY_RE = re.compile(
    r"(?i)^\s*(?:para|pra)\s+quem\b|\bpessoas\s+que\b|\btem\s+gente\s+que\b"
    r"|^\s*quem\b")
FIRST_PERSON_RE = re.compile(r"(?i)\b(?:eu|meu|minha|meus|minhas|me|comigo|mim)\b")
WE_RE = re.compile(r"(?i)\b(?:a\s+gente|nós|nosso|nossa)\b")
YOU_RE = re.compile(r"(?i)\b(?:você|voce|vocês|teu|tua|seu|sua|te|contigo)\b")
# Afirma ou pergunta o estado de quem assiste: "Você está cansado",
# "Você se sente sozinha?", "Você sofre de ansiedade?".
ATTRIBUTE_RE = re.compile(
    r"(?i)\bvoc[eê]s?\s+(?:não\s+|nao\s+|já\s+|ja\s+|também\s+|ainda\s+)?"
    r"(?:está|esta|estão|é|são|anda|vive|sofre|tem|se\s+sente|se\s+acha"
    r"|se\s+sentiu|era|foi|ficou)\b")

DEALBREAKERS = [
    (re.compile(r"(?i)^\s*(?:para\s+de\s+rolar|pare\s+de\s+rolar|não\s+passa|nao\s+passa)"),
     "Abre com \"para de rolar\". Pedir atenção mostra que ela ainda não foi conquistada."),
    (re.compile(r"(?i)\b(?:n(?:e|es)ste\s+(?:vídeo|video|reels?)|vou\s+te\s+(?:mostrar|contar|ensinar))\b"),
     "Preâmbulo de vídeo. Corte e abra direto na ideia."),
    (re.compile(r"(?i)^\s*(?:oi|olá|ola|e\s+aí|bem-vind[oa])\b"),
     "Saudação. Ninguém abriu o feed para ser cumprimentado."),
    (ATTRIBUTE_RE,
     "Afirma algo sobre quem assiste (\"você está/é/se sente...\"). A Meta recusa isso "
     "em anúncio e o voice.md proíbe (Regra 2). Troque por \"para quem...\", \"a gente\" "
     "ou uma cena em primeira pessoa."),
    (HASHTAG_RE,
     "Hashtag no gancho. Hashtag vai no fim da legenda."),
    (EMOJI_RE,
     "Emoji no gancho. No tamanho de gancho, a tela tem espaço para palavras ou para "
     "emoji, não para os dois."),
]


def clamp(n):
    return max(0.0, min(100.0, n))


def words(text):
    # "R$ 1.200" é uma palavra falada só, então aqui também.
    return WORD_RE.findall(re.sub(r"(?<=\d)\.(?=\d{3})", "", text))


def check_length(text, wpm):
    """O gancho tem que chegar antes do polegar se mexer."""
    w = words(text)
    n = len(w)
    secs = n / (wpm / 60.0)
    chars = len(text.strip())
    if 5 <= n <= 12:
        score = 100.0
    elif n < 5:
        score = clamp(100 - (5 - n) * 20)
    else:
        score = clamp(100 - (n - 12) * 11)
    if chars > 60:                       # duas linhas de texto grande na tela
        score -= 12
    return clamp(score), (f"{n} palavras, {chars} caracteres, ~{secs:.1f}s falado "
                          "(ideal: 5 a 12 palavras)")


def check_specificity(text):
    """Uma coisa concreta vale mais que três abstratas."""
    nums = [n.strip() for n in NUMBER_RE.findall(text) if n.strip()]
    propers = set(PROPER_RE.findall(text))
    low = [fold(w) for w in words(text)]
    spoken = [w for w in low if w in SPOKEN_NUMBERS or w in MONEY_WORDS or w in SCENE_WORDS]
    hits = len(nums) + len(propers) + len(spoken)
    score = 15.0 if hits == 0 else clamp(45 + hits * 30)
    found = ", ".join(nums[:2] + sorted(propers)[:2] + spoken[:2])
    return score, (f"{hits} marcador(es) concreto(s)" + (f": {found}" if found else
                   " - sem número, nome, dia ou hora"))


def check_stakes(text):
    """Tensão, custo, negação. Algo que quem assiste pode perder ou sentir."""
    w = [fold(x) for x in words(text)]
    markers = sorted({x for x in w if x in STAKES})
    if re.search(r"R\$\s?\d", text):
        markers.append("um preço")
    n = len(markers)
    score = {0: 20.0, 1: 70.0}.get(n, 100.0)
    detail = f"{n} marcador(es) de tensão" + (f": {', '.join(markers[:4])}" if markers else
                                              " - nada em jogo nesta frase")
    return clamp(score), detail


def check_frontload(text):
    """A palavra interessante não pode estar na posição nove."""
    w = words(text)
    if not w:
        return 0.0, "vazio"
    low = [fold(x) for x in w]
    opener = " ".join(low[:2])
    penalty = 0
    hit_opener = None
    for weak in WEAK_OPENERS:
        if opener.startswith(weak) or low[0] == weak:
            penalty, hit_opener = 30, weak
            break
    payload = None
    for i, token in enumerate(low):
        if (token in STAKES or token in SPOKEN_NUMBERS or token in MONEY_WORDS
                or token in SCENE_WORDS or NUMBER_RE.match(w[i])
                or (i and PROPER_RE.match(w[i]))):
            payload = i
            break
    if payload is None:
        base = 30.0
        where = "nenhuma palavra de impacto na frase"
    elif payload <= 3:
        base = 100.0
        where = f"impacto na palavra {payload + 1}"
    elif payload <= 6:
        base = 70.0
        where = f"impacto na palavra {payload + 1}, dá para trazer para a frente"
    else:
        base = 40.0
        where = f"impacto na palavra {payload + 1}, tarde demais"
    detail = where + (f"; abertura fraca \"{hit_opener}\"" if hit_opener else "")
    return clamp(base - penalty), detail


def check_address(text):
    """Quem se reconhece na frase, sem ser acusado (voice.md, Regra 2)."""
    w = [fold(x) for x in words(text)]
    if ATTRIBUTE_RE.search(text):
        return 30.0, "afirma o estado de quem assiste (Regra 2)"
    if IDENTIFY_RE.search(text):
        return 100.0, "identificação sem acusação (\"para quem\", \"quem\", \"pessoas que\")"
    if FIRST_PERSON_RE.search(text):
        return 95.0, "cena em primeira pessoa: quem viveu se reconhece"
    if WE_RE.search(text):
        return 90.0, "\"a gente\": inclui sem apontar"
    if w and w[0] in IMPERATIVES:
        return 80.0, f"abre com imperativo (\"{w[0]}\")"
    if YOU_RE.search(text):
        return 70.0, "fala com \"você\" sem afirmar nada; ok fora do gancho"
    if any(x in SCENE_WORDS for x in w) or re.search(r"\b\d{1,2}(?::\d{2}|h)", text):
        return 80.0, "cena impessoal com dia ou hora: quem viveu se coloca nela"
    return 35.0, "terceira pessoa, ninguém na sala"


CHECKS = ["TAMANHO", "CONCRETO", "TENSÃO", "FRENTE", "ENDEREÇO"]


def run(text, wpm=140):
    results = {
        "TAMANHO": check_length(text, wpm),
        "CONCRETO": check_specificity(text),
        "TENSÃO": check_stakes(text),
        "FRENTE": check_frontload(text),
        "ENDEREÇO": check_address(text),
    }
    flags = [msg for pattern, msg in DEALBREAKERS if pattern.search(text)]
    scores = [results[c][0] for c in CHECKS]
    # O critério mais fraco puxa a nota para baixo, como no original.
    overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4 - len(flags) * 15
    overall = clamp(overall)
    verdict = "FORTE" if overall >= 70 and min(scores) >= 55 and not flags else (
        "OK" if overall >= 50 else "FRACO")
    return results, overall, verdict, flags


def bar(score, width=24):
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)


def render_one(text, results, overall, verdict, flags, out=sys.stdout):
    print("\nNOTA DO GANCHO", file=out)
    print("=" * 62, file=out)
    print(f"  \"{text.strip()}\"\n", file=out)
    for name in CHECKS:
        score, detail = results[name]
        print(f"  {name:<13} {bar(score)} {score:5.1f}", file=out)
        print(f"  {'':<13} {detail}", file=out)
    print("-" * 62, file=out)
    print(f"  {'NOTA':<13} {bar(overall)} {overall:5.1f}   {verdict}", file=out)
    for f in flags:
        print(f"\n  DEALBREAKER  {f}", file=out)
    if verdict != "FORTE":
        weakest = min(CHECKS, key=lambda c: results[c][0])
        print(f"\n  Critério mais fraco: {weakest}. Corrija esse e rode de novo.", file=out)
    print("", file=out)


def render_table(rows, out=sys.stdout):
    print("\nRANKING DE GANCHOS\n" + "=" * 78, file=out)
    for i, r in enumerate(rows, 1):
        mark = "->" if i == 1 else "  "
        hook = r["hook"] if len(r["hook"]) <= 62 else r["hook"][:59] + "..."
        print(f"{mark} {r['score']:5.1f} {r['verdict']:<7} {hook}", file=out)
        print(f"        mais fraco: {r['weakest']} ({r['checks'][r['weakest']]['score']:.0f})",
              file=out)
        for f in r["flags"]:
            print(f"        dealbreaker: {f}", file=out)
    print("\nGrave o primeiro. Se o primeiro ficou abaixo de 50, nenhum deles é o gancho.\n",
          file=out)


def main():
    ap = argparse.ArgumentParser(description="Nota de gancho de Reel, em português.")
    ap.add_argument("input", nargs="?", default="-", help="arquivo com um gancho por linha, ou -")
    ap.add_argument("--hook", help="avaliar um gancho só, passado na linha de comando")
    ap.add_argument("--wpm", type=float, default=140, help="palavras por minuto (padrão 140)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.hook:
        lines = [args.hook]
    else:
        raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not lines:
        print("nada para avaliar", file=sys.stderr)
        sys.exit(2)

    payload = []
    for line in lines:
        results, overall, verdict, flags = run(line, args.wpm)
        payload.append({
            "hook": line,
            "checks": {k: {"score": round(v[0], 1), "detail": v[1]} for k, v in results.items()},
            "weakest": min(CHECKS, key=lambda c: results[c][0]),
            "flags": flags,
            "score": round(overall, 1),
            "verdict": verdict,
        })

    if args.json:
        print(json.dumps(payload if len(payload) > 1 else payload[0], indent=2, ensure_ascii=False))
        return

    if len(payload) == 1:
        results, overall, verdict, flags = run(lines[0], args.wpm)
        render_one(lines[0], results, overall, verdict, flags)
    else:
        render_table(sorted(payload, key=lambda r: -r["score"]))

    sys.exit(0 if max(p["score"] for p in payload) >= 70 else 1)


if __name__ == "__main__":
    main()
