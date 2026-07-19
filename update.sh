#!/usr/bin/env bash
#
# Measure every installed ollama model, rebuild the page, publish everywhere.
#
#   ./update.sh              measure all installed models, then publish
#   ./update.sh --no-push    measure and rebuild, but do not publish
#   ./update.sh gemma3:4b    measure one model only, then publish
#
set -euo pipefail

cd "$(dirname "$0")"

PUSH=1
MODELS=()
for arg in "$@"; do
  case "$arg" in
    --no-push) PUSH=0 ;;
    -*) echo "Nepoznata opcija: $arg" >&2; exit 2 ;;
    *) MODELS+=("$arg") ;;
  esac
done

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

# --- 1. scoring tests must pass before any number is trusted -----------------
say "1/5  Testovi ocenjivanja"
python3 bench/test_scoring.py

# --- 2. ollama must be up ----------------------------------------------------
say "2/5  Provera ollame"
if ! curl -sf -o /dev/null --max-time 5 http://localhost:11434/api/tags; then
  echo "Pokrećem ollama serve..."
  nohup ollama serve > /tmp/ollama.log 2>&1 &
  until curl -sf -o /dev/null --max-time 3 http://localhost:11434/api/tags; do sleep 2; done
fi

if [ ${#MODELS[@]} -eq 0 ]; then
  while IFS= read -r model; do MODELS+=("$model"); done < <(
    curl -s http://localhost:11434/api/tags |
      python3 -c "import json,sys; [print(m['name']) for m in json.load(sys.stdin)['models']]"
  )
fi
echo "Modeli: ${MODELS[*]}"

# --- 3. benchmark ------------------------------------------------------------
say "3/5  Merenje (${#MODELS[@]} modela)"
failed=()
for model in "${MODELS[@]}"; do
  echo "--- $model"
  if ! python3 bench/run.py --model "ollama:$model" 2>&1 | tail -9; then
    echo "PAO: $model" >&2
    failed+=("$model")
  fi
done
rm -f results/mock.json
[ ${#failed[@]} -gt 0 ] && echo "Nisu izmereni: ${failed[*]}" >&2

# --- 4. regenerate the page from results -------------------------------------
say "4/5  Generisanje stranice"
python3 bench/build_page.py

if [ "$PUSH" -eq 0 ]; then
  say "Gotovo (bez objavljivanja)."
  exit 0
fi

if git diff --quiet && git diff --cached --quiet; then
  say "Nema promena — ništa se ne objavljuje."
  exit 0
fi

# --- 5. publish to GitHub and Hugging Face -----------------------------------
say "5/5  Objavljivanje"
stamp=$(date +%Y-%m-%d)
git add -A
git commit -q -m "results: re-measure benchmark ($stamp)"
git push -q origin main
echo "GitHub ✓  https://umilutinovic25-hash.github.io/serbian-llm-bench/"

if [ -z "${HF_TOKEN:-}" ]; then
  echo "HF_TOKEN nije postavljen — Space preskočen."
  echo "  export HF_TOKEN=\$(pbpaste)   pa ponovo ./update.sh"
  exit 0
fi

space_dir=$(mktemp -d)
trap 'rm -rf "$space_dir"' EXIT
git clone -q "https://uros69:${HF_TOKEN}@huggingface.co/spaces/uros69/serbian-llm-bench" "$space_dir"
cp docs/index.html "$space_dir/index.html"
(
  cd "$space_dir"
  git add -A
  if git diff --cached --quiet; then
    echo "Space već ažuran."
  else
    git commit -q -m "Update results ($stamp)"
    git push -q origin main
    echo "HF Space ✓  https://huggingface.co/spaces/uros69/serbian-llm-bench"
  fi
)
