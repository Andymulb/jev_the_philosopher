# Source audit (WP3b), 20 September 2026

Every source checked against the original. "Checked" means I opened the source and confirmed
the bibliographic details and that it actually supports the claim it is cited for.

## Claims and their sources

| Claim in the paper | Source | Checked |
|---|---|---|
| Trolley problem as a philosophical thought experiment | Foot 1967, Thomson 1976, Thomson 1985 | ✓ originals identified, DOIs added for both Thomson papers |
| People approve diverting but reject pushing | Greene et al. 2001, Thomson 1985 | ✓ Greene reports participants' responses matched these intuitions |
| Film premiered 2013, US title *After the Dark*, plot of the three rounds, each character's two role cards | Wikipedia (fixed revision) | ✓ now cited as the exact revision (oldid 1370168198, 19 Aug 2026) |
| The film opens with the trolley problem in two versions, Plato's cave, the infinite monkey theorem and an "ignorance is bliss" experiment | The Love Pirate 2014; Horizon and the Fringe 2014; Conmose 2016 | ✓ The Love Pirate names all four explicitly; the other two confirm the trolley and the cave |
| The film frames the rounds as calculation versus human values | Blimey; The Love Pirate 2014 | ✓ |
| Critics called the film's philosophy shallow | Philosophy in Film 2018; Horizon and the Fringe 2014; Never Felt Better 2014 | ✓ all three say so |
| Human decision times of 4.6–6.8 s | Greene et al. 2001, Fig. 3 | ✓ read from the figure; the paper states ±0.1 s and that the numbers come from a chart |
| Procedure of the human study (3 screens, self-paced, max 46 s) | Greene et al. 2001, note 12 | ✓ quoted from the paper's own methods note |
| Jev is a "System One" model that returns typed answers with probabilities | TypeSafe blog; TypeSafe docs | ✓ |
| The three question types and their answer formats | TypeSafe quick start; Cloudflare model page | ✓ both give the schema |
| Probabilities are calibrated; 0.5 means genuinely split; questions in one request are independent | TypeSafe agent skill | ✓ |
| Jev is served on a separate decisions endpoint, not as a chat model | OpenRouter decisions docs; OpenRouter model endpoint | ✓ |
| Release in September 2026 | OpenRouter model endpoint (creation timestamp) | ✓ |
| Per-request latency | OpenRouter generation-statistics endpoint | ✓ the field is the provider latency |
| Allegory of the Cave | Plato, *Republic*, Book VII, 514a–520a | ✓ edition and passage given |
| Infinite monkeys, probability 1 | Borel 1913 | ✓ see correction below |

## Corrections made

1. **Borel's title was wrong.** The paper (like many secondary sources) cited "Mécanique
   statistique et irréversibilité". The actual title is **"La mécanique statique et
   l'irréversibilité"**, *J. Phys. Theor. Appl.*, vol. 3, no. 1, pp. 189–196, 1913,
   doi 10.1051/jphystap:019130030018900. Verified against the HAL archive record (jpa-00241832).
2. **DOIs added:** Thomson 1976 (10.5840/monist197659224), Thomson 1985 (10.2307/796133),
   Borel 1913. Greene 2001 already had one.
3. **By-lines added** where the sources have them: Gaby Shedwick (Collider, 23 Mar 2025),
   Matthew Jones (Philosophy in Film, 11 Mar 2018), J. Edward Hackett (Horizon and the Fringe,
   2 Sep 2014), Carola (Conmose, 28 Jul 2016), lovepirate77 (The Love Pirate, 14 Mar 2014),
   NFB (Never Felt Better, 24 Oct 2014). Blimey shows neither author nor date, which the entry
   now states.
4. **Wikipedia is cited by permanent revision link**, not the live page.
5. **Grokipedia removed.** It is an AI-generated wiki and therefore not a source a paper should
   lean on. Everything it was cited for is covered by The Love Pirate, which names all four
   opening exercises explicitly.
6. **Foot 1967:** the *Oxford Review* page range 5–15 is confirmed by several catalogue records;
   the entry now also names the 1978 reprint in *Virtues and Vices*, which is far easier to obtain.

## IEEE formatting fixes

- Switched the bibliography to `style=ieee`, which numbers references in order of first
  appearance, as IEEE requires.
- Protected capitals in titles with braces. IEEE style lowercases titles, which had produced
  "Introducing system one models & jev" and "the ruins of john huddle's".
- `biblatex-ieee`'s driver for online sources never prints the publication date, although the
  IEEE format calls for it. The driver is redefined in `main.tex` so online sources now read
  *Author, "Title," Site, Date, Accessed: date. [Online]. Available: URL*.
- Grouped citations such as [4], [5], [6] can no longer break across lines.

## Sources that remain weak, and why they are acceptable

Five of the sixteen sources are film blogs (Blimey, The Love Pirate, Conmose, Never Felt Better,
Philosophy in Film) and one is a fan-facing outlet (Collider). They are used only for what the
film shows and how it was received, never for an empirical claim. The film itself is the primary
source for all of it; no transcript is publicly available, which the paper states in its
limitations. Blimey has neither author nor date and is the weakest of them; it is only ever
cited alongside a second source.

---

# Second pass: the sources added for the implications section

Added 20 September 2026, verified the same way. Each was checked against Crossref (authors,
venue, volume, issue, pages, year, DOI) or, for the two regulations and the three industry
sources, against the publisher's own page. The bibliography now holds 48 entries; every one is
cited in the text, and no entry is cited that is not in the bibliography (checked mechanically).

| Claim in the paper | Source | Checked |
|---|---|---|
| Fast, automatic judgement is one of two systems, the second of which corrects it | Kahneman, *Thinking, Fast and Slow*, 2011 | ✓ |
| Time pressure changes which answer people give, not just how fast | Suter & Hertwig 2011, *Cognition* 119(3) | ✓ DOI |
| Responsibility gap when a machine decides | Matthias 2004; Sparrow 2007 | ✓ DOIs |
| Meaningful human control requires tracking reasons and tracing to a person | Santoni de Sio & van den Hoven 2018 | ✓ DOI |
| Automating the routine leaves people supervising what they no longer practise | Bainbridge 1983, *Automatica* | ✓ DOI |
| People follow machine recommendations against their own evidence | Skitka et al. 1999; Parasuraman & Riley 1997; Goddard et al. 2012 (clinical) | ✓ DOIs |
| Mandated human oversight can become a legitimating ritual | Green 2022; Zerilli et al. 2019 | ✓ DOIs |
| Automated decisions can outrun human intervention; circuit breakers as mandated slowness | Kirilenko et al. 2017, *Journal of Finance* | ✓ DOI (the published version, not the SSRN preprint) |
| Standard map of algorithmic-ethics concerns, incl. traceability | Mittelstadt et al. 2016 | ✓ DOI |
| Rule by systems whose grounds cannot be contested | Danaher 2016 | ✓ DOI |
| Who writes the question is a social question | Rahwan 2018 | ✓ DOI |
| Moral preferences over such dilemmas vary across cultures | Awad et al. 2018, *Nature* | ✓ DOI |
| People want others' cars utilitarian and their own protective | Bonnefon et al. 2016, *Science* | ✓ DOI |
| A deployed recidivism tool no better than untrained people | Dressel & Farid 2018, *Science Advances* | ✓ DOI |
| A widely deployed sepsis model performed worse than advertised | Wong et al. 2021, *JAMA Internal Medicine* | ✓ DOI |
| Outsourcing judgement erodes the skill | Vallor 2015, *Philosophy & Technology* | ✓ DOI (published 2015 in vol. 28(1); Crossref lists the 2014 online-first date) |
| Overseers must stay aware of automation bias, interpret output, override or stop the system | Regulation (EU) 2024/1689, Art. 14 | ✓ wording checked against the article text |
| Right not to be subject to a purely automated decision | Regulation (EU) 2016/679, Art. 22 | ✓ |
| A claim reviewed, fraud-checked, approved and paid in three seconds | Lemonade blog 2017, plus *Carrier Management* coverage | ✓ company source and independent trade report |
| Moderation at a scale only automation reaches; precision around 91–92 % | Meta Integrity Reports, H1 2026 | ✓ |

## Note on the industry sources

The Lemonade record is a company claim about its own product, reported by trade press; it is
cited as an example of what is already deployed, not as a measurement. The Meta figures are
self-reported platform statistics. Both are labelled as such in the text.
