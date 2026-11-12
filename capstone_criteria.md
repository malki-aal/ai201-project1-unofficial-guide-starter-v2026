# Capstone criteria: hardening the Gemini call

> Drafted with Claude at my instructor's direction. The "at least 4 of 5"
> target in criterion 1 is mine. Written and committed before any Milestone 5
> results.

**How every criterion is tested.** Each criterion is checked in **3 trials**,
with no code or config changed between them. A "run" is one
`python app.py ask "<question>"` in a fresh process with `AI201_CACHE=0`, so
every run is a real call. All evidence comes from `logs/runs.jsonl` and the
command's exit code. Failures are triggered with the environment variables
in RUNNING.md:

| Failure | Trigger | Expected `failure_kind` |
|---|---|---|
| Timeout | `AI201_TIMEOUT_S=0.05` | `timeout` |
| Bad API key | `GEMINI_API_KEY=not-a-real-key` | `auth` |
| Network down | `HTTPS_PROXY=http://127.0.0.1:9` | `network` |

The question for every triggered run is `how does the housing lottery work?`
(it passes the relevance gate, so the run actually reaches Gemini).

A criterion is **MET** only if all 3 trials hit the target.

---

## 1. Each triggered failure is named correctly (extension)

**Target:** For each of the 3 failure types, at least **4 of 5** runs end with
`status: "failed"` **and** the `failure_kind` from the table above, so the user
sees that failure's specific fallback message. Checked per type, per trial:
3 types × 5 runs = 15 runs per trial.

**Why 4 of 5 and not 5 of 5:** two of these triggers depend on the network.
The timeout races a real request, and the proxy trigger relies on a refused
connection. In M3 the timeout trigger came back as `client` once, because
Gemini's own 400 beat our timeout. That's fixed, but I'm leaving room for one
timing-dependent misfire. A misfire still shows a readable message, not a
crash; criterion 2 covers crashes separately.

**Why not 3 of 5:** the message for each kind tells the user what to do.
"Check your key" when the network is down sends them to fix the wrong thing.
Getting it wrong 2 times in 5 would make the messages untrustworthy.

## 2. No triggered failure crashes the run (bad path, extension)

**Target:** Across all 15 triggered runs in a trial, **0** runs have
`status: "error"`, **0** runs exit with a non-zero exit code, and **0** runs
print a Python traceback.

**Why zero:** not crashing is the whole point of the extension. Before it, all
three of these failures ended the run with an exception (a bad key or network
error), or hung forever (a timeout). These are failures I chose and know the
exact cause of. If even one of them still crashes, the hardening doesn't work
for that path. There's no timing excuse here either: even a misclassified
failure from criterion 1 must still come back as `failed`, not `error`.

## 3. Transient failures are retried once; permanent ones aren't retried (extension)

**Target:** In **5 of 5** runs per type, per trial:
- bad API key → `model_calls == 1`
- timeout → `model_calls == 2`
- network down → `model_calls == 2`

**Why exact counts, 5 of 5:** the retry decision is a fixed code path
(`FAILURE_KINDS` in `generate.py`, and `TRANSIENT_RETRIES = 2` in `config.py`),
not something that varies with the model. Any other count means the
classification or the retry loop is wrong.

**Why it matters:** retrying a bad key can never succeed. It only burns calls
against the 300-call session budget and makes the user wait for nothing.
Not retrying a timeout gives up on a failure that a second try often fixes.

## 4. The user gets the fallback message within 10 seconds (extension)

**Target:** In **5 of 5** runs per failure type, per trial, `duration_s` is
**≤ 10.0** seconds.

**Why 10 s:** a normal answered question averages 1.50 s (M3, 10 runs). In a
terminal, a command that's silent much past 10 s looks hung, and hanging is
exactly the failure the timeout was added to remove. If the fallback arrives
later than that, the user has likely already hit Ctrl+C.

**Why not stricter (e.g. 5 s):** the timeout and network paths include one
retry with a 1 s backoff, and in M3 the network-down run took 7.94 s. A 5 s
target would fail on retry behavior I want to keep (criterion 3).

**Known limit:** this is measured with the forced 0.05 s timeout. At the
default 30 s timeout, a real hang would take about 61 s (two 30 s attempts plus
backoff). This criterion doesn't test that.

## 5. Normal questions still work the same (regression)

**Target:** Run the 5 questions in `questions.py` twice each (10 runs, in one
process, the same procedure as the M3 cost baseline). All **10 of 10** end
with `status: "ok"`, a non-empty `answer` and at least one source, and the
average `duration_s` is **≤ 2.0** seconds. Also, all **5 of 5**
`OUT_OF_SCOPE` questions are still refused with `model_calls == 0`.

**Why 10 of 10:** these questions all answered before the extension, and the
hardening wraps every Gemini call. A normal question that now comes back as
`failed` means the hardening is catching things it shouldn't, which is a
regression.

**Why 2.0 s:** the M3 baseline is 1.50 s with this exact procedure, including
the slow first run in the process. A 0.5 s margin covers normal network
jitter. Anything beyond that means the extension added real overhead to the
happy path.

---

**Not covered by these criteria:** empty responses (`failure_kind: "empty"`).
I can only simulate those with a fake client, not trigger them for real, so
any result would be testing my fake rather than Gemini. Listed in What's Still
Broken.
