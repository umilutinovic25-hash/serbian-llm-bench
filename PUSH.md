# Objavljivanje na Hugging Face

Potreban je **write** token: https://huggingface.co/settings/tokens → New token → tip **Write**.

```bash
cd ~/serbian-llm-bench
.venv/bin/hf auth login          # nalepi token kad pita
.venv/bin/hf upload uros69/serbian-llm-bench . --repo-type=space
```

Ako Space ne postoji, `upload` ga pravi sam. Posle par minuta build-a leaderboard je
live na `https://huggingface.co/spaces/uros69/serbian-llm-bench`.

Za GitHub kopiju:

```bash
gh repo create serbian-llm-bench --public --source=. --push
```
