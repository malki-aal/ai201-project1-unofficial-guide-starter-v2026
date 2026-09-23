"""
Decide whether an answer counts as correct.

`run_eval.py` imports `judge` from here, if it exists, and uses it to mark
each run pass/fail instead of leaving the Run columns blank for you to read
by hand.

The rule: `expects` (from questions.py) is a short phrase naming the words a
correct answer has to contain — not a sentence to match verbatim. An answer
passes if every one of those words shows up in it somewhere, ignoring case,
punctuation, and simple plurals ("midterm" vs "midterms"). That's strict
enough to catch an answer that dodges the question, and loose enough to not
care about phrasing.
"""

from __future__ import annotations

import re

from store import Result

STOPWORDS = {"a", "an", "the", "of", "in", "on", "to", "and", "or", "is", "are"}


def normalize(text: str | None) -> str:
    """Lowercase, drop punctuation, collapse whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _stem(word: str) -> str:
    """Crude plural stripping — "midterms" -> "midterm". Good enough here."""
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def _keywords(text: str) -> set[str]:
    return {_stem(w) for w in normalize(text).split() if w not in STOPWORDS}


def judge(question: str, expects: str, answer: str, results: list[Result]) -> bool:
    """True if every keyword in `expects` appears somewhere in `answer`."""
    if not expects:
        return False

    expected_words = _keywords(expects)
    answer_words = _keywords(answer)
    return expected_words.issubset(answer_words)
