"""Loading and scoring of Serbian benchmark tasks."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CATEGORIES = ["gramatika", "padezi", "pravopis", "razumevanje", "ner", "prevod"]

LETTERS = ["A", "B", "C", "D", "E"]


@dataclass
class Task:
    id: str
    category: str
    type: str
    prompt: str
    choices: list[str] = field(default_factory=list)
    answer: str = ""
    expected: list[list[str]] = field(default_factory=list)
    keywords: list[list[str]] = field(default_factory=list)

    def render(self) -> str:
        if self.type == "mc":
            lines = [self.prompt, ""]
            for letter, choice in zip(LETTERS, self.choices):
                lines.append(f"{letter}) {choice}")
            lines.append("")
            lines.append("Odgovori isključivo jednim slovom (A, B ili C).")
            return "\n".join(lines)
        if self.type == "extract":
            return self.prompt + "\n\nOdgovori tako što ćeš navesti pronađene pojmove razdvojene zarezom, bez dodatnog teksta."
        return self.prompt


def load_tasks(categories: list[str] | None = None) -> list[Task]:
    wanted = categories or CATEGORIES
    tasks: list[Task] = []
    for category in wanted:
        path = DATA_DIR / f"{category}.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                tasks.append(Task(**json.loads(line)))
    return tasks


def _fold(text: str) -> str:
    """Lowercase, strip diacritics and punctuation so č/c and š/s compare equal."""
    text = text.lower()
    text = text.replace("đ", "dj").replace("ђ", "dj")
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9@./\s-]", " ", stripped)


def _extract_letter(response: str, n_choices: int) -> str | None:
    valid = LETTERS[:n_choices]
    head = response.strip()[:400]
    patterns = [
        r"^\s*\(?([A-E])\)?\s*[).:,-]",   # "B)" / "B." / "(B)"
        r"^\s*([A-E])\s*$",                 # bare letter
        r"odgovor\D{0,15}([A-E])\b",       # "odgovor je B"
        r"\b([A-E])\)",                     # first "B)" anywhere
    ]
    for pattern in patterns:
        match = re.search(pattern, head, re.IGNORECASE | re.MULTILINE)
        if match and match.group(1).upper() in valid:
            return match.group(1).upper()
    return None


def score(task: Task, response: str) -> tuple[float, str]:
    """Return (score in 0..1, short note explaining the grade)."""
    if not response.strip():
        return 0.0, "prazan odgovor"

    if task.type == "mc":
        letter = _extract_letter(response, len(task.choices))
        if letter is None:
            # Model may have written the answer text instead of a letter.
            folded = _fold(response)
            correct_text = _fold(task.choices[LETTERS.index(task.answer)])
            others = [
                _fold(c)
                for i, c in enumerate(task.choices)
                if LETTERS[i] != task.answer
            ]
            hit = correct_text in folded
            if hit and not any(o in folded for o in others):
                return 1.0, "tačan tekst odgovora (bez slova)"
            return 0.0, "nije prepoznato slovo odgovora"
        return (1.0, "tačno") if letter == task.answer else (0.0, f"dao {letter}, tačno {task.answer}")

    if task.type == "extract":
        # F1 rather than recall: echoing the whole sentence must not score 1.0.
        items = [i.strip() for i in re.split(r"[,\n;]", response) if i.strip()]
        matched_groups = set()
        matched_items = 0
        for item in items:
            folded_item = _fold(item)
            for index, variants in enumerate(task.expected):
                if any(_fold(v) in folded_item for v in variants):
                    matched_groups.add(index)
                    matched_items += 1
                    break
        recall = len(matched_groups) / len(task.expected)
        precision = matched_items / len(items) if items else 0.0
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        return f1, f"P {precision:.2f} R {recall:.2f} F1 {f1:.2f}"

    if task.type == "translate":
        folded = _fold(response)
        found = sum(1 for variants in task.keywords if any(_fold(v) in folded for v in variants))
        total = len(task.keywords)
        return found / total, f"pogođeno {found}/{total} ključnih pojmova"

    return 0.0, f"nepoznat tip zadatka: {task.type}"
