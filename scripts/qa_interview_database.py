#!/usr/bin/env python3
"""Quality-assurance harness for the synthesised interview database.

Runs completeness, consistency, repetition and distribution checks over the
generated transcripts and prints a scorecard.  Exit code is non-zero when any
blocking check fails, so it can gate a rebuild.
"""
from __future__ import annotations

import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from interview_database.codebook import CODEBOOK, CODE_ORDER  # noqa: E402
from interview_database.personas import SURVEY_FILE, load  # noqa: E402
from interview_database.workbook import build_transcripts  # noqa: E402

N = 18


def words(t: str) -> int:
    return len(t.split())


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", t.strip().lower())


def shingles(t: str, k: int = 10) -> set[str]:
    toks = re.findall(r"[a-z']+", t.lower())
    return {" ".join(toks[i:i + k]) for i in range(max(0, len(toks) - k + 1))}


def main() -> int:
    people = load(ROOT / SURVEY_FILE)
    tr = build_transcripts(people)
    findings: list[tuple[str, str, str]] = []   # (severity, check, detail)

    def add(sev: str, check: str, detail: str):
        findings.append((sev, check, detail))

    # ---------------------------------------------------------------- format --
    for p in people:
        for q in range(1, N + 1):
            text, codes = tr[p.rid][q]
            tag = f"{p.rid}-Q{q}"
            if not text.strip():
                add("BLOCK", "empty", tag)
            if "  " in text or "\n" in text:
                add("BLOCK", "whitespace", tag)
            if re.search(r"\{[^}]*\}|None|nan|\[[A-Z_]+\]", text):
                add("BLOCK", "template leak", tag)
            if not text[:1].isupper():
                add("BLOCK", "lowercase start", tag)
            if text[-1] not in ".!?":
                add("MAJOR", "no end punctuation", tag)
            if re.search(r"\s[,.;]", text):
                add("MAJOR", "space before punctuation", tag)
            if re.search(r"[A-Za-z],[A-Za-z]", text):
                add("MAJOR", "missing space after comma", tag)
            if re.search(r"\.\.(?!\.)", text):
                add("MINOR", "double full stop", tag)
            if re.search(r"\b(\w+)\s+\1\b", text, re.I) and not re.search(
                    r"\b(had|that|very|no|so|is)\s+\1\b", text, re.I):
                add("MINOR", "repeated word", tag)
            if words(text) < 30 or words(text) > 220:
                add("MINOR", "length", f"{tag} ({words(text)} words)")

    # ------------------------------------------------------------ facts / logic --
    for p in people:
        q1 = tr[p.rid][1][0]
        if p.primary_network not in q1:
            add("MAJOR", "Q1 network", p.rid)
        if str(p.age_value) not in q1:
            add("MINOR", "Q1 age", p.rid)

        q3 = tr[p.rid][3][0]
        if p.exposure.lower() == "never" and re.search(r"every time|several times|often", q3, re.I):
            add("MAJOR", "Q3 exposure contradiction", p.rid)

        q6 = tr[p.rid][6][0]
        if p.trust_level >= 4 and re.search(
                r"I do not trust them|Not much, to be honest|Very little|I have learned to be careful", q6):
            add("MAJOR", "Q6 trust contradiction", p.rid)
        if p.trust_level <= 2 and re.search(r"I do trust them|On the whole I believe", q6):
            add("MAJOR", "Q6 trust contradiction", p.rid)

        q8 = tr[p.rid][8][0]
        if p.purchase_status == "NO" and re.search(r"I bought it|I bought the|so I bought", q8):
            add("MAJOR", "Q8 purchase contradiction", p.rid)
        if p.purchase_status in ("YES", "LIMITED") and not re.search(r"bought|purchase", q8):
            add("MAJOR", "Q8 missing purchase", p.rid)
        ch = p.channel.lower() if p.purchase_status in ("YES", "LIMITED") else ""
        if not ch:
            kind = None
        elif "ussd" in ch:
            kind = "ussd"
        elif "agent" in ch:
            kind = "agent"
        elif "mobile money" in ch:
            kind = "money"
        else:
            kind = "app"
        if kind is None:
            pass
        elif kind == "app" and "app" not in q8:
            add("MAJOR", "Q8 channel missing", p.rid)
        elif kind == "ussd" and "USSD" not in q8:
            add("MAJOR", "Q8 channel missing", p.rid)
        elif kind == "agent" and "agent" not in q8:
            add("MAJOR", "Q8 channel missing", p.rid)
        elif kind == "money" and not re.search(r"Mpamba|Airtel Money", q8):
            add("MAJOR", "Q8 channel missing", p.rid)

        q12 = tr[p.rid][12][0]
        if p.score(29) <= 2 and re.search(r"I saw .* and bought|buy a bundle that was not in my plan", q12):
            add("MAJOR", "Q12 impulse contradiction", p.rid)
        if p.purchase_status == "NO" and re.search(r"I will see an advert and buy", q12):
            add("MAJOR", "Q12 purchase contradiction", p.rid)

        q14 = tr[p.rid][14][0]
        f = p.factor.lower()
        if f:
            probe = {"price": r"price|afford|cost|money",
                     "data": r"data|gigabyte|volume|size of the bundle",
                     "validity": r"valid|last|days|duration",
                     "promotion": r"discount|promotion|bonus|offer",
                     "network": r"network|coverage|speed|reliab",
                     "convenien": r"convenien|ease|easy|app|click|quick",
                     "recommend": r"recommend|friend|classmate|other students"}[next((k for k in
                        ("price", "data", "validity", "promotion", "network",
                         "convenien", "recommend") if k in f), "price")]
            if not re.search(probe, q14, re.I):
                add("MAJOR", "Q14 factor missing", p.rid)

        q18 = tr[p.rid][18][0]
        r = p.overall_rating.lower()
        if r and r not in ("very high",) and r not in q18.lower():
            add("MINOR", "Q18 rating missing", f"{p.rid} ({p.overall_rating})")

        q10 = tr[p.rid][10][0]
        other = "Airtel" if p.primary_network == "TNM" else "TNM"
        if not p.dual_network and re.search(
                rf"I bought the {other} bundle|mixing the two networks|moved to {other}|"
                rf"switched network|I changed network|I switched", q10):
            add("MAJOR", "Q10 network switch contradiction", p.rid)
        if not p.dual_network and re.search(r"I keep two lines|I have two lines", tr[p.rid][1][0]):
            add("MAJOR", "Q1 network contradiction", p.rid)

        # Q12: a self-described planner must not narrate impulse behaviour
        if p.score(29) <= 3 and re.search(
                r"smaller bundle to recover|I do not regret it|"
                r"pages that push offers too hard|buy first and think later", q12):
            add("MAJOR", "Q12 planner/impulse contradiction", p.rid)

        # Q10: a switching story must not sit next to a "I never switch" line
        if re.search(r"switched network|I moved to (Airtel|TNM)|mixing the two networks", q10) and \
                re.search(r"rather adjust my bundle than change the network|I do not switch easily|"
                          r"Changing would mean losing", q10):
            add("MAJOR", "Q10 switch/stay contradiction", p.rid)

        # cross-answer: trust narrative should not flip inside Q15
        q15 = tr[p.rid][15][0]
        if p.trust_level >= 4 and re.search(r"I have had a problem|Yes, more than once", q15):
            add("MAJOR", "Q15 trust contradiction", p.rid)

    # ------------------------------------------------------------ repetition --
    rep = []
    for q in range(1, N + 1):
        counts = Counter()
        for p in people:
            for s in shingles(tr[p.rid][q][0]):
                counts[s] += 1
        top, n = counts.most_common(1)[0]
        rep.append((q, n, top))
    for q, n, top in rep:
        share = n / len(people)
        sev = "MAJOR" if share > 0.45 else "MINOR" if share > 0.30 else "OK"
        if sev != "OK":
            add(sev, "repetition", f"Q{q}: {share:.0%} share → '{top[:70]}'")

    identical = 0
    for q in range(1, N + 1):
        c = Counter(norm(tr[p.rid][q][0]) for p in people)
        identical += sum(v - 1 for v in c.values() if v > 1)
    if identical:
        add("MAJOR", "identical answers", f"{identical} duplicates")

    # ------------------------------------------------------------ distribution --
    codes_by_person = {p.rid: {c for _, cs in tr[p.rid].values() for c in cs} for p in people}
    freq = Counter()
    for cs in codes_by_person.values():
        freq.update(cs)
    for code in CODE_ORDER:
        share = freq[code] / len(people)
        if share == 1.0:
            add("MAJOR", "code saturation", code)

    # correlation between survey item and matching code
    pairs = [(15, "TR_TRUST", ">=", 4), (29, "IM_IMPULSE", ">=", 4),
             (36, "CP_COMPARE_ALWAYS", "always", None)]
    # purchase: survey Q32 says Yes
    survey_yes = sum(1 for p in people if p.purchase.lower().startswith("yes"))
    coded_yes = sum(1 for cs in codes_by_person.values() if "PC_PURCHASED" in cs)
    if abs(coded_yes - survey_yes) / len(people) * 100 > 5:
        add("MAJOR", "distribution gap", f"PC_PURCHASED: {coded_yes} vs survey {survey_yes}")
    for q, code, op, thresh in pairs:
        if q == 36:
            survey = sum(1 for p in people if p.comparison.lower() == "always")
        else:
            survey = sum(1 for p in people if getattr(p, "score")(q) >= thresh)
        coded = sum(1 for cs in codes_by_person.values() if code in cs)
        gap = abs(coded - survey) / len(people) * 100
        if gap > 5:
            add("MAJOR", "distribution gap", f"{code}: {coded} vs survey {survey} ({gap:.1f}pp)")

    # ---------------------------------------------------------------- report --
    print(f"Respondents: {len(people)}   Answers: {len(people) * N}")
    lens = [words(t) for p in people for t, _ in tr[p.rid].values()]
    print(f"Words/answer: mean {statistics.mean(lens):.1f}, median {statistics.median(lens):.0f}, "
          f"min {min(lens)}, max {max(lens)}")
    print(f"Total words: {sum(lens):,}")
    print(f"Codes: {len(CODE_ORDER)} in {len({v[0] for v in CODEBOOK.values()})} themes; "
          f"codes/respondent {min(len(c) for c in codes_by_person.values())}–"
          f"{max(len(c) for c in codes_by_person.values())}")

    print("\nTop repeated 10-word runs per question:")
    for q, n, top in rep:
        print(f"  Q{q:<2} {n/len(people):5.0%}  {top[:88]}")

    by_sev = defaultdict(list)
    for sev, check, detail in findings:
        by_sev[sev].append((check, detail))
    print("\nFindings:")
    for sev in ("BLOCK", "MAJOR", "MINOR"):
        items = by_sev.get(sev, [])
        print(f"  {sev}: {len(items)}")
        for check, detail in items[:14]:
            print(f"     - {check}: {detail}")
        if len(items) > 14:
            print(f"     … {len(items) - 14} more")

    blocking = len(by_sev.get("BLOCK", [])) + len(by_sev.get("MAJOR", []))
    print("\nRESULT:", "PASS" if blocking == 0 else f"FAIL ({blocking} blocking issues)")
    return 0 if blocking == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
