# The Unofficial Guide

Malakai — corpus: `campus_life`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This is a retrieval-augmented question-answering system built on `campus_life`,
a corpus of 88 short posts about student life at a university — dining halls,
dorms, course workloads, and the administrative rules nobody explains
properly. It answers specific questions like "how many mid-terms does MATH 220
have?" or "does the housing lottery ever sell out east lots?" by retrieving the
most relevant post, checking that it's actually close enough to be trustworthy,
and having a model write an answer grounded in that post — naming the source
file it came from. Questions clearly outside the corpus get refused instead of
answered with a guess.

## Chunking Strategy

**Chunk size:** 350 characters
**Overlap:** 0 characters

`campus_life`'s posts average about 317 characters — close enough to one
paragraph that a fixed 800-character window (the starter default) would have
swallowed several unrelated posts into a single chunk if documents were ever
concatenated, and more importantly gave no signal about where one post's
single thought actually ends. Reading the documents in Milestone 1, almost
every post is one self-contained answer to one implied question, so the goal
became keeping each post whole rather than cutting it by length at all.
350 was chosen so the large majority of posts fit as a single chunk unsplit;
the few that run longer (course workload posts with a paragraph plus a
follow-up detail, mostly) get split on paragraph breaks instead of mid-sentence,
so a boundary always falls between thoughts. Overlap is 0 because there's
nothing to preserve across a boundary when the split already lands between
paragraphs — overlap only matters when you're forced to cut mid-thought, and
this strategy is built to avoid that.

## Sample Chunks

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.

```

**Chunk 2** — source: `course_cs_210.txt#0` — produced by: `chunker.py::split_documents`

```
CS 210 Data Structures

I'm a junior and I've done this twice now. Format is lecture with weekly labs; slides go up after class, not before. Assessment: two midterms and a final, all drawn from lecture material rather than the textbook. Midterms are curved, the final is not.

Expect 8 to 10 hours a week outside class.
```

**Chunk 3** — source: `course_math_220_workload.txt#0` — produced by: `chunker.py::split_documents`

```
Workload for MATH 220 Linear Algebra

People keep asking so: 6 to 8 hours a week, almost all of it on problem sets. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 4** — source: `dining_the_ridgeway_cafe.txt#0` — produced by: `chunker.py::split_documents`

```
The Ridgeway Café

Second-year here. Wait times: 10 to 15 minutes at 12:30, none after 2:00. The thing worth going for is the only place on campus with real espresso. The thing to know is that seating is tight; about 40 seats for a building of 900.

Hours are 7:00am to 4:00pm weekdays only. Costs declining balance only, no meal swipes.
```

**Chunk 5** — source: `housing_innisfree_hall_laundry.txt#0` — produced by: `chunker.py::split_documents`

```
Laundry in Innisfree Hall

Machines take $1.75 wash, $1.75 dry, app-based. There are eight washers and six dryers for the building, which is the wrong ratio and means the dryers back up on Sunday evenings.

Best time to do laundry here is Tuesday or Wednesday morning. Sunday after 6pm you will wait.
```

## Sample Answer

**Question:** How many credit hours are required to graduate?

**Answer:**

```
To graduate, 120 credit hours are required.

Source: admin_graduation_requirements.txt

Sources retrieved: admin_graduation_requirements.txt, admin_pass_fail_option.txt, course_stat_150.txt, course_stat_150_workload.txt, money_jobs.txt
```

**My relevance cutoff:** 0.6 (the starter default)

Ran my five test questions and the five `OUT_OF_SCOPE` ones through
`app.py retrieve` and recorded the best distance for each. The two groups
didn't overlap at all: every in-corpus question's best match landed between
0.256 and 0.416, and every out-of-corpus question's best match landed between
0.823 and 0.934 — a gap from roughly 0.42 to 0.82 with nothing in it. 0.6 sits
in the middle of that gap, so it isn't a close call either way; I'd have
needed to move it by more than 0.2 in either direction before it started
misclassifying anything.

| Question | In corpus? | Best distance |
|---|---|---|
| How many credit hours are required to graduate? | yes | 0.289 |
| What is the last semester to declare a major | yes | 0.355 |
| How many mid-terms are there in math220 Linear Algebra? | yes | 0.404 |
| Do students receive free campus wifi? | yes | 0.416 |
| Does east parking lots ever sell out? | yes | 0.256 |
| What is the capital of Mongolia? | no | 0.825 |
| How do I change the oil in a diesel engine? | no | 0.934 |
| Who won the 1994 World Cup? | no | 0.823 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.837 |
| How do I write a for loop in Rust? | no | 0.891 |

## How I Used AI

**1.** I asked Claude to write `split_documents` given full context on the
project (the corpus, `config.py`, `ingest.py`). My own in-progress draft
packed words one at a time into a running buffer and merged trailing leftovers
back into the previous chunk by mutating `chunks[-1].text` directly, plus it
had a leftover `print(chunks)` debug line still in the loop. Claude rewrote
it to first check whether a whole document already fits under `CHUNK_SIZE`
(most `campus_life` posts do) and only fall back to paragraph-boundary
splitting for the longer ones, and removed the debug print and the mutation.

**2.** When I asked Claude to commit `chunker.py` and this README, it caught
that the sample chunk text I'd pasted into the README had gotten corrupted —
the em dashes had come out as literal replacement characters when copied from
a PowerShell terminal that wasn't rendering UTF-8. It regenerated the sample
text directly from Python (writing straight to a file instead of through the
terminal) to get the real characters back before committing.

**3.** In unit 2, I'd only sketched `scorer.py` — a `normalize()` that just
returned `None`, no `judge()` — so my own first read of criterion 1 (4/5, wifi
failing) was a manual judgment call with nothing to check it against. I asked
Claude to actually implement `judge()` and re-run the eval; the automated
score came out 4/5 with the same wifi miss, which is the only reason I trust
that number now instead of just my own read of the text.

**4.** For Milestone 3's diagnosis, I asked Claude to look across the three
"before" runs and work out whether criterion 1's wifi miss and criterion 5's
vague target were two problems or one. It traced both to the same mechanism
in `generate.py::GROUNDING_INSTRUCTION` — the model treating "included with
your account" as equivalent to "free" — instead of me writing two separate
patches for what turned out to be one root cause. That's the specific
pattern-spotting this unit asked for, and it's also why the fix I tried
targeted the prompt rather than retrieval or chunking.

**5.** After the fix didn't move any numbers, I asked Claude to diff the
before/after answers line by line rather than just re-reading the pass/fail
table. That's how we caught that the wifi answer came back byte-for-byte
identical, and that the one thing that did change (a hedge on the
declaring-a-major question) had just moved from run 3 to run 1 rather than
actually resolving anything — a distinction the criteria table alone doesn't
show.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunk overlap close to 0 (3 of 5 questions' source chunks sampled) | ~0 characters shared between neighboring chunks | 0 chars | 0 chars | 0 chars | MET |
| 5. Corpus mishandles "yes/no" questions that require inferring past what the source states | Same failure shows up on 4+ of 5 questions with this shape (of the 3 runs available) | mishandled | mishandled | mishandled | MET* |

*Run count note: `run_eval.py` defaults to 3 runs, matching criteria 1–3 above, not the 5 I wrote criterion 5's target against. Reported as 3/3 available trials rather than out of 5.

Row 1 is scored, not read by hand: `scorer.py::judge` checks that every keyword in `expects` (from `questions.py`) shows up in the answer. Produced by `run_eval.py::main` and `run_eval.py::check_out_of_scope` (`results/run_2026-09-23_1841_before.md`; an earlier unscored run from before `scorer.py` existed is `results/run_2026-09-23_1738.md`), except criterion 4, which isn't something that script measures — I got it by calling `chunker.py::split_documents` directly and reading `config.py`'s `CHUNK_OVERLAP = 0`.

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

**1. Retrieved chunk contains the answer** (`scorer.py::judge`, `run_eval.py::main`, `store.py::search`) — 4/5, same every run because retrieval is deterministic (same query, same index) and the answers came out identical in substance each time. The one miss is the wifi question:

> Q: "Do students receive free campus wifi?"
> Chunk (`admin_wifi_and_accounts.txt`): "Your student account gives you campus wifi, printing, and a cloud drive with unlimited storage..."
> Answer: "Yes, your student account gives you campus wifi."

The chunk never says "free" — the model infers it because wifi is bundled with the account. The other four chunks state their answers outright: `admin_graduation_requirements.txt` says "120 credit hours," `course_math_220_exams.txt` says "Two midterms," `admin_declaring_a_major.txt` says "at the end of your second semester," `admin_parking_permits.txt` says "The east lot never sells out."

**2. Every answer names a source** (`generate.py::answer_from_chunks`) — 5/5 every run. Example from run 1: "To graduate, 120 credit hours are required (admin_graduation_requirements.txt)."

**3. Gate stops out-of-corpus questions** (`run_eval.py::check_out_of_scope`, `gate.py::check`) — 5/5, refused all five (target was 4/5): "What is the capital of Mongolia?" → best distance 0.825, refused. Same for the other four.

**4. Chunk overlap close to 0** (`chunker.py::split_documents`) — I sampled the source chunks for 3 of the 5 questions: `admin_graduation_requirements.txt`, `admin_wifi_and_accounts.txt`, and `course_math_220.txt`. The first two are short enough to stay a single whole chunk each (no neighbor to overlap with). `course_math_220.txt` split into two:

```
chunk 0 (269 chars): "...Expect 6 to 8 hours a week, almost all of it on problem sets."
chunk 1 (112 chars): "The one piece of advice: the problem sets are the course..."
```

No characters repeat between them — consistent with `config.py`'s `CHUNK_OVERLAP = 0`.

**5. Corpus mishandles "yes/no" questions that require inferring past what the source states** — the wifi question is the clearest case: the source never says "free," but the answer said "Yes" with no hedge, in all 3 runs. The declaring-a-major question showed a milder version of the same thing — the source only implies there's no hard deadline ("no penalty for declaring late"), and the model's confidence in stating that varied: runs 1–2 answered directly, but run 3 added "The documents do not specify a final deadline or last semester to declare a major," which is a more honest read of the same chunk. So the corpus doesn't reliably flag when a question asks for something one inferential step beyond what's written.

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer — 4 of 5 | MET | `scorer.py::judge` scored 4/5 in all three runs, same miss every time: the wifi question's chunk says the account "gives you campus wifi" but never says "free," so the retrieved text doesn't actually contain what the question asked for. |
| 2 | Every answer names a source — 5 of 5 | MET | I read all 15 answers (5 questions × 3 runs) in `results/run_2026-09-23_1841_before.md` by hand; every one names a source file, no exceptions, no close calls. |
| 3 | Gate stops out-of-corpus questions — 4 of 5 | MET | `run_eval.py::check_out_of_scope` refused 5 of 5 `OUT_OF_SCOPE` questions — clears the 4-of-5 bar with room to spare, and it's one deterministic pass so there's nothing to average across runs. |
| 4 | Chunk overlap close to 0 (3 of 5 sampled) | MET | Sampled the chunks behind 3 of my 5 questions directly from `chunker.py::split_documents`; two never split, and the one that did (`course_math_220.txt`) shares 0 characters between its two pieces — matches `config.CHUNK_OVERLAP = 0` exactly, not just "close." |
| 5 | Same question type mishandled in ≥4 of 5 trials | MISSED — criterion is broken as written | `run_eval.py` produces 3 runs by default, not 5, so "4 of 5 trials" has no 5th trial to be 4 of. I also never named "the type of question" in advance, so any category I pick now (e.g. "questions needing an inference the source never states") is reverse-engineered from results I'd already seen, not a prediction I'm checking. See the revision in `criteria.md`. |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

Only one criterion missed: **#5**. Criteria 1–4 all cleared their targets, so
there's only one diagnosis to do, not a pipeline post-mortem across the board.

### #5 — not a pipeline failure, a criterion-writing failure

I'm not going to force this into "loading / chunking / embedding / retrieval /
generation" and pretend that's where it broke, because it didn't break there —
it broke before any of those stages ran a single query. The target said "4 of
the 5 trails," but `run_eval.py` runs 3 trials by default, so there was never
a 5th trial to be 4 of. And "the type of question the corpus handles badly"
was never named in advance — nothing in `questions.py` or `criteria.md` fixed
a category before I saw results, so any category I named after the fact would
be reverse-engineered from the answer I already had, not a prediction I was
testing. That's a measurement problem, not a system problem, which is why I
revised it in `criteria.md` instead of just re-running it.

### The mechanism underneath it, since it's real

The revision names a real, checkable behavior, so it's worth tracing where it
actually lives, even though it isn't what made criterion 5 a miss.

- **Loading / chunking:** ruled out. `admin_wifi_and_accounts.txt` is 283
  characters — under `CHUNK_SIZE=350` — so it became one whole chunk. Nothing
  was cut or separated.
- **Embedding / retrieval:** ruled out. The wifi question's best distance was
  0.416, well under the 0.6 gate, and `admin_wifi_and_accounts.txt` was in the
  top-5 every run. Retrieval found the right chunk every time.
- **Generation:** this is where it happens. `generate.py::GROUNDING_INSTRUCTION`
  tells the model "Use only the information in the documents... Do not guess,"
  but the chunk only says the account "gives you campus wifi" — it never says
  the word "free," and never states a price at all. The model answered "Yes"
  anyway, treating "included with the account" as equivalent to "free." The
  instruction bans guessing but never defines the line between *paraphrasing
  what's written* and *asserting something plausible that isn't written* —
  so the model gets to decide that line itself, and it decided generously.

### Pattern, not two separate problems

This is the same failure showing up twice, not two different ones. It's the
one question behind criterion 1's single miss (4/5, wifi) *and* the one behind
criterion 5's revision — same chunk, same generation call, same mechanism.
One root cause: the generation stage will affirm a reasonable-sounding
inference without flagging that it went past what the source states.

### Were my targets set low?

Partly. Criterion 3 cleared its target by a wide margin — 5/5 against a 4/5
bar, and the out-of-scope distances (0.823–0.934) sit far above the 0.6
cutoff, so there was never a close call to lose. That's a target I'd tighten:
instead of "4 of 5 refused," I'd measure the *margin* — e.g. "every refused
question's best distance is at least 0.1 above the cutoff" — since right now
the criterion can't tell a comfortable refusal from a borderline one.
Criterion 2 is similarly soft: `GROUNDING_INSTRUCTION` explicitly tells the
model to name its source on every answer, so "does it name a source" mostly
tests whether the model follows an instruction, not whether the source it
names is the *right* one. I'd tighten that to "the named source is the
document that actually contains the answer," which is a real correctness
check instead of a formatting one.

## The Improvement

**What I changed:** One rule added to `generate.py::GROUNDING_INSTRUCTION`:

```
- If the question asks for a specific detail (a price, a deadline, a count, a yes/no) and the documents
  imply it but never state it outright, say plainly that it isn't stated rather than asserting it as fact.
```

Nothing else changed — same chunks, same index, same top-k, same threshold. The
diff is one sentence in the system prompt.

**Why I picked it:** The diagnosis traced criterion 1's one miss and criterion
5's revision to the same mechanism, and it lives in generation, not retrieval:
`GROUNDING_INSTRUCTION` already banned "guessing" but never defined the line
between paraphrasing what a chunk says and asserting something the chunk only
implies. This targets that exact line — the same gap the diagnosis named,
not a new problem I noticed along the way.

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 4/5 | 4/5 | 4/5 | MET (unchanged) |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET (unchanged) |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET (unchanged) |
| 4. Chunk overlap close to 0 (3 of 5 sampled) | ~0 characters shared | 0 chars | 0 chars | 0 chars | MET (unchanged — this fix never touched chunking) |
| 5. Revised: wifi question answered without flagging the inference | mishandled in all 3 runs | mishandled | mishandled | mishandled | Confirmed, unchanged |

Produced by `run_eval.py::main` and `run_eval.py::check_out_of_scope`,
`results/run_2026-09-26_2245_after.md`, compared against the before run at
`results/run_2026-09-23_1841_before.md`.

**Before vs. after, the one question that mattered:**

```
Before — "Do students receive free campus wifi?" (all 3 runs identical):
  Yes, your student account gives you campus wifi.
  Source: admin_wifi_and_accounts.txt

After  — same question (all 3 runs identical):
  Yes, your student account gives you campus wifi. This is stated in `admin_wifi_and_accounts.txt`.
```

**Did it help?** No. Be plain about it: the exact answer the diagnosis was
about — the wifi question — came back unchanged in all 3 after-runs. It still
says "Yes" with no hedge on "free," still fails `scorer.py::judge` the same
way, and every one of the five criteria landed on the identical numbers as
the before run. Nothing moved.

The one thing that did shift is smaller than it looks: on the
declaring-a-major question, the hedged phrasing ("The documents do not state
a final semester...") now shows up in run 1 instead of run 3. That's not
progress — it's still 1 of 3 runs hedging, same inconsistency as before, just
relocated.

My best read of why: the model isn't treating "your account gives you wifi"
and "wifi is free" as two separate claims it needs separate evidence for —
it's filling the gap with background knowledge (campus wifi bundled with an
account is usually free) that the prompt's "don't use anything you know from
elsewhere" rule was already supposed to block. One more sentence competing
against that prior wasn't enough to override it. A next attempt would need to
either name the specific fact-type more concretely (e.g. call out cost/price
words specifically) or address this before generation — at retrieval or
gating — rather than asking the model to catch its own inference after the
fact.

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

**The wifi/"free" question itself is still broken.** Criterion 1 still sits
at exactly 4/5 because of it, and criterion 5's revision exists specifically
to keep tracking it: it's mishandled in all 3 after-runs, identically to the
3 before-runs. The one change I tried — tightening the grounding prompt — did
not touch this. What I'd try next, in order:

1. **A verification pass after generation, not another prompt tweak.** The
   diagnosis showed the model is filling the gap with outside knowledge
   ("account wifi is usually free") rather than something in the retrieved
   text, and a second sentence in the same prompt wasn't enough to override
   that. A cheap, checkable next step: after generation, check whether the
   specific fact-word the question is asking about (here, "free" or a price)
   actually appears in the retrieved chunk text, and if it doesn't, force a
   rewrite or append a caveat rather than trusting the model to self-police.
   That's a different pipeline stage than the one I already changed, so it's
   a genuinely separate experiment, not a variation on this one.
2. **Rewrite the source document itself** to state cost explicitly ("wifi is
   included at no extra cost") — the cheapest possible fix, but it only works
   because I happen to control this corpus, and it wouldn't teach the system
   anything about handling the next document like it.

I stopped after one change because that's what this milestone asked for — one
change, measured properly — not because there's nothing left to try. Trying a
second fix on top of the first, in the same run, would have made it
impossible to tell which change did what, which is the exact mistake the
milestone is built to prevent.

**Criterion 5 as revised is really a diagnostic, not a target with a pass
condition tied to improvement.** It confirms the weakness recurs, but it
doesn't currently reward fixing it — "mishandled in all 3 runs" and "fixed in
all 3 runs" would both just be different observations, not a met/missed bar.
I'd want a real next-unit version of it with an actual improvement target,
e.g. "0 of 3 runs mishandle the wifi question" — which, honestly, the system
fails right now (3 of 3).

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->

**Criterion 5**, clearly — already revised once this unit, and I'd go further
next time. I'd name the specific question or question-shape in advance
("questions where the source implies an answer but never states it outright")
rather than discovering the category by reading results, and I'd write the
target against the 3 runs `run_eval.py` actually produces instead of a nicer-
sounding "5 trials" I never checked against the tooling.

**Criterion 2**, next. "Names a source" turned out to test compliance with an
instruction (`GROUNDING_INSTRUCTION` already tells the model to cite one every
time) rather than anything about the system's actual behavior — it was never
at risk of failing. I'd write it as "the named source is the document that
actually contains the answer," which is a claim that could be false and would
have caught the wifi case too (it names the right file; it just overclaims
what that file says).

**Criterion 1**, more subtly. "The retrieved chunks include one that contains
the answer" sounds precise but I was the one interpreting "contains" for four
of five questions, and it took the wifi case actually failing to notice that
"contains" and "supports a reasonable inference of" are different claims. I'd
write it next time as "the exact fact the question asks about appears as
text in the chunk, not just something a reasonable person could conclude from
it" — spelling out the distinction before a real answer forces me to invent
it under pressure.

---

## Capstone

**System**

The Unofficial Guide: a RAG system over the `campus_life` corpus that chunks, retrieves, gates on relevance, and answers with Gemini (`app.py ask`, `serve.py`).

**Shape**

B: Harden against failure.

**The Shape**

I'm hardening the one place this system talks to the outside world: the Gemini call in `generate.py`. Right now three things go wrong there. The call has no timeout, so a slow or dead network hangs the run forever. Any error that isn't a 429 (a 500/503, a bad key, the network dropping) is raised immediately with no retry and kills the run. And when Gemini returns empty text (for example a safety block), `""` goes back to the user as the "answer". After the extension, every `ask` either returns a real answer or returns a clear, specific fallback message saying what went wrong. A failure in generation never crashes the run, hangs, or shows a blank answer, and every one of those outcomes, good or bad, leaves a structured log entry.

**Out of scope**

- **Input validation.** I'm not adding checks for empty, whitespace-only, or very long questions before retrieval. That's a different stage (before `search`) and a separate piece of work.
- **Retrieval and index failures.** If `chroma_db` is missing or corrupt, `store.search` still raises the way it does now. I'm not touching chunking, the embedder, or the store.
- **Answer correctness.** The wifi/"free" grounding problem from What's Still Broken stays broken. That's the model asserting facts the chunks don't state, not a crash, and fixing it means a verification pass, not error handling.

**Instrumentation**

Every question that goes through `app.py::ask_pipeline` (the command line and `serve.py` both use it) appends one JSON object to [`logs/runs.jsonl`](logs/runs.jsonl). The logger is [`runlog.py`](runlog.py). The record is written in a `finally` block, so a run that crashes still leaves a line. `python runlog.py` prints the last 10 as a table; `python runlog.py --stats` averages them.

Fields: `run_id`, `timestamp` (UTC), `entrypoint` (cli/http), `question`, `corpus`, `model`, `status` (`ok` / `refused` / `failed` = handled generation failure / `error` = crash), `answer`, `failure_kind` (timeout, network, server, rate_limit, auth, client, empty, unknown, crash), `failure_detail` (the raw exception), `best_distance`, `threshold`, `chunks_retrieved`, `sources`, `model_calls` (includes retries), `cache_hit`, `tokens_in`, `tokens_out` (read off Gemini's `usage_metadata`), `retrieval_s`, `generation_s`, `duration_s`, `timeout_s`.

The 10 measured runs (the 5 questions in `questions.py`, twice each, `AI201_CACHE=0` so every one is a real call):

```json
{"run_id": "dbbfe90a", "timestamp": "2026-11-11T23:45:14+00:00", "entrypoint": "cli", "question": "How many credit hours are required to graduate?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "To graduate, 120 credit hours are required. \n\nSource: admin_graduation_requirements.txt", "failure_kind": null, "failure_detail": null, "best_distance": 0.2886, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_graduation_requirements.txt", "admin_pass_fail_option.txt", "course_stat_150.txt", "course_stat_150_workload.txt", "money_jobs.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 577, "tokens_out": 23, "retrieval_s": 1.015, "generation_s": 4.312, "duration_s": 8.762, "timeout_s": 30.0}
{"run_id": "e66f60c7", "timestamp": "2026-11-11T23:45:23+00:00", "entrypoint": "cli", "question": "What is the last semester to declare a major", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "You can declare at the end of your second semester, or later if you need to; the documents do not state a final deadline or last semester to declare. \n\nSource: admin_declaring_a_major.txt", "failure_kind": null, "failure_detail": null, "best_distance": 0.3553, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_add_drop_deadline.txt", "admin_declaring_a_major.txt", "admin_graduation_requirements.txt", "admin_pass_fail_option.txt", "admin_study_abroad.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 534, "tokens_out": 46, "retrieval_s": 0.053, "generation_s": 0.537, "duration_s": 0.59, "timeout_s": 30.0}
{"run_id": "9c312294", "timestamp": "2026-11-11T23:45:23+00:00", "entrypoint": "cli", "question": "How many mid-terms are there in math220 Linear Algebra?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "There are two midterms in MATH 220 Linear Algebra, according to `course_math_220.txt` and `course_math_220_exams.txt`.", "failure_kind": null, "failure_detail": null, "best_distance": 0.4045, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["course_cs_210_exams.txt", "course_cs_340_exams.txt", "course_math_220.txt", "course_math_220_exams.txt", "course_math_220_workload.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 549, "tokens_out": 41, "retrieval_s": 0.046, "generation_s": 0.452, "duration_s": 0.497, "timeout_s": 30.0}
{"run_id": "38fc317f", "timestamp": "2026-11-11T23:45:24+00:00", "entrypoint": "cli", "question": "Do students receive free campus wifi?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "Yes, your student account gives you campus wifi. This information comes from `admin_wifi_and_accounts.txt`.", "failure_kind": null, "failure_detail": null, "best_distance": 0.4162, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_campus_jobs_and_financial_aid.txt", "admin_printing_quota.txt", "admin_wifi_and_accounts.txt", "money_textbooks.txt", "transit_shuttle.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 466, "tokens_out": 25, "retrieval_s": 0.049, "generation_s": 0.489, "duration_s": 0.538, "timeout_s": 30.0}
{"run_id": "cc8f0691", "timestamp": "2026-11-11T23:45:24+00:00", "entrypoint": "cli", "question": "Does east parking lots ever sell out?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "No, the east lot never sells out because it is a 12-minute walk. \n\nSource: admin_parking_permits.txt", "failure_kind": null, "failure_detail": null, "best_distance": 0.2558, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "dining_halden_hall.txt", "dining_the_atrium.txt", "housing_aldridge_hall_laundry.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 566, "tokens_out": 31, "retrieval_s": 0.044, "generation_s": 0.441, "duration_s": 0.485, "timeout_s": 30.0}
{"run_id": "b35c0c40", "timestamp": "2026-11-11T23:45:25+00:00", "entrypoint": "cli", "question": "How many credit hours are required to graduate?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "120 credit hours are required to graduate, as stated in admin_graduation_requirements.txt.", "failure_kind": null, "failure_detail": null, "best_distance": 0.2886, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_graduation_requirements.txt", "admin_pass_fail_option.txt", "course_stat_150.txt", "course_stat_150_workload.txt", "money_jobs.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 577, "tokens_out": 21, "retrieval_s": 0.049, "generation_s": 0.524, "duration_s": 0.573, "timeout_s": 30.0}
{"run_id": "403cb0c1", "timestamp": "2026-11-11T23:45:25+00:00", "entrypoint": "cli", "question": "What is the last semester to declare a major", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "Based on the documents provided, you declare at the end of your second semester, or later if you need to; a specific \"last semester\" is not stated. \n\nSource: admin_declaring_a_major.txt", "failure_kind": null, "failure_detail": null, "best_distance": 0.3553, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_add_drop_deadline.txt", "admin_declaring_a_major.txt", "admin_graduation_requirements.txt", "admin_pass_fail_option.txt", "admin_study_abroad.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 534, "tokens_out": 47, "retrieval_s": 0.044, "generation_s": 0.533, "duration_s": 0.577, "timeout_s": 30.0}
{"run_id": "394aa643", "timestamp": "2026-11-11T23:45:26+00:00", "entrypoint": "cli", "question": "How many mid-terms are there in math220 Linear Algebra?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "There are two midterms in MATH 220 Linear Algebra. This information comes from `course_math_220.txt` and `course_math_220_exams.txt`.", "failure_kind": null, "failure_detail": null, "best_distance": 0.4045, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["course_cs_210_exams.txt", "course_cs_340_exams.txt", "course_math_220.txt", "course_math_220_exams.txt", "course_math_220_workload.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 549, "tokens_out": 43, "retrieval_s": 0.048, "generation_s": 0.459, "duration_s": 0.507, "timeout_s": 30.0}
{"run_id": "de9557ec", "timestamp": "2026-11-11T23:45:26+00:00", "entrypoint": "cli", "question": "Do students receive free campus wifi?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "Yes, your student account gives you campus wifi. \n\nSource: `admin_wifi_and_accounts.txt`", "failure_kind": null, "failure_detail": null, "best_distance": 0.4162, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_campus_jobs_and_financial_aid.txt", "admin_printing_quota.txt", "admin_wifi_and_accounts.txt", "money_textbooks.txt", "transit_shuttle.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 466, "tokens_out": 25, "retrieval_s": 0.056, "generation_s": 0.494, "duration_s": 0.55, "timeout_s": 30.0}
{"run_id": "de86a01d", "timestamp": "2026-11-11T23:45:27+00:00", "entrypoint": "cli", "question": "Does east parking lots ever sell out?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "No, the east lot never sells out because it is a 12-minute walk. \n\nSource: admin_parking_permits.txt", "failure_kind": null, "failure_detail": null, "best_distance": 0.2558, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "dining_halden_hall.txt", "dining_the_atrium.txt", "housing_aldridge_hall_laundry.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 566, "tokens_out": 31, "retrieval_s": 0.055, "generation_s": 1.84, "duration_s": 1.895, "timeout_s": 30.0}
```

Failed and refused runs, each triggered on purpose:

- **Timeout trigger, misclassified (before the fix).** `AI201_TIMEOUT_S=0.05`, but Gemini's 400 *"Minimum allowed deadline is 10s"* came back before our own timeout fired, so it was logged as `client`. This log line is how I found the bug fixed in `949f879`.

```json
{"run_id": "60f5caa1", "timestamp": "2026-11-11T23:45:32+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "The answer service refused this request, so there's no answer to show.", "failure_kind": "client", "failure_detail": "ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Manually set deadline 1s is too short. Minimum allowed deadline is 10s.', 'status': 'INVALID_ARGUMENT'}}", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.746, "generation_s": 4.076, "duration_s": 4.822, "timeout_s": 0.05}
```

- **Timeout, after the fix.** Same trigger, now logged as `timeout`. 2 model calls = first attempt + 1 retry, then the fallback message.

```json
{"run_id": "820c4ed9", "timestamp": "2026-11-11T23:46:47+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "The answer service took too long to respond, so there's no answer this time. Your question was fine; try again in a moment.", "failure_kind": "timeout", "failure_detail": "ReadTimeout: The read operation timed out", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 1.213, "generation_s": 4.795, "duration_s": 6.008, "timeout_s": 0.05}
```

- **Bad API key.** `GEMINI_API_KEY=not-a-real-key`. `auth`, 1 model call: not retried, because retrying a bad key can't help.

```json
{"run_id": "fdb9e0ae", "timestamp": "2026-11-11T23:45:39+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "The answer service rejected the API key, so no answer can be generated. Check GEMINI_API_KEY in .env.", "failure_kind": "auth", "failure_detail": "ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.596, "generation_s": 2.408, "duration_s": 3.004, "timeout_s": 30.0}
```

- **Network down.** `HTTPS_PROXY=http://127.0.0.1:9`. `network`, 2 model calls (retried once).

```json
{"run_id": "de5b0aca", "timestamp": "2026-11-11T23:45:45+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "Couldn't reach the answer service. Check your internet connection and try again.", "failure_kind": "network", "failure_detail": "ConnectError: [WinError 10061] No connection could be made because the target machine actively refused it", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.599, "generation_s": 7.338, "duration_s": 7.938, "timeout_s": 30.0}
```

- **Crash outside generation (out of scope, but still logged).** Index folder moved away. `status: error`. The `finally` block wrote the record even though the run died.

```json
{"run_id": "1f1925c1", "timestamp": "2026-11-11T23:39:59+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "error", "answer": null, "failure_kind": "crash", "failure_detail": "RuntimeError: No index called 'campus_life__default'. Run `python app.py index` first.", "best_distance": null, "threshold": null, "chunks_retrieved": null, "sources": [], "model_calls": 0, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": null, "generation_s": null, "duration_s": 0.578, "timeout_s": 30.0}
```

- **Refused input.** Off-topic question; the relevance gate refused it and Gemini was never called (0 model calls, 0 tokens).

```json
{"run_id": "2396318a", "timestamp": "2026-11-11T23:45:55+00:00", "entrypoint": "cli", "question": "Who won the 1994 World Cup?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "refused", "answer": "I don't have enough information about that.", "failure_kind": null, "failure_detail": null, "best_distance": 0.823, "threshold": 0.6, "chunks_retrieved": 5, "sources": [], "model_calls": 0, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.593, "generation_s": null, "duration_s": 0.593, "timeout_s": 30.0}
```


**What It Costs**

**Measured: 538.4 input tokens + 33.3 output tokens per answered question, and 1.50 s wall-clock** (average of the 10 runs above, `dbbfe90a` → `de86a01d`).

How I measured it: each log record's `tokens_in` / `tokens_out` is the difference in `generate.token_counts()` before and after the run. Those counts are read off the `usage_metadata` Gemini sends back with each response, not estimated from the prompt length. Duration is `time.perf_counter()` around the whole of `ask_pipeline`. I averaged exactly those 10 rows (the log's other `ok` rows are smoke tests). To reproduce it:

```bash
python runlog.py --stats dbbfe90a e66f60c7 9c312294 38fc317f cc8f0691 b35c0c40 403cb0c1 394aa643 de9557ec de86a01d
```

| | avg | min | max |
|---|---|---|---|
| tokens_in | 538.4 | 466 | 577 |
| tokens_out | 33.3 | 21 | 47 |
| duration_s | 1.497 | 0.485 | 8.762 |
| retrieval_s | 0.146 | 0.044 | 1.015 |
| generation_s | 1.008 | 0.441 | 4.312 |

The 8.76 s max is the first run in the process (it loads the embedding model and opens Chroma). Every run after that was under 2 s.

**In dollars:** I'm on the Gemini free tier, so the **actual spend was $0.00**. At paid-tier prices of $0.30 / 1M input and $2.50 / 1M output tokens (third-party listings for `gemini-3.5-flash-lite`, not yet checked against Google's own pricing page):

```
538.4 × $0.30 / 1,000,000 = $0.000162
 33.3 × $2.50 / 1,000,000 = $0.000083
                            ---------
                            $0.000245 per answered question
```

A refused question costs $0 in API calls (0 tokens) and about 0.6 s. A failed one costs 0 tokens but up to 2 calls' worth of waiting.

**For 100 people a day**, assuming each person asks 5 questions and every one is answered (the worst case, since refusals and failures cost $0):

```
100 people × 5 questions          = 500 answered questions / day
500 × $0.000245                   = $0.12 / day
$0.12 × 30 days                   = $3.68 / month
tokens: 500 × (538.4 + 33.3)      = 285,850 tokens / day
```

So running this for a hundred people a day would cost about **12 cents a day (≈ $3.68 a month)** at paid-tier prices. Money isn't the real limit here; the free tier's request quotas and the 30-requests-per-minute pacing in `config.py` would hit first.

**Run Log**

Criteria: [`capstone_criteria.md`](capstone_criteria.md), committed in `2dba265` before any of these results. The runner is [`capstone_eval.py`](capstone_eval.py) (committed in `2c062d1`, also before results). Each trial is `python capstone_eval.py N`. Nothing was changed between the three trials. Raw output is in `results/capstone_trial_{1,2,3}.txt` and `.json`. Every log line below was written to `logs/runs.jsonl` by `runlog.py::write()`, called from the `finally` block in `app.py::ask_pipeline`. The scores were computed by `capstone_eval.py::score()`.

A criterion is MET only if all 3 trials hit the target.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Each triggered failure is named correctly (timeout / auth / network) | ≥ 4 of 5 per type | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | MET |
| 2. No triggered failure crashes the run | 0 of 15 crash | 0/15 | 0/15 | 0/15 | MET |
| 3. Transient failures retried once, permanent ones not (timeout / auth / network) | 5 of 5 per type | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | MET |
| 4. Fallback message within 10 s (timeout / auth / network) | 5 of 5 per type | 5/5 / 5/5 / 3/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 4/5 | **MISSED** |
| 5. Normal questions still work | 10/10 ok, avg ≤ 2.0 s, 5/5 refused | 10/10 ok, avg 1.216s, 5/5 refused | 10/10 ok, avg 1.286s, 5/5 refused | 10/10 ok, avg 1.362s, 5/5 refused | MET |

These were real reruns, not cached repeats: all 90 `run_id`s across the three trials are unique, every run had `AI201_CACHE=0`, and the model's wording changes between trials. For example, the wifi answer was 23, 25 and 25 output tokens, with a different source citation format each time.


*Criterion 1 (real output, run 1).* One log line per failure type, each with the expected `status: "failed"` and matching `failure_kind`:

```json
{"run_id": "0fd59a06", "timestamp": "2026-11-12T00:06:01+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "The answer service took too long to respond, so there's no answer this time. Your question was fine; try again in a moment.", "failure_kind": "timeout", "failure_detail": "ReadTimeout: The read operation timed out", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 1.354, "generation_s": 5.022, "duration_s": 6.376, "timeout_s": 0.05}
{"run_id": "434ffa2b", "timestamp": "2026-11-12T00:06:50+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "The answer service rejected the API key, so no answer can be generated. Check GEMINI_API_KEY in .env.", "failure_kind": "auth", "failure_detail": "ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.89, "generation_s": 2.594, "duration_s": 3.484, "timeout_s": 30.0}
{"run_id": "7eddd77b", "timestamp": "2026-11-12T00:07:53+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "Couldn't reach the answer service. Check your internet connection and try again.", "failure_kind": "network", "failure_detail": "ConnectError: [WinError 10061] No connection could be made because the target machine actively refused it", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.769, "generation_s": 8.733, "duration_s": 9.502, "timeout_s": 30.0}
```

*Criterion 2 (real output, run 1).* Exit code and the last lines the user saw, captured by `capstone_eval.py::run_triggered()`. No traceback in any of the 15:

```
[timeout] exit_code=0 traceback=False
    2 model calls this session
      [timeout] call failed. Retrying in 1s (attempt 1 of 2).
[auth] exit_code=0 traceback=False
    [no answer: auth] The answer service rejected the API key, so no answer can be generated. Check GEMINI_API_KEY in .env.
    1 model calls this session
[network] exit_code=0 traceback=False
    2 model calls this session
      [network] call failed. Retrying in 1s (attempt 1 of 2).
```

*Criterion 3 (real output, run 1).* `model_calls` for all 15 triggered runs:

```
0fd59a06  timeout  model_calls=2
ea081a03  timeout  model_calls=2
d76d7110  timeout  model_calls=2
b06397cb  timeout  model_calls=2
7b8abd6a  timeout  model_calls=2
434ffa2b  auth     model_calls=1
dbe8c4f2  auth     model_calls=1
b2ef241b  auth     model_calls=1
cd545304  auth     model_calls=1
bef6022a  auth     model_calls=1
7eddd77b  network  model_calls=2
2bae097b  network  model_calls=2
6693350c  network  model_calls=2
80cf2078  network  model_calls=2
7041d2d7  network  model_calls=2
```

*Criterion 4 (real output, run 1, the one that missed).* All 5 network-down log lines. `2bae097b` (13.813 s) and `6693350c` (11.06 s) are over the 10 s target:

```json
{"run_id": "7eddd77b", "timestamp": "2026-11-12T00:07:53+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "Couldn't reach the answer service. Check your internet connection and try again.", "failure_kind": "network", "failure_detail": "ConnectError: [WinError 10061] No connection could be made because the target machine actively refused it", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.769, "generation_s": 8.733, "duration_s": 9.502, "timeout_s": 30.0}
{"run_id": "2bae097b", "timestamp": "2026-11-12T00:08:09+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "Couldn't reach the answer service. Check your internet connection and try again.", "failure_kind": "network", "failure_detail": "ConnectError: [WinError 10061] No connection could be made because the target machine actively refused it", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 2.124, "generation_s": 11.69, "duration_s": 13.813, "timeout_s": 30.0}
{"run_id": "6693350c", "timestamp": "2026-11-12T00:08:29+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "Couldn't reach the answer service. Check your internet connection and try again.", "failure_kind": "network", "failure_detail": "ConnectError: [WinError 10061] No connection could be made because the target machine actively refused it", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.966, "generation_s": 10.094, "duration_s": 11.06, "timeout_s": 30.0}
{"run_id": "80cf2078", "timestamp": "2026-11-12T00:08:45+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "Couldn't reach the answer service. Check your internet connection and try again.", "failure_kind": "network", "failure_detail": "ConnectError: [WinError 10061] No connection could be made because the target machine actively refused it", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.721, "generation_s": 8.652, "duration_s": 9.373, "timeout_s": 30.0}
{"run_id": "7041d2d7", "timestamp": "2026-11-12T00:08:59+00:00", "entrypoint": "cli", "question": "how does the housing lottery work?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "failed", "answer": "Couldn't reach the answer service. Check your internet connection and try again.", "failure_kind": "network", "failure_detail": "ConnectError: [WinError 10061] No connection could be made because the target machine actively refused it", "best_distance": 0.1454, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_housing_lottery.txt", "admin_parking_permits.txt", "advising_registration.txt", "housing_morrow_house.txt"], "model_calls": 2, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.655, "generation_s": 8.471, "duration_s": 9.126, "timeout_s": 30.0}
```

Network-down `duration_s` across all three trials: run 1: 9.502, 13.813, 11.06, 9.373, 9.126 · run 2: 9.34, 8.652, 8.063, 8.034, 8.234 · run 3: 11.652, 8.993, 8.04, 8.079, 7.954. Timeout and bad-key runs were all ≤ 9.353 s.


*Criterion 5 (real output, run 1).* The first in-scope run (which includes loading the embedding model, hence 6 s) and an out-of-scope refusal:

```json
{"run_id": "a82b1aa0", "timestamp": "2026-11-12T00:09:12+00:00", "entrypoint": "cli", "question": "How many credit hours are required to graduate?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "ok", "answer": "120 credit hours are required to graduate, as stated in admin_graduation_requirements.txt.", "failure_kind": null, "failure_detail": null, "best_distance": 0.2886, "threshold": 0.6, "chunks_retrieved": 5, "sources": ["admin_graduation_requirements.txt", "admin_pass_fail_option.txt", "course_stat_150.txt", "course_stat_150_workload.txt", "money_jobs.txt"], "model_calls": 1, "cache_hit": false, "tokens_in": 577, "tokens_out": 21, "retrieval_s": 0.662, "generation_s": 3.481, "duration_s": 5.999, "timeout_s": 30.0}
{"run_id": "015eae99", "timestamp": "2026-11-12T00:09:24+00:00", "entrypoint": "cli", "question": "What is the capital of Mongolia?", "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "status": "refused", "answer": "I don't have enough information about that.", "failure_kind": null, "failure_detail": null, "best_distance": 0.8246, "threshold": 0.6, "chunks_retrieved": 5, "sources": [], "model_calls": 0, "cache_hit": false, "tokens_in": 0, "tokens_out": 0, "retrieval_s": 0.127, "generation_s": null, "duration_s": 0.127, "timeout_s": 30.0}
```

In-scope `duration_s` for run 1: 5.999, 0.833, 0.724, 0.618, 0.521, 0.809, 0.716, 0.682, 0.541, 0.72 → average 1.216 s.

**Verdicts**

| # | Criterion | Target | Verdict |
|---|---|---|---|
| 1 | Failure named correctly (t/a/n) | ≥ 4 of 5 per type | MET |
| 2 | No crashes | 0 of 15 | MET |
| 3 | Retry counts (t/a/n) | 5 of 5 per type | MET |
| 4 | Fallback ≤ 10 s (t/a/n) | 5 of 5 per type | **MISSED** |
| 5 | Normal path (ok, avg, refused) | 10/10 ok, avg ≤ 2.0 s, 5/5 refused | MET |

- **1: MET.** 15/15 named correctly in every trial, beating the 4-of-5 allowance. The timeout race found in M3 didn't come back after the `X-Server-Timeout` fix.
- **2: MET.** 0 crashes in 45 triggered runs: every one exited 0 with `status: "failed"` and no traceback.
- **3: MET.** Exact `model_calls` in 45/45 runs.
- **4: MISSED.** Network-down runs: 3/5, 5/5, 4/5 within 10 s. Timeout and bad-key runs were 5/5 in all three trials. The target has to hold in every trial, and it didn't.
- **5: MET.** 10/10 answered each trial (averages 1.216, 1.286, 1.362 s, against the 1.50 s M3 baseline), 5/5 off-topic refused with 0 model calls.

**Diagnosis**

**Criterion 4.** The stage is **generation** (`generate.py::generate` → `_get_client` and the retry loop), not retrieval. Across trial 1's five network-down runs, `retrieval_s` was 0.66–2.12 s but `generation_s` was 8.5–11.7 s.

The mechanism is that generation time in a failure was mostly *fixed* costs that have nothing to do with the failure, and my criterion assumed it was the retry policy. I timed each piece in a fresh process (3 runs each, very consistent):

| Piece of a network-down run | Seconds | Why |
|---|---|---|
| Retrieval (embedder + Chroma, cold) | 1.6–1.8 | one-time per process |
| `import google.genai` | 2.57–2.63 | done lazily inside the *first* Gemini call, after retrieval |
| `genai.Client()` | 0.91–1.00 | same |
| attempt 1 → `ConnectError` | 2.04 | Windows retries a refused TCP connect before giving up. A raw `socket.connect` to the dead port takes 2.04 s every time; on Linux it's near-instant |
| backoff | 1.00 | `2 ** 0` |
| attempt 2 → `ConnectError` | 2.04 | same |
| **total** | **≈ 10.2–10.7** | |

So a network-down run normally landed right on the 10 s line, and normal disk and CPU jitter decided which side. When I wrote the target, I reasoned from "2 attempts + 1 s backoff" and never counted the 3.5 s SDK cold start or Windows' 2 s connection refusal.

**The pattern** is one problem with three symptoms, not just a network problem. All three failure types pay the same 3.5 s SDK cold start inside `generation_s`. That's why bad-key runs, which make one fast HTTP round trip, still took up to 9.35 s, and timeout runs up to 9.1 s. Network runs crossed the line first only because they also add 2 × 2.04 s of refused connects.

I didn't touch the retry policy (2 attempts for network). Criterion 3 depends on it, and a dropped connection is the case a retry exists for.

**The Improvement**

One change (`d4a6741`): `generate.prewarm()` starts importing the SDK and building the client in a background thread at the top of `ask_pipeline`, so the 3.5 s cold start overlaps with retrieval instead of following it. `_get_client()` joins that thread rather than building a second client. No retry, timeout or classification logic changed. Then I re-ran all 5 criteria × 3 trials with the same runner (`python capstone_eval.py after_N`).

**Before vs after** (t/a/n = timeout / auth / network):

| Criterion | Before 1 | Before 2 | Before 3 | Before | After 1 | After 2 | After 3 | After |
|---|---|---|---|---|---|---|---|---|
| 1. Failure named correctly (t/a/n) | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | MET | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | MET |
| 2. No crashes | 0/15 | 0/15 | 0/15 | MET | 0/15 | 0/15 | 0/15 | MET |
| 3. Retry counts (t/a/n) | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | MET | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | MET |
| 4. Fallback ≤ 10 s (t/a/n) | 5/5 / 5/5 / 3/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 4/5 | **MISSED** | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 5/5 | 5/5 / 5/5 / 3/5 | **MISSED** |
| 5. Normal path (ok, avg, refused) | 10/10, 1.216s, 5/5 | 10/10, 1.286s, 5/5 | 10/10, 1.362s, 5/5 | MET | 10/10, 1.279s, 5/5 | 10/10, 1.429s, 5/5 | 10/10, 1.246s, 5/5 | MET |

`duration_s` of triggered runs, all 15 per type across the three trials:

| Failure | Before median | Before max | After median | After max |
|---|---|---|---|---|
| timeout | 4.862 s | 9.1 s | 4.321 s | 4.678 s |
| auth | 3.406 s | 9.353 s | 3.174 s | 3.457 s |
| network | 8.993 s | 13.813 s | 8.129 s | 12.628 s |

**Did it help? Partly, and criterion 4 is still MISSED** (after: 5/5, 5/5, 3/5 for network).

- **It helped the timeout and bad-key paths a lot.** Worst case went from 9.1 → 4.7 s and 9.35 → 3.5 s, so they're now far from the line instead of close to it.
- **It helped network a little:** median 8.993 → 8.129 s. 2 of 3 trials now hit 5/5 (before: 1 of 3).
- **Why only a little:** the overlap is partial. Importing the SDK and loading the embedder both mostly run Python code, so the two threads take turns on the GIL instead of running in parallel. Network `generation_s` dropped from ~7.3–8.7 s to ~6.8–7.5 s, but `retrieval_s` rose from ~0.7 s to ~0.9–1.2 s.
- **What missed after the fix:** two runs in after-trial 3, `1bdad081` (10.769 s) and `8b582184` (12.628 s). In both, retrieval *and* generation were slow at the same time (retrieval 2.926 / 3.34 s versus the usual ~1 s), which looks like the machine being briefly busy rather than one stage. The remaining floor is ≈ 7 s of generation: 2 × 2.04 s refused connects, 1 s backoff and ≈ 1.9 s of cold start the overlap didn't hide. That leaves about 2 s of headroom, and a busy moment uses it up.
- **The trade-off:** the next obvious fix is to stop retrying a refused connection, which would save ≈ 3 s. That would break criterion 3, which requires network failures to be retried once. I'd rather miss 4 by a couple of seconds now and then than give up a retry that helps real dropped connections.
- **Normal path:** still 10/10 in every trial (averages 1.279, 1.429, 1.246 s), so the fix didn't cost anything there.

**What's Still Broken**

- **Criterion 4 (MISSED): network-down fallback can still take more than 10 s.** What I'd do: give `generate()` one total deadline for the whole call, including retries (for example 8 s), instead of a timeout per attempt. When the deadline is close, it would skip the second attempt and return the fallback right away. That keeps the retry when there's time for it (criterion 3) and caps the wait (criterion 4). Why I stopped: M6 allows one fix, and I spent it on the SDK cold start because that was the cost all three failure types shared. Stopping retries on a refused connection would have been simpler, but it breaks criterion 3, and I didn't want to trade one miss for another.
- **The miss is partly a Windows effect.** A refused connection takes 2.04 s on this machine because Windows retries it before giving up. My network trigger (a dead local proxy) measures that behavior, not a real outage. I haven't measured it on Linux or macOS, where the same run would likely pass.
- **A real hang at the default timeout is slow, and untested.** All my timeout runs forced `AI201_TIMEOUT_S=0.05`. At the default 30 s, a truly hung call would take about 61 s (2 × 30 s plus the backoff) before the user sees anything. The criteria never tested this, and the total-deadline fix above would cover it.
- **Empty responses are only tested with a fake client.** `failure_kind: "empty"` works against a fake that returns no text, but I couldn't make Gemini return a real empty response on demand, so no criterion covers it.
- **Criteria set too low.** Criterion 3 is close to guaranteed: it checks a fixed code path, so it was always going to be 45/45. Criterion 1's "4 of 5" allowance was never needed (45/45 named correctly once the M3 timeout race was fixed). I'd tighten criterion 1 to **5 of 5 per type**. I'd replace criterion 3 with one that can actually fail: **a real hang at the default 30 s timeout returns the fallback within 35 s, 5 of 5.**
- **Still out of scope, unchanged:** input validation before retrieval, crashes when the index is missing (still `status: "error"`, though now logged), and the wifi/"free" grounding problem from the earlier unit.

**What I'd Do Next**

I'd replace the per-attempt timeout with a single deadline for the whole Gemini call, retries included. It's the one change that fixes the criterion 4 miss and the untested 61-second hang together, without giving up the retry that criterion 3 protects.

**How I Used AI (Capstone)**

I worked with Claude (Claude Code, in VS Code) throughout the capstone. I made the project decisions: which system to extend, Shape B, the 4-of-5 target in criterion 1, and keeping criterion 3's retry policy instead of trading it away to pass criterion 4. I reviewed each milestone before moving on. Claude wrote most of the code and the first drafts of the write-ups, and it did the measurement and diagnosis work, which I checked against the logs.

In more detail:

- **M1:** I chose this project and Shape B. Claude read the code, listed the real failure gaps (no timeout, non-429 errors not retried, empty responses shown as blank), and wrote the Shape and Out of scope text, which I reviewed. It then did the brief's scope count and told me the plan held about 3–4 pieces. I kept them together as one hardening layer around the Gemini call rather than cutting.
- **M2–M3:** Claude wrote the hardening code (`generate.py`, `app.py`, `serve.py`), the logger (`runlog.py`), and the capstone section of `RUNNING.md`. It also ran the fresh-clone test and the 10 cost runs. The per-token price came from a web search of third-party listings, not Google's page, and the README says so.
- **M4:** the criteria were drafted by Claude at my instructor's direction (noted at the top of `capstone_criteria.md`). The "at least 4 of 5" target in criterion 1 is mine. Claude first refused to write them, because the brief says to write them unaided, and only drafted them after I explained my instructor's exception.
- **M5–M6:** Claude wrote the test runner, ran all six trials, measured each piece of the network-down time, and made the one fix. I decided to keep criterion 3's retry policy rather than trade it away for criterion 4.

Where the AI was wrong, and how it got caught:
- **Its first diagnosis guess was wrong.** It guessed the Gemini SDK was quietly retrying connection errors on its own. Reading the SDK source (`retry_options` defaults to `None`, meaning one attempt) and timing each piece showed the real cause: the 3.5 s cold start plus Windows' 2 s connection refusal.
- **It wrote a claim it couldn't back.** It wrote "the averaging script is in the commit history" when it wasn't. It caught this itself and replaced it with a command anyone can re-run (`python runlog.py --stats <ids>`).
- **It moved my vector index by mistake.** While testing the "missing index" crash, it renamed `chroma_db`, Chroma created a new empty one, and moving the folder back put the real index inside it. It noticed and restored it. The index is rebuildable, so nothing was lost, but I'd now back up rather than rename.
- **The logs exposed a real bug.** One "timeout" run was logged as `client`. That led to finding that Gemini rejects deadlines under 10 s, which the logs exposed rather than me noticing by hand.
