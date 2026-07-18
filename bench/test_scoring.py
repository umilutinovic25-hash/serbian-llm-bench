"""Scoring tests. Run: python bench/test_scoring.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tasks import Task, _extract_letter, _fold, score  # noqa: E402

FAILURES = []


def check(label, got, want):
    if got != want:
        FAILURES.append(f"{label}: dobijeno {got!r}, očekivano {want!r}")


def approx(label, got, want, tol=0.01):
    if abs(got - want) > tol:
        FAILURES.append(f"{label}: dobijeno {got:.3f}, očekivano ~{want}")


MC = Task(
    id="t", category="c", type="mc",
    prompt="Koliko?", choices=["Jedna", "Dva", "Tri"], answer="B",
)

# Letter extraction must not pick lowercase letters out of ordinary words.
check("letter/prefix", _extract_letter("B) Dva", 3), "B")
check("letter/bare", _extract_letter("B", 3), "B")
check("letter/phrase", _extract_letter("Odgovor je B", 3), "B")
check("letter/embedded", _extract_letter("Dvojkodak je odgovor: B) Dva.", 3), "B")
check("letter/lowercase-trap", _extract_letter("Dva jabuke su ostale", 3), None)
check("letter/none", _extract_letter("Ne znam odgovor.", 3), None)

check("mc/correct", score(MC, "B")[0], 1.0)
check("mc/wrong", score(MC, "A")[0], 0.0)
check("mc/text-answer", score(MC, "Dva")[0], 1.0)
check("mc/empty", score(MC, "")[0], 0.0)

# Serbian is digraphic — Cyrillic and Latin spellings must fold identically.
check("fold/cyrillic", _fold("Ниш"), _fold("Niš"))
check("fold/diacritics", _fold("Niš"), _fold("Nis"))
check("fold/dj", _fold("Ђоковић"), _fold("Djokovic"))
if not _fold("Она је радила"):
    FAILURES.append("fold/cyrillic-nonempty: ćirilica se briše u prazan string")

NER = Task(
    id="n", category="ner", type="extract",
    prompt="Izdvoj gradove", expected=[["Niš"], ["Beograd"]],
)
approx("ner/clean", score(NER, "Niš, Beograd")[0], 1.0)
approx("ner/cyrillic", score(NER, "Ниш, Београд")[0], 1.0)
approx("ner/half", score(NER, "Niš")[0], 0.667)
# Echoing the sentence has perfect recall but poor precision — must not score 1.0.
echo = score(NER, "Voz, iz, Niša, za, Beograd, staje, danas, ovde")[0]
if echo >= 0.8:
    FAILURES.append(f"ner/echo-attack: prepisivanje rečenice dobilo {echo:.2f}, mora biti niže")

TRANSLATE = Task(
    id="p", category="prevod", type="translate",
    prompt="Prevedi", keywords=[["sastanak"], ["odložen", "pomeren"]],
)
approx("prevod/full", score(TRANSLATE, "Sastanak je odložen")[0], 1.0)
approx("prevod/synonym", score(TRANSLATE, "Sastanak je pomeren")[0], 1.0)
approx("prevod/cyrillic", score(TRANSLATE, "Састанак је одложен")[0], 1.0)
approx("prevod/half", score(TRANSLATE, "Sastanak je sutra")[0], 0.5)

if FAILURES:
    print(f"PALO {len(FAILURES)} testova:")
    for failure in FAILURES:
        print(f"  - {failure}")
    sys.exit(1)
print("Svi testovi prošli.")
