"""
script_check.py — the quality bar every long-video script must pass before it is built.

Owner, 2026-11-04: "make sure high quality with trending and viral script and visual so
people get the connection and story ... keep checking this too."

Rules come from the current hits in our niche (notes/2026-11-03_niche_research.md and the
chapter analysis in VIRAL_PLAYBOOK.md): a fast second-person hook with stakes, about 10
chapters of ~60-120 s, a re-hook at least every ~2 minutes, every big number made
visible against a human, short spoken sentences, sources, and a payoff at the end.

Usage:
  python script_check.py run_some_long.py          # module with SEGMENTS, SCRIPT, SOURCES
Exit code 1 if any MUST rule fails. Words are timed at ~2.5 words/s (Kokoro at speed ~1.05).
"""
import importlib.util
import re
import sys

WPS = 2.5
STAKES = re.compile(r"\b(die|dead|death|kill\w*|surviv\w*|swallow\w*|crush\w*|eat\w*|hunt\w*|attack\w*|bite|teeth|jaws|"
                    r"danger\w*|deadl\w*|never|dark\w*|deep\w*|alone|drown\w*|trap\w*|scream\w*|terrif\w*|monster\w*|"
                    r"giant|biggest|largest|loudest|fastest|strongest|only)\b", re.I)
YOU = re.compile(r"\b(you|your|you're|you'd|you'll)\b", re.I)
REHOOK = re.compile(r"(\?|\bbut\b|\bhere'?s the (thing|twist|problem)\b|\bit gets worse\b|\bthe real\b|\bonly one\b|"
                    r"\bstill\b.*\?|\bwhat happens\b|\bnobody\b|\bno one\b|\bsecret\b|\bwait\b)", re.I)
SCALE = re.compile(r"\b(you|your|human|person|people|diver|bus|buses|car|cars|football field|pitch|basketball court|"
                   r"elephant|house|floor|building|storey|story|times|as (big|long|tall|heavy|deep) as|"
                   r"bigger than|longer than|taller than|heavier than)\b", re.I)
NUMBER = re.compile(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion|"
                    r"dozen|half|twice|double|triple)\b", re.I)
BANNED = re.compile(r"\b(in this video|hey guys|welcome back|let'?s dive in|without further ado|fun fact|smash that|"
                    r"don'?t forget to subscribe|basically|literally)\b", re.I)


def _load(path):
    spec = importlib.util.spec_from_file_location("script_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(segments, script, sources=""):
    words = [len(re.findall(r"[\w'’-]+", s["line"])) for s in segments]
    starts, t = [], 0.0
    for w in words:
        starts.append(t)
        t += w / WPS
    total = t
    lines = [s["line"] for s in segments]
    res = []   # (level, ok, rule, detail)

    def rule(level, ok, name, detail=""):
        res.append((level, bool(ok), name, detail))

    # 1. Hook: first ~15 s
    hook_idx = [i for i, s in enumerate(starts) if s < 15] or [0]
    hook = " ".join(lines[i] for i in hook_idx)
    rule("MUST", YOU.search(hook), "hook speaks to the viewer (you/your) in the first 15 s", hook[:90])
    rule("MUST", STAKES.search(hook), "hook has stakes (danger, death, scale, a superlative) in the first 15 s")
    rule("MUST", not re.match(r"\s*(hi|hello|hey|welcome|today|in this video)\b", lines[0], re.I),
         "no greeting or 'today we...' opener", lines[0][:60])
    # 2. Promise / open loop inside the first 60 s
    first60 = " ".join(lines[i] for i, s in enumerate(starts) if s < 60)
    rule("MUST", re.search(r"\?|\bonly one\b|\bby the end\b|\bnumber one\b|\bthe last\b|\bwhich\b", first60, re.I),
         "an open question or promise in the first 60 s")
    # 3. Length and chapters
    rule("MUST", 480 <= total <= 1200, "length 8-20 min", f"{total/60:.1f} min ({sum(words)} words)")
    ch = [i for i, s in enumerate(segments) if s.get("chapter")]
    intro = starts[ch[1]] if len(ch) > 1 else total
    rule("MUST", 6 <= len(ch) <= 16, "6-16 chapters", f"{len(ch)} chapters")
    rule("SHOULD", intro <= 75, "intro (before the first real chapter) under ~75 s", f"{intro:.0f} s")
    if len(ch) > 1:
        bounds = [starts[i] for i in ch] + [total]
        lens = [b - a for a, b in zip(bounds, bounds[1:])]
        rule("SHOULD", max(lens[1:] or [0]) <= 150, "no chapter longer than ~2.5 min",
             f"longest {max(lens[1:] or [0]):.0f} s")
        weak = [segments[i]["chapter"] for i in ch[1:] if len(segments[i]["chapter"].split()) < 2]
        rule("SHOULD", not weak, "chapter titles are mini-hooks (2+ words, not just a name)", ", ".join(weak[:5]))
    # 4. Re-hooks: max gap between curiosity lines
    hooks_at = [starts[i] for i, l in enumerate(lines) if REHOOK.search(l)] + [total]
    gaps = [b - a for a, b in zip([0.0] + hooks_at, hooks_at)]
    rule("MUST", max(gaps) <= 120, "a re-hook (question, 'but', twist) at least every 2 min", f"longest gap {max(gaps):.0f} s")
    # 5. Numbers shown to scale: each chapter has a number next to a human-scale comparison
    if len(ch) > 1:
        bounds = ch + [len(segments)]
        missing = []
        for a, b in zip(bounds, bounds[1:]):
            text = " ".join(lines[a:b])
            if not (NUMBER.search(text) and SCALE.search(text)):
                missing.append(segments[a]["chapter"])
        rule("SHOULD", not missing[1:], "every chapter has a number made visible against a human/object",
             ", ".join(missing[1:5]))
    # 6. Speakability
    long_lines = [l for l, w in zip(lines, words) if w > 32]
    rule("MUST", not long_lines, "no narrated line over 32 words", (long_lines[0][:70] + "...") if long_lines else "")
    sent = [len(x.split()) for l in lines for x in re.split(r"(?<=[.!?])\s+", l) if x.strip()]
    avg = sum(sent) / max(1, len(sent))
    rule("SHOULD", avg <= 15, "average sentence 15 words or fewer", f"{avg:.1f}")
    banned = sorted({m.group(0).lower() for l in lines for m in BANNED.finditer(l)})
    rule("MUST", not banned, "no filler phrases", ", ".join(banned))
    rule("SHOULD", not re.search(r"subscribe", " ".join(lines[i] for i, s in enumerate(starts) if s < 60), re.I),
         "no subscribe ask in the first minute")
    # 7. Ending: payoff, short CTA
    tail = " ".join(lines[-4:])
    rule("SHOULD", sum(1 for l in lines[-6:] if re.search(r"subscribe|comment|like", l, re.I)) <= 2,
         "call to action is short (2 lines max)")
    rule("SHOULD", re.search(r"\?|\bso\b|\bthat'?s why\b|\bin the end\b|\bnumber one\b|\bverdict\b|\banswer\b", tail, re.I),
         "ends with a payoff/answer, not just a CTA")
    # 8. Visual pace (cartoon/AI shot lists): a new picture every <= ~4 s
    if all("shots" in s for s in segments):
        per = [(w / WPS) / max(1, len(s["shots"])) for s, w in zip(segments, words)]
        slow = sum(1 for p in per if p > 6.5)
        rule("SHOULD", slow <= len(segments) * 0.1, "a new picture at least every ~6 s on 90% of lines",
             f"{slow} slow lines")
    # 9. Sources, title, thumbnail text
    n_src = len([l for l in (sources or "").splitlines() if l.strip().startswith("-")])
    rule("MUST", n_src >= 4, "at least 4 sources listed", f"{n_src}")
    title = (script or {}).get("title", "")
    rule("MUST", 0 < len(title) <= 70, "title 70 characters or fewer", f"{len(title)}: {title}")
    rule("SHOULD", YOU.search(title) or STAKES.search(title) or re.search(r"\d", title),
         "title has 'you', a stake/superlative, or a number")
    return res, total


def report(res, total):
    fails = [r for r in res if not r[1]]
    for level, ok, name, detail in res:
        print(f"  {'PASS' if ok else ('FAIL' if level == 'MUST' else 'WARN')}  [{level}] {name}" + (f"  ({detail})" if detail else ""))
    must = [r for r in fails if r[0] == "MUST"]
    print(f"\n  {len(res) - len(fails)}/{len(res)} rules pass | {len(must)} MUST failing | ~{total/60:.1f} min")
    return not must


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    m = _load(sys.argv[1])
    res, total = check(m.SEGMENTS, getattr(m, "SCRIPT", {}), getattr(m, "SOURCES", ""))
    sys.exit(0 if report(res, total) else 1)
