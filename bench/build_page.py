"""Generate docs/index.html from results/*.json.

The published page must never be hand-edited: every number here is read from a
result file, so re-running the benchmark and rebuilding is the only way results
change.
"""

from __future__ import annotations

import html
import json
import statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
HEAD_FILE = Path(__file__).resolve().parent / "page_head.html"
OUT_FILE = ROOT / "docs" / "index.html"

CHANCE = 33.3          # random guessing on three-choice questions
STRONG = 90.0          # highlighted as a strong score

CATEGORY_ORDER = ["gramatika", "padezi", "pravopis", "razumevanje", "ner", "prevod"]
CATEGORY_LABELS = {
    "gramatika": "Gramatika",
    "padezi": "Padeži",
    "pravopis": "Pravopis",
    "razumevanje": "Razumevanje",
    "ner": "NER",
    "prevod": "Prevod",
}
CATEGORY_SHORT = dict(CATEGORY_LABELS, razumevanje="Razumev.")

# Parameter counts are not in the result files; ollama tags do not always carry them.
MODEL_SIZES = {
    "mistral:latest": ("mistral", "7B"),
    "gemma2:2b": ("gemma2", "2B"),
    "qwen2.5:3b": ("qwen2.5", "3B"),
    "llama3.2:latest": ("llama3.2", "3B"),
    "qwen2.5:1.5b": ("qwen2.5", "1.5B"),
    "phi3:mini": ("phi3 mini", "3.8B"),
    "llama3.2:1b": ("llama3.2", "1B"),
    "gemma3:4b": ("gemma3", "4B"),
}

MONTHS = [
    "januar", "februar", "mart", "april", "maj", "jun",
    "jul", "avgust", "septembar", "oktobar", "novembar", "decembar",
]


def load_results() -> list[dict]:
    results = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["model"] == "mock":
            continue
        tag = data["model"].replace("ollama:", "")
        name, size = MODEL_SIZES.get(tag, (tag, ""))
        data["tag"] = tag
        data["display_name"] = name
        data["size"] = size
        results.append(data)
    if not results:
        raise SystemExit("Nema rezultata u results/ — pokreni bench/run.py prvo.")
    return sorted(results, key=lambda d: d["overall"], reverse=True)


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def build_board(results: list[dict]) -> str:
    rows = [
        '      <div class="board-row board-head">\n'
        "        <span>#</span>\n"
        "        <span>Model</span>\n"
        '        <span class="track-head">Ukupno</span>\n'
        '        <span class="score">%</span>\n'
        "      </div>"
    ]
    for rank, data in enumerate(results, 1):
        size = f' <span class="model-size">{esc(data["size"])}</span>' if data["size"] else ""
        rows.append(
            f'      <div class="board-row">\n'
            f'        <span class="rank">{rank}</span>\n'
            f'        <span class="model-name">{esc(data["display_name"])}{size}</span>\n'
            f'        <div class="track"><div class="fill" style="width: {data["overall"]}%"></div>'
            f'<div class="chance"></div></div>\n'
            f'        <span class="score">{data["overall"]}</span>\n'
            f"      </div>"
        )
    return "\n".join(rows)


def build_difficulty(results: list[dict]) -> tuple[str, list[tuple[str, float]]]:
    averages = []
    for key in CATEGORY_ORDER:
        scores = [d["categories"][key]["score"] for d in results if key in d["categories"]]
        if scores:
            averages.append((key, round(statistics.mean(scores), 1)))
    averages.sort(key=lambda pair: pair[1])

    hardest = averages[0][0] if averages else None
    rows = []
    for key, value in averages:
        hard = " hard" if key == hardest else ""
        rows.append(
            f'      <div class="diff-row">\n'
            f'        <span class="diff-label">{esc(CATEGORY_LABELS[key])}</span>\n'
            f'        <div class="diff-track"><div class="diff-fill{hard}" style="width: {value}%"></div></div>\n'
            f'        <span class="diff-score">{value}</span>\n'
            f"      </div>"
        )
    return "\n".join(rows), averages


def cell_class(value: float) -> str:
    if value < CHANCE:
        return ' class="below"'
    if value >= STRONG:
        return ' class="strong"'
    return ""


def build_table(results: list[dict]) -> str:
    header = "".join(
        f'            <th scope="col">{esc(CATEGORY_SHORT[key])}</th>\n'
        for key in CATEGORY_ORDER
    )
    rows = []
    for data in results:
        label = f'{data["display_name"]} {data["size"]}'.strip()
        cells = "".join(
            f'<td{cell_class(data["categories"][key]["score"])}>{data["categories"][key]["score"]}</td>'
            if key in data["categories"] else "<td>—</td>"
            for key in CATEGORY_ORDER
        )
        rows.append(
            f'          <tr>\n'
            f'            <th scope="row">{esc(label)}</th>\n'
            f'            <td class="lead">{data["overall"]}</td>{cells}\n'
            f"          </tr>"
        )
    return (
        '        <thead>\n          <tr>\n'
        '            <th scope="col">Model</th>\n'
        '            <th scope="col">Ukupno</th>\n'
        f"{header}"
        "          </tr>\n        </thead>\n"
        "        <tbody>\n" + "\n".join(rows) + "\n        </tbody>"
    )


def build_findings(results: list[dict], averages: list[tuple[str, float]]) -> str:
    hardest_key, hardest_avg = averages[0]
    easiest_key, easiest_avg = averages[-1]

    # Tag, not display name: llama3.2:latest and llama3.2:1b share a display name.
    below = [
        (d["tag"], d["categories"][hardest_key]["score"])
        for d in results
        if hardest_key in d["categories"] and d["categories"][hardest_key]["score"] < CHANCE
    ]
    best_hard = max(d["categories"][hardest_key]["score"] for d in results if hardest_key in d["categories"])
    below_text = (
        " ".join(f"<code>{esc(name)}</code> ({score}%)," for name, score in below).rstrip(",")
        + " su ispod nasumičnog pogađanja — bolje bi prošli da su bacali novčić."
        if below else "Nijedan model nije ispod nasumičnog pogađanja."
    )

    worst = results[-1]
    worst_key = min(worst["categories"], key=lambda k: worst["categories"][k]["score"])
    worst_score = worst["categories"][worst_key]["score"]

    # "Size is not decisive" must name a model that actually outranks larger ones,
    # or the page asserts something the data contradicts.
    def billions(data: dict) -> float | None:
        size = data["size"].removesuffix("B")
        try:
            return float(size)
        except ValueError:
            return None

    upset, beaten = results[0], 0
    for index, data in enumerate(results):
        mine = billions(data)
        if mine is None:
            continue
        larger = [
            other for other in results[index + 1:]
            if (theirs := billions(other)) is not None and theirs > mine
        ]
        if len(larger) > beaten:
            upset, beaten = data, len(larger)

    if beaten:
        names = ", ".join(f"<code>{esc(o['tag'])}</code>" for o in results if
                          (b := billions(o)) is not None and (u := billions(upset)) is not None
                          and b > u and o["overall"] < upset["overall"])
        upset_text = (
            f"<code>{esc(upset['tag'])}</code> sa {esc(upset['size'])} parametara je "
            f"ispred {beaten} {'većeg modela' if beaten == 1 else 'većih modela'} "
            f"({names}). Zastupljenost srpskog u podacima za treniranje znači više "
            f"od broja parametara."
        )
    else:
        upset_text = (
            "Poredak prati veličinu modela — nijedan manji model ne pretiče većeg. "
            "Uz ovako mali uzorak modela to je očekivano, ali nije pravilo."
        )

    return f"""      <div class="finding">
        <div class="figure">{hardest_avg}%</div>
        <h3>{esc(CATEGORY_LABELS[hardest_key])} — najteža kategorija</h3>
        <p>
          Nijedan model ne prelazi {best_hard}%. {below_text}
          Sedmopadežni sistem sa rekcijom predloga je ono što ovi modeli nisu naučili.
        </p>
      </div>

      <div class="finding">
        <div class="figure">{easiest_avg}%</div>
        <h3>{esc(CATEGORY_LABELS[easiest_key])} — najlakša kategorija</h3>
        <p>
          Izdvajanje imena, gradova i iznosa je uglavnom prepisivanje iz teksta.
          Morfologija se ne dira, pa i najslabiji modeli prolaze — visok skor ovde
          ne znači znanje jezika.
        </p>
      </div>

      <div class="finding">
        <div class="figure">{esc(upset["size"] or "—")}</div>
        <h3>Veličina nije presudna</h3>
        <p>
          {upset_text}
        </p>
      </div>

      <div class="finding">
        <div class="figure">{worst_score}%</div>
        <h3>Ispod ~2B se gubi zadatak</h3>
        <p>
          <code>{esc(worst["tag"])}</code> na kategoriji
          „{esc(CATEGORY_LABELS[worst_key].lower())}" često uopšte ne odgovori slovom
          nego napiše nepovezan tekst. <code>phi3:mini</code> sklizne u ćirilicu i
          piše rečenice koje nisu srpski: „Визимото је пропуштано".
        </p>
      </div>"""


def render() -> str:
    results = load_results()
    board = build_board(results)
    difficulty, averages = build_difficulty(results)
    table = build_table(results)
    findings = build_findings(results, averages)

    total_tasks = results[0]["total_tasks"]
    today = date.today()
    stamp = f"{MONTHS[today.month - 1]} {today.year}"
    hardest_key, hardest_avg = averages[0]

    body = f"""<div class="wrap">

  <header class="masthead">
    <div class="eyebrow">Otvoreni benchmark · {stamp}</div>
    <h1>Koliko mali modeli zaista znaju <span class="alt">српски</span>?</h1>
    <p class="standfirst">
      Engleski leaderboardi ne mere padeže. Model može biti odličan na MMLU i i dalje
      ne znati u koji padež ide imenica posle predloga „uprkos".
    </p>
    <div class="facts">
      <span><b>{total_tasks}</b> zadataka</span>
      <span><b>{len(results)}</b> modela</span>
      <span><b>{len(CATEGORY_ORDER)}</b> kategorija</span>
      <span><b>temperature 0</b></span>
    </div>
  </header>

  <section>
    <h2>Rang lista</h2>
    <p class="section-note">
      Ukupan rezultat po modelu. Isprekidana linija je <b>{CHANCE}%</b> — koliko donosi
      nasumično pogađanje na pitanjima sa tri ponuđena odgovora. Rezultat blizu nje
      znači da model ne razume zadatak, a ne da je „malo slabiji".
    </p>

    <div class="board">
{board}
    </div>

    <div class="board-legend">
      <span class="legend-mark"></span>
      <span>nasumično pogađanje · {CHANCE}%</span>
    </div>
  </section>

  <section>
    <h2>Šta je teško, a šta lako</h2>
    <div class="difficulty">
{difficulty}
    </div>
    <p class="section-note">Prosek svih {len(results)} modela po kategoriji.</p>
  </section>

  <section>
    <h2>Nalazi</h2>
    <div class="findings">

{findings}

    </div>
  </section>

  <section>
    <h2>Rezultati po kategorijama</h2>
    <div class="table-scroll">
      <table>
        <caption>
          Crveno je ispod nasumičnog pogađanja ({CHANCE}%), zeleno je preko {int(STRONG)}%.
        </caption>
{table}
      </table>
    </div>
  </section>

  <section>
    <h2>Kako se meri</h2>

    <div class="method">
      <h3>Ocenjivanje</h3>
      <p>
        Pitanja sa izborom se ocenjuju tačno/netačno. NER se ocenjuje <strong>F1
        merom, ne odzivom</strong>: model koji prepiše celu rečenicu ima savršen
        odziv, ali ga preciznost obara na 0.62 umesto 1.0. Bez toga se benchmark
        trivijalno vara. Prevod se meri pokrivenošću ključnih pojmova, sa
        priznatim sinonimima.
      </p>
      <p>
        Poređenje zanemaruje dijakritike i <strong>transliterira ćirilicu</strong> —
        „Niš", „Nis" i „Ниш" prolaze isto. Srpski je dvoazbučan, pa bi kažnjavanje
        ćiriličnog odgovora merilo pismo umesto znanja jezika.
      </p>
    </div>

    <div class="method">
      <h3>Dva buga koja su obarala rezultate</h3>
      <p>
        Testovi ocenjivanja postoje jer su ove greške već pokvarile merenje. Obe su
        nađene proverom sumnjivo niskog rezultata, pa su svi modeli mereni ponovo.
      </p>
      <div class="bugs">
        <div class="bug">
          <span class="bug-tag">regex</span>
          <span>
            Izvlačenje slova radilo je sa <code>IGNORECASE</code>, pa je
            <code>[A-E]</code> hvatalo malo „a" unutar običnih reči — odgovor
            „Dvojkodak je odgovor: B) Dva" čitan je kao <b>A</b>. Model je bio u
            pravu, grader nije.
          </span>
        </div>
        <div class="bug">
          <span class="bug-tag">unicode</span>
          <span>
            Normalizacija teksta brisala je ćirilicu u prazan string, pa bi ispravan
            ćirilični odgovor dobio nulu.
          </span>
        </div>
      </div>
    </div>

    <div class="method">
      <h3>Pokretanje</h3>
      <pre><code>ollama serve
python bench/run.py --model ollama:mistral:latest
python bench/test_scoring.py
./update.sh                     # izmeri sve, regeneriši stranicu, objavi</code></pre>
      <p>
        Modeli se pokreću lokalno preko ollame, bez API troška. Rezultati se upisuju
        u <code>results/&lt;model&gt;.json</code> sa odgovorom i ocenom za svaki
        zadatak, pa se svaka greška može pregledati pojedinačno.
      </p>
      <p>
        <strong>Ova stranica je generisana</strong> iz tih JSON fajlova
        (<code>bench/build_page.py</code>) — brojevi se ne kucaju ručno, pa ne mogu
        da se raziđu sa merenjima.
      </p>
    </div>

    <div class="method">
      <h3>Ograničenja</h3>
      <p>
        Zadatke je pisao jedan izvorni govornik; standardni srpski, ekavica.
        Skup je mali ({total_tasks} zadataka), pa razlike ispod nekoliko procentnih
        poena nisu značajne. Testirani su samo modeli koji staju na laptop — veliki
        komercijalni modeli bi verovatno probili plafon svuda osim na kategoriji
        „{esc(CATEGORY_LABELS[hardest_key].lower())}".
      </p>
    </div>
  </section>

  <footer>
    <span class="status">
      Objavljeno i na <a href="https://huggingface.co/spaces/uros69/serbian-llm-bench">Hugging Face</a>.
      Kod, zadaci i harness: <a href="https://github.com/umilutinovic25-hash/serbian-llm-bench">GitHub</a>.
    </span>
    <span>Kod i podaci: Apache 2.0 · Uroš Milutinović</span>
  </footer>

</div>
</body>
</html>
"""
    return HEAD_FILE.read_text(encoding="utf-8") + body


if __name__ == "__main__":
    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(render(), encoding="utf-8")
    print(f"Stranica generisana: {OUT_FILE}")
