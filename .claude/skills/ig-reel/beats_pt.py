#!/usr/bin/env python3
"""
beats_pt.py - versão em português do beats.py: transforma o roteiro de um
Reel numa folha de tempos antes de gravar.

Diferenças em relação ao original:

  1. Conta palavras acentuadas como uma palavra só (o original partia
     "ninguém" em duas e superestimava o tempo).
  2. "Concreto" inclui números falados ("doze"), R$, horários ("19h",
     "22:47") e dias da semana, além de números e nomes.
  3. O loop compara pela raiz da palavra ("perguntou" e "perguntar" contam)
     e olha a abertura inteira (as telas dos primeiros 6 segundos), não só
     a primeira linha.
  4. Ritmo padrão de 140 palavras por minuto (voice.md). Em Reel só de telas,
     use o mesmo número como tempo de leitura.

Os tempos são estimativa por contagem de palavras. Bons para planejar a
edição, não substituem gravar.

Uso
  python3 beats_pt.py roteiro.txt
  python3 beats_pt.py roteiro.txt --target 40
  python3 beats_pt.py roteiro.txt --wpm 150 --target 45 --json
"""

import argparse
import json
import re
import sys
import unicodedata

WORD_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ$%'’-]+")
SENT_RE = re.compile(r"[^.!?]+[.!?]*")
CONCRETE_RE = re.compile(
    r"R\$\s?\d|\b\d{1,2}:\d{2}\b|\b\d{1,2}h(?:\d{2})?\b|\b\d[\d.,]*\b"
    r"|(?<!^)(?<![.!?:…] )\b[A-ZÀ-Ý][a-zà-ÿ]{2,}\b", re.MULTILINE)


def fold(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip("'’")


CONCRETE_WORDS = {fold(w) for w in """
    dois duas três quatro cinco seis sete oito nove dez onze doze treze
    quatorze catorze quinze vinte trinta quarenta cinquenta cem mil metade
    reais domingo segunda terça quarta quinta sexta sábado madrugada natal
    aniversário
""".split()}
STOPWORDS = {fold(w) for w in """
    a o as os um uma uns umas e ou mas se de do da dos das em no na nos nas
    por para pra pro com sem que quem qual isso isto esse essa este esta
    ele ela eles elas eu me mim meu minha você voce te seu sua nós a gente
    é foi ser era está estava são não nem já só tão mais muito tudo todo
    toda nada ainda também como quando onde aqui lá ao à
""".split()}

HOOK_WINDOW = 3.0        # segundos. Depois disso, o polegar já decidiu.
OPENING_WINDOW = 6.0     # o que volta à tela logo no replay
MAX_BEAT = 4.0           # segundos numa ideia sem mudar nada na tela
ABSTRACT_RUN = 3         # telas seguidas sem nada concreto
STEM = 6                 # letras comparadas para achar a mesma raiz


def words(text):
    return WORD_RE.findall(re.sub(r"(?<=\d)\.(?=\d{3})", "", text))


def concrete(text):
    hits = len(CONCRETE_RE.findall(text))
    return hits + sum(1 for w in words(text) if fold(w) in CONCRETE_WORDS)


def stems(text):
    return {fold(w)[:STEM]: w for w in words(text)
            if fold(w) not in STOPWORDS and len(fold(w)) >= 4}


def tc(seconds):
    m, s = divmod(seconds, 60)
    return f"{int(m)}:{s:04.1f}"


def split_beats(raw, wps):
    """Uma linha é uma tela, a menos que seja longa demais para uma só."""
    beats = []
    for line in [l.strip() for l in raw.splitlines()]:
        if not line:
            continue
        if len(words(line)) / wps <= MAX_BEAT * 1.5:
            beats.append(line)
            continue
        parts = [p.strip() for p in SENT_RE.findall(line) if p.strip()]
        buf = ""
        for part in parts:
            candidate = (buf + " " + part).strip()
            if buf and len(words(candidate)) / wps > MAX_BEAT:
                beats.append(buf)
                buf = part
            else:
                buf = candidate
        if buf:
            beats.append(buf)
    return beats


def analyse(raw, wpm=140, target=None):
    wps = wpm / 60.0
    beats = split_beats(raw, wps)
    if not beats:
        return None

    rows, clock = [], 0.0
    for i, text in enumerate(beats):
        n = len(words(text))
        dur = n / wps
        rows.append({
            "n": i + 1, "start": round(clock, 2), "dur": round(dur, 2),
            "words": n, "text": text, "concrete": concrete(text),
            "label": "", "flags": [],
        })
        clock += dur
    total = clock

    for r in rows:
        if r["n"] == 1 or r["start"] + r["dur"] <= HOOK_WINDOW:
            r["label"] = "GANCHO"
    rows[-1]["label"] = "CTA" if rows[-1]["label"] != "GANCHO" else "GANCHO/CTA"
    half = total / 2
    for r in rows:
        if not r["label"] and r["start"] <= half < r["start"] + r["dur"]:
            r["label"] = "MEIO"

    notes = []
    if rows[0]["dur"] > HOOK_WINDOW:
        rows[0]["flags"].append(f"gancho leva {rows[0]['dur']:.1f}s, passa dos {HOOK_WINDOW:.0f}s")
        notes.append(f"A tela 1 leva {rows[0]['dur']:.1f}s. Corte para {int(HOOK_WINDOW * wps)} "
                     "palavras ou menos, senão o gancho chega depois da decisão.")
    if rows[0]["concrete"] == 0:
        notes.append("A tela 1 não tem número, nome, dia nem hora. Gancho sem nada concreto "
                     "é o que mais se pula.")

    for r in rows:
        if r["dur"] > MAX_BEAT:
            r["flags"].append(f"{r['dur']:.1f}s numa tela só")
    long_beats = [r["n"] for r in rows if r["dur"] > MAX_BEAT]
    if long_beats:
        notes.append(f"Tela(s) {', '.join(map(str, long_beats))} passam de {MAX_BEAT:.0f}s. "
                     "Divida a frase ou mude algo na tela no meio dela.")

    run, start = 0, None
    for r in rows:
        if r["concrete"] == 0:
            run += 1
            start = start if start is not None else r["n"]
            if run == ABSTRACT_RUN:
                notes.append(f"Telas {start}-{r['n']} não têm nada concreto. Coloque um número, "
                             "um nome, um dia ou uma hora em uma delas.")
        else:
            run, start = 0, None

    opening = {}
    for r in rows[:-1]:
        if r["start"] < OPENING_WINDOW:
            opening.update(stems(r["text"]))
    last = stems(rows[-1]["text"])
    shared = sorted(set(opening) & set(last))
    if shared:
        pairs = [f"{last[s]}/{opening[s]}" for s in shared[:3]]
        notes.append(f"Loop: a última tela ecoa a abertura ({', '.join(pairs)}). "
                     "Replay é alcance de graça.")
    else:
        notes.append("Sem loop. A última tela não repete nenhuma palavra da abertura. Ecoar "
                     "uma palavra das primeiras telas é o replay mais barato que existe.")

    if target:
        delta = total - target
        if abs(delta) <= target * 0.1:
            notes.append(f"Duração no alvo ({total:.1f}s para {target:g}s).")
        elif delta > 0:
            notes.append(f"{delta:.1f}s acima do alvo. Corte cerca de {int(delta * wps)} palavras.")
        else:
            notes.append(f"{-delta:.1f}s abaixo do alvo. Acrescente {int(-delta * wps)} palavras "
                         "ou deixe curto. Curto costuma ser o certo.")

    return {
        "wpm": wpm, "target": target,
        "total_seconds": round(total, 2),
        "total_words": sum(r["words"] for r in rows),
        "beats": rows, "notes": notes,
    }


def render(a, out=sys.stdout):
    head = (f"FOLHA DE TEMPOS  ·  {a['total_words']} palavras  ·  ~{a['total_seconds']:.1f}s "
            f"a {a['wpm']:g} ppm")
    if a["target"]:
        head += f"  ·  alvo {a['target']:g}s"
    print(head, file=out)
    print("=" * 72, file=out)
    for r in a["beats"]:
        print(f"  {tc(r['start'])}  {r['dur']:4.1f}s  {r['label']:<10} {r['text']}", file=out)
        for f in r["flags"]:
            print(f"  {'':<26}^ {f}", file=out)
    print("-" * 72, file=out)
    for n in a["notes"]:
        print(f"  - {n}", file=out)


def main():
    ap = argparse.ArgumentParser(description="Folha de tempos de Reel, em português.")
    ap.add_argument("input", nargs="?", default="-", help="arquivo do roteiro, ou -")
    ap.add_argument("--wpm", type=float, default=140, help="palavras por minuto (padrão 140)")
    ap.add_argument("--target", type=float, help="duração alvo em segundos")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    a = analyse(raw, args.wpm, args.target)
    if not a:
        print("roteiro vazio", file=sys.stderr)
        sys.exit(2)
    if args.json:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    else:
        render(a)


if __name__ == "__main__":
    main()
