"""
Capstone: structured run logging.

Every question that goes through `app.py::ask_pipeline` (the command line and
serve.py both use it) appends exactly one JSON object to logs/runs.jsonl,
whether the run answered, was refused, failed gracefully, or crashed. The
write happens in a `finally`, so a crash still leaves a record.

Read it back with:
    python runlog.py            # last 10 runs as a table
    python runlog.py --stats    # averages over every ok run
"""

import json
import sys
import time
import uuid
from datetime import datetime, timezone

import config

LOG_DIR = config.ROOT / "logs"
LOG_PATH = LOG_DIR / "runs.jsonl"


def new_record(question: str, entrypoint: str) -> dict:
    return {
        "run_id": uuid.uuid4().hex[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "entrypoint": entrypoint,          # "cli" or "http"
        "question": question,
        "corpus": None,
        "model": config.MODEL,
        # one of: ok, refused, failed (handled generation failure), error (crash)
        "status": None,
        "answer": None,
        "failure_kind": None,
        "failure_detail": None,
        "best_distance": None,
        "threshold": None,
        "chunks_retrieved": None,
        "sources": [],
        "model_calls": 0,                   # includes retries
        "cache_hit": False,
        "tokens_in": 0,
        "tokens_out": 0,
        "retrieval_s": None,
        "generation_s": None,
        "duration_s": None,
        "timeout_s": config.GENERATION_TIMEOUT_S,
    }


def write(record: dict) -> None:
    """Append one record. Never lets logging break the run it describes."""
    try:
        LOG_DIR.mkdir(exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # noqa: BLE001
        print(f"  [runlog] couldn't write log: {exc}", file=sys.stderr)


def read_all() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    rows = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.seconds = round(time.perf_counter() - self.start, 3)
        return False


def _main(argv: list[str]) -> None:
    rows = read_all()
    if "--stats" in argv:
        ok = [r for r in rows if r.get("status") == "ok" and not r.get("cache_hit")]
        if not ok:
            print("No uncached ok runs logged yet.")
            return
        n = len(ok)
        avg = lambda k: sum(r.get(k) or 0 for r in ok) / n  # noqa: E731
        print(f"{n} uncached ok runs")
        print(f"  avg duration_s   {avg('duration_s'):.3f}")
        print(f"  avg retrieval_s  {avg('retrieval_s'):.3f}")
        print(f"  avg generation_s {avg('generation_s'):.3f}")
        print(f"  avg tokens_in    {avg('tokens_in'):.1f}")
        print(f"  avg tokens_out   {avg('tokens_out'):.1f}")
        print(f"  avg model_calls  {avg('model_calls'):.2f}")
        by_status = {}
        for r in rows:
            by_status[r.get("status")] = by_status.get(r.get("status"), 0) + 1
        print(f"  all runs by status: {by_status}")
        return
    for r in rows[-10:]:
        print(
            f"{r['timestamp']}  {r['run_id']}  {r['status']:<8} "
            f"{(r.get('failure_kind') or ''):<8} {r['duration_s']:>7}s  "
            f"{r['tokens_in']:>4}/{r['tokens_out']:<4} {r['question'][:45]}"
        )


if __name__ == "__main__":
    _main(sys.argv[1:])
