"""Run the Serbian benchmark against one model and write a JSON result file."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

from providers import ProviderError, get_provider
from tasks import CATEGORIES, load_tasks, score

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def run(provider_spec: str, categories: list[str] | None, limit: int | None, verbose: bool) -> dict:
    provider = get_provider(provider_spec)
    tasks = load_tasks(categories)
    if limit:
        tasks = tasks[:limit]

    records = []
    started = time.time()
    for index, task in enumerate(tasks, 1):
        task_started = time.time()
        try:
            response = provider.generate(task.render())
            error = None
        except ProviderError as exc:
            response, error = "", str(exc)
        points, note = score(task, response)
        elapsed = time.time() - task_started
        records.append({
            "id": task.id,
            "category": task.category,
            "score": points,
            "note": note,
            "seconds": round(elapsed, 2),
            "response": response[:300],
            "error": error,
        })
        marker = "OK " if points == 1.0 else ("~  " if points > 0 else "XX ")
        print(f"[{index}/{len(tasks)}] {marker} {task.id}  {note}  ({elapsed:.1f}s)", flush=True)
        if verbose and points < 1.0:
            print(f"        odgovor: {response[:160]!r}", flush=True)

    by_category = defaultdict(list)
    for record in records:
        by_category[record["category"]].append(record["score"])

    return {
        "model": provider_spec,
        "total_tasks": len(records),
        "overall": round(statistics.mean(r["score"] for r in records) * 100, 1) if records else 0.0,
        "categories": {
            category: {
                "score": round(statistics.mean(scores) * 100, 1),
                "tasks": len(scores),
            }
            for category, scores in sorted(by_category.items())
        },
        "total_seconds": round(time.time() - started, 1),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Serbian LLM benchmark runner")
    parser.add_argument("--model", required=True, help='npr. "ollama:qwen3:1.7b" ili "mock"')
    parser.add_argument("--categories", nargs="*", choices=CATEGORIES, default=None)
    parser.add_argument("--limit", type=int, default=None, help="Pokreni samo prvih N zadataka")
    parser.add_argument("--verbose", action="store_true", help="Ispiši odgovore za netačne zadatke")
    parser.add_argument("--out", default=None, help="Putanja izlaznog JSON fajla")
    args = parser.parse_args()

    result = run(args.model, args.categories, args.limit, args.verbose)

    RESULTS_DIR.mkdir(exist_ok=True)
    slug = args.model.replace(":", "_").replace("/", "_")
    out_path = Path(args.out) if args.out else RESULTS_DIR / f"{slug}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{result['model']}: {result['overall']}%  ({result['total_seconds']}s)")
    for category, stats in result["categories"].items():
        print(f"  {category:<14} {stats['score']:>5}%  ({stats['tasks']} zadataka)")
    print(f"\nRezultat sačuvan: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
