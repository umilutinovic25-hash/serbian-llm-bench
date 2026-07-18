# Objavljivanje

Postoje tri načina, svi besplatni. Statična stranica u `docs/` radi već sada i ne
zavisi ni od čega.

## 1. GitHub Pages (statična stranica, bez ikakvog tokena)

```bash
gh repo create serbian-llm-bench --public --source=. --push
gh api -X POST repos/:owner/serbian-llm-bench/pages -f source[branch]=main -f source[path]=/docs
```

Rezultat: `https://<korisnik>.github.io/serbian-llm-bench`

## 2. Hugging Face Space (interaktivni leaderboard)

HF token je **besplatan** — nije plaćena usluga, kao ni hosting Space-a na free
tieru. Napravi ga na https://huggingface.co/settings/tokens → New token → tip
**Write**.

```bash
cd ~/serbian-llm-bench
.venv/bin/hf auth login          # nalepi token kad pita
.venv/bin/hf upload uros69/serbian-llm-bench . --repo-type=space
```

Ako Space ne postoji, `upload` ga pravi sam. Posle par minuta build-a leaderboard je
live na `https://huggingface.co/spaces/uros69/serbian-llm-bench`.

## 3. Lokalno (za probu pre objavljivanja)

```bash
.venv/bin/python app.py     # Gradio leaderboard na http://127.0.0.1:7860
open docs/index.html        # statična verzija
```
