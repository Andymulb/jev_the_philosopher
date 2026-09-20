# Jev takes the bunker exam

What does a *decision model* answer when you give it the moral dilemmas from the film
*The Philosophers* (2013, US title *After the Dark*), and how long does it take?

This repository holds the experiment, the raw answers and the LaTeX source of the paper
**"A Quarter of a Second to Decide Who Lives"**.

Jev 1.13 by TypeSafe is not a chat model. It takes a situation and typed questions, and returns
a typed answer with probabilities and no explanation. We put 39 questions from the film to it,
ten times each, through OpenRouter.

## What came out

- **Speed does not depend on difficulty.** Median 275 ms per request, whether the question was a
  maths puzzle or who should die (274 ms when the model was almost undecided, 272 ms when it was
  sure). People in a classic study needed 4.6–6.8 s per moral dilemma, and were slowest when
  they overruled their instinct.
- **Stable when repeated, sensitive to wording.** Across ten runs answers varied by at most 0.08.
  Rewording the same dilemma moved them far more: the trolley problem gave 0.99 for diverting as
  a choice between options and 0.78 as a yes/no question.
- **Agreement with the film is partial.** On the 29 questions where the film makes the
  characters' decision clear, Jev matched it 11 times, differed 11 times and was genuinely
  undecided (0.45–0.55) 7 times. In the three bunker rounds it shared 9, 8 and 7 of its ten
  picks with the film.

The whole experiment, 410 requests, cost **$0.0081**.

## Repository layout

```
questions.json     the 39 questions as typed Jev requests, with the film's answers
run_tests.py       runs the experiment and fetches each request's latency from OpenRouter
analysis.py        shared scoring: undecided band, agreement with the film, rankings
results/           one run: raw answers (raw.jsonl), summary.json, readable summary.md
paper/main.tex     the paper (IEEE format)
paper/references.bib
paper/make_data.py turns a run into every number, table and plot the paper uses
paper/source-audit.md   how each source was verified
docs/jev-api.md    how Jev is called through OpenRouter, with the pitfalls
docs/the-philosophers-questions.md   the questions with their sources and the film's answers
```

## Reproducing

Requirements: Python 3.10+ (standard library only), an OpenRouter API key with credit, and for
the paper a TeX Live installation with `IEEEtran`, `biblatex`, `biblatex-ieee`, `pgfplots` and
`newtx`.

```bash
cp .env.example .env        # then paste your OpenRouter key into .env
python3 run_tests.py --runs 10          # ~410 requests, about $0.01, a few minutes
python3 paper/make_data.py              # results -> paper/generated/
cd paper && latexmk -pdf main.tex       # -> main.pdf
```

Useful variants:

```bash
python3 run_tests.py --runs 1 --only QA.1,Q2.3      # a few questions only
python3 run_tests.py --add-timing results/<run>     # add latency to an existing run
python3 paper/make_data.py results/<run>/summary.json
```

The paper builds from the run already in `results/`, so you can rebuild it without an API key.
`paper/generated/` is not committed because it is derived; run `make_data.py` first.

## Reading the data

`results/<run>/summary.md` is the human-readable report. `summary.json` has the same content as
data: per question the mean, range and per-run values, the choice distributions, the latency
statistics and the comparison with the film. `raw.jsonl` holds every request and response
exactly as sent and received, one line per request.

## Caveats worth knowing before citing this

- The film's answers are **what its characters decided in a story**, not correct answers.
  Comparing against them measures similarity to the film, not moral quality.
- The questions are paraphrases. No transcript of the film is publicly available.
- Four warm-up scenarios (a trolley variant with a child, three questions about a fall from a
  cliff) rest on the author's recollection of the film; no source found describes them. They are
  marked in the data and in the paper.
- Latency is the provider latency OpenRouter reports, which excludes the network to and from
  OpenRouter.
- One model version, one day, mostly one wording per question. Because the model is so stable
  across runs, more repetitions add little; more wordings would add more.

## Licence

MIT, see `LICENSE`. The film and the works cited in the paper belong to their respective
rights holders.
