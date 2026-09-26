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

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
