"""Gradio leaderboard for the Serbian LLM benchmark."""

import json
from pathlib import Path

import gradio as gr
import pandas as pd

RESULTS_DIR = Path(__file__).parent / "results"

CATEGORY_LABELS = {
    "gramatika": "Gramatika",
    "padezi": "Padeži",
    "pravopis": "Pravopis",
    "razumevanje": "Razumevanje",
    "ner": "NER",
    "prevod": "Prevod",
}

RANDOM_BASELINE = 33.3


def load_results() -> list[dict]:
    results = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["model"] == "mock":
            continue
        results.append(data)
    return sorted(results, key=lambda d: d["overall"], reverse=True)


def build_table() -> pd.DataFrame:
    rows = []
    for rank, data in enumerate(load_results(), 1):
        row = {
            "#": rank,
            "Model": data["model"].replace("ollama:", ""),
            "Ukupno": data["overall"],
        }
        for key, label in CATEGORY_LABELS.items():
            stats = data["categories"].get(key)
            row[label] = stats["score"] if stats else None
        rows.append(row)
    return pd.DataFrame(rows)


def category_breakdown() -> pd.DataFrame:
    """Average score per category across all models — shows which skills are hard."""
    results = load_results()
    rows = []
    for key, label in CATEGORY_LABELS.items():
        scores = [d["categories"][key]["score"] for d in results if key in d["categories"]]
        if scores:
            rows.append({
                "Kategorija": label,
                "Prosek svih modela": round(sum(scores) / len(scores), 1),
                "Najbolji": max(scores),
                "Najgori": min(scores),
            })
    return pd.DataFrame(rows).sort_values("Prosek svih modela")


DESCRIPTION = f"""
# 🇷🇸 Serbian LLM Benchmark

Koliko mali open-source modeli zaista znaju **srpski**? Engleski leaderboardi ne mere padeže.

**95 ručno pisanih zadataka** u 6 kategorija, svi modeli dobijaju identične promptove
na `temperature=0`. Nasumično pogađanje na pitanjima sa ponuđenim odgovorima daje
**{RANDOM_BASELINE}%** — sve ispod te linije znači da model ne razume zadatak.

Ocenjivanje: tačan odgovor za pitanja sa izborom, **F1** (preciznost + odziv) za NER,
pokrivenost ključnih pojmova za prevod.
"""

FINDINGS = """
### Šta merenja pokazuju

- **Padeži su najteži.** Nijedan testirani model ne prelazi 50%, a neki padaju
  ispod nasumičnog pogađanja — bolje bi prošli da su odgovarali nasumično.
- **NER je najlakši.** Izdvajanje imena i mesta ide preko 95% kod najboljih jer je
  uglavnom prepisivanje iz teksta, bez morfologije.
- **Veličina nije sve.** Mistral 7B vodi, ali gemma2 sa 2B parametara tuče i
  qwen2.5:3b i phi3:mini — podaci za treniranje znače više od broja parametara.
- **Ispod ~2B se gubi zadatak.** llama3.2:1b na razumevanju ima 20%, jer često ne
  odgovori slovom nego napiše nepovezan tekst.
"""

METHODOLOGY = """
### Metodologija

**Kategorije (95 zadataka)**

| Kategorija | Zadataka | Šta meri |
|---|---|---|
| Gramatika | 20 | slaganje subjekta i predikata, glagolski oblici, „trebati" |
| Padeži | 20 | svih sedam padeža, rekcija predloga i glagola |
| Pravopis | 15 | č/ć, dž/đ, spojeno i odvojeno pisanje, jednačenje |
| Razumevanje | 15 | izvlačenje činjenica, poređenje, idiomi, ironija |
| NER | 15 | imena, gradovi, firme, datumi, iznosi, kontakti |
| Prevod | 10 | srpski ↔ engleski, u oba smera |

**Zaštita od varanja u ocenjivanju.** NER se ocenjuje F1 merom, ne samo odzivom:
model koji prepiše celu rečenicu dobija visok odziv, ali niska preciznost mu obara
rezultat na ~0.6 umesto 1.0. Poređenje zanemaruje dijakritike i transliterira
ćirilicu, pa „Niš", „Nis" i „Ниш" prolaze isto — srpski je dvoazbučan, meri se
znanje jezika a ne pismo.

Ocenjivanje pokriva skup testova (`bench/test_scoring.py`), napisan nakon što su
dva buga obarala rezultate: hvatanje slova „a" unutar reči „Dva" kao odgovora A, i
normalizacija koja je brisala ćirilicu u prazan string.

**Pokretanje lokalno**

```bash
ollama serve
python bench/run.py --model ollama:mistral:latest
```

**Ograničenja.** Zadatke je pisao jedan izvorni govornik, standardni srpski,
ekavica. Testirani su modeli koji staju na laptop (1.5B–7B). Skup je mali (95
zadataka), pa razlike ispod nekoliko procentnih poena nisu značajne.
"""


with gr.Blocks(title="Serbian LLM Benchmark") as demo:
    gr.Markdown(DESCRIPTION)

    with gr.Tab("Rang lista"):
        gr.Dataframe(
            value=build_table(),
            interactive=False,
            wrap=True,
        )
        gr.Markdown(FINDINGS)

    with gr.Tab("Po kategorijama"):
        gr.Markdown("Prosek svih modela po kategoriji — niže je teže.")
        gr.Dataframe(value=category_breakdown(), interactive=False)

    with gr.Tab("Metodologija"):
        gr.Markdown(METHODOLOGY)


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
