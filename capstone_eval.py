#!/usr/bin/env python3
"""
Capstone Milestone 5: run one trial of every criterion in capstone_criteria.md.

    python capstone_eval.py 1      # trial 1 -> results/capstone_trial_1.json + .md

What one trial runs:
  - 3 failure types x 5 runs, each `python app.py ask ...` in a fresh process
    with the trigger env var set           -> criteria 1, 2, 3, 4
  - the 5 questions in questions.py twice, in one process   -> criterion 5
  - the 5 OUT_OF_SCOPE questions, in the same process       -> criterion 5

Every number comes from the rows this trial appended to logs/runs.jsonl
(`runlog.py`) plus each subprocess's exit code and output. Nothing here
changes the system under test.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "runs.jsonl"
RESULTS = ROOT / "results"
PY = sys.executable

QUESTION = "how does the housing lottery work?"
RUNS_PER_TYPE = 5
PAUSE_S = 2  # between subprocess runs, to stay well under the free-tier RPM

TRIGGERS = {
    "timeout": {"AI201_TIMEOUT_S": "0.05"},
    "auth": {"GEMINI_API_KEY": "not-a-real-key"},
    "network": {"HTTPS_PROXY": "http://127.0.0.1:9"},
}
EXPECTED_CALLS = {"timeout": 2, "auth": 1, "network": 2}
MAX_FAIL_S = 10.0
MAX_AVG_OK_S = 2.0


def log_rows() -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]


def new_rows(before: int) -> list[dict]:
    return log_rows()[before:]


def run_triggered(kind: str) -> dict:
    env = {**os.environ, "AI201_CACHE": "0", "PYTHONIOENCODING": "utf-8", **TRIGGERS[kind]}
    before = len(log_rows())
    proc = subprocess.run(
        [PY, "app.py", "ask", QUESTION],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=180,
    )
    rows = new_rows(before)
    output = proc.stdout + proc.stderr
    return {
        "trigger": kind,
        "exit_code": proc.returncode,
        "traceback": "Traceback (most recent call last)" in output,
        "log": rows[-1] if rows else None,
        "log_rows_written": len(rows),
        "output_tail": output.strip().splitlines()[-3:],
    }


NORMAL_SNIPPET = r"""
import json
from questions import answered, OUT_OF_SCOPE
from app import ask_pipeline
for q in [q["question"] for q in answered()] * 2:
    ask_pipeline(q)
for q in OUT_OF_SCOPE:
    ask_pipeline(q)
"""


def run_normal() -> dict:
    env = {**os.environ, "AI201_CACHE": "0", "PYTHONIOENCODING": "utf-8"}
    for k in ("AI201_TIMEOUT_S", "HTTPS_PROXY"):
        env.pop(k, None)
    before = len(log_rows())
    proc = subprocess.run(
        [PY, "-c", NORMAL_SNIPPET], cwd=ROOT, env=env, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=600,
    )
    rows = new_rows(before)
    return {"exit_code": proc.returncode, "in_scope": rows[:10], "out_of_scope": rows[10:15],
            "stderr_tail": proc.stderr.strip().splitlines()[-3:]}


def score(triggered: list[dict], normal: dict) -> dict:
    by_kind = {k: [r for r in triggered if r["trigger"] == k] for k in TRIGGERS}

    def logged(r, key, default=None):
        return (r["log"] or {}).get(key, default)

    c1 = {k: sum(logged(r, "status") == "failed" and logged(r, "failure_kind") == k
                 for r in rs) for k, rs in by_kind.items()}
    c2_crashes = sum(
        logged(r, "status") == "error" or r["exit_code"] != 0 or r["traceback"]
        or r["log"] is None
        for r in triggered
    )
    c3 = {k: sum(logged(r, "model_calls") == EXPECTED_CALLS[k] for r in rs)
          for k, rs in by_kind.items()}
    c4 = {k: sum((logged(r, "duration_s") or 1e9) <= MAX_FAIL_S for r in rs)
          for k, rs in by_kind.items()}
    c4_max = {k: max((logged(r, "duration_s") or 0) for r in rs) for k, rs in by_kind.items()}

    ins, oos = normal["in_scope"], normal["out_of_scope"]
    c5_ok = sum(r["status"] == "ok" and bool((r["answer"] or "").strip()) and len(r["sources"]) >= 1
                for r in ins)
    c5_avg = round(sum(r["duration_s"] for r in ins) / len(ins), 3) if ins else None
    c5_refused = sum(r["status"] == "refused" and r["model_calls"] == 0 for r in oos)

    n = RUNS_PER_TYPE
    return {
        "c1": {"per_type": c1, "met": all(v >= 4 for v in c1.values()),
               "cell": " · ".join(f"{k} {v}/{n}" for k, v in c1.items())},
        "c2": {"crashes": c2_crashes, "met": c2_crashes == 0,
               "cell": f"{c2_crashes} crashes / {len(triggered)}"},
        "c3": {"per_type": c3, "met": all(v == n for v in c3.values()),
               "cell": " · ".join(f"{k} {v}/{n}" for k, v in c3.items())},
        "c4": {"per_type": c4, "max_s": c4_max, "met": all(v == n for v in c4.values()),
               "cell": " · ".join(f"{k} {c4[k]}/{n} (max {c4_max[k]}s)" for k in c4)},
        "c5": {"ok": c5_ok, "of": len(ins), "avg_s": c5_avg, "refused": c5_refused,
               "met": c5_ok == 10 and len(ins) == 10 and c5_avg is not None
                      and c5_avg <= MAX_AVG_OK_S and c5_refused == 5,
               "cell": f"{c5_ok}/{len(ins)} ok, avg {c5_avg}s, {c5_refused}/5 refused"},
    }


def main():
    trial = sys.argv[1] if len(sys.argv) > 1 else "1"
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Trial {trial} — started {started}")

    triggered = []
    for kind in TRIGGERS:
        for i in range(RUNS_PER_TYPE):
            r = run_triggered(kind)
            triggered.append(r)
            lg = r["log"] or {}
            print(f"  {kind:8s} #{i+1}  exit={r['exit_code']} status={lg.get('status')} "
                  f"kind={lg.get('failure_kind')} calls={lg.get('model_calls')} "
                  f"{lg.get('duration_s')}s  run_id={lg.get('run_id')}")
            time.sleep(PAUSE_S)

    print("  normal path: 10 in-scope + 5 out-of-scope in one process ...")
    normal = run_normal()
    for r in normal["in_scope"] + normal["out_of_scope"]:
        print(f"  normal   {r['run_id']} {r['status']:8s} calls={r['model_calls']} "
              f"{r['duration_s']}s  {r['question'][:50]}")

    scores = score(triggered, normal)
    for c, s in scores.items():
        print(f"  {c.upper()}: {'MET ' if s['met'] else 'MISS'}  {s['cell']}")

    RESULTS.mkdir(exist_ok=True)
    out = {"trial": trial, "started": started, "scores": scores,
           "triggered": triggered, "normal": normal}
    path = RESULTS / f"capstone_trial_{trial}.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
