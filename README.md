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
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

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
