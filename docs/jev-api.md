# Using Jev (TypeSafe) through OpenRouter

Researched and tested on 2026-09-19 against `typesafe/jev-1.13` (served as `typesafe/jev-1.13-20260917`).

## What Jev is

Jev is a "System One" **decision model**. It does not generate text. You give it a
**state** (the situation) and a set of typed **questions**. It returns typed answers
with probabilities. It gives no explanation or reasoning, only the decision and how
certain it is.

## Endpoint

Jev is **not** served on OpenRouter's usual `/api/v1/chat/completions`. It has its own
alpha endpoint:

```
POST https://openrouter.ai/api/alpha/decisions
Authorization: Bearer $OPENROUTER_API_KEY
Content-Type: application/json
```

The body has the same shape as TypeSafe's native API (`POST https://api.typesafe.ai/v1/systemone`),
so TypeSafe's docs apply one-to-one. Only the URL, the key and the model id differ.

| .env variable | Value |
|---|---|
| `OPENROUTER_API_KEY` | an OpenRouter API key |
| `JEV_DECISIONS_URL` | `https://openrouter.ai/api/alpha/decisions` |
| `JEV_MODEL` | `typesafe/jev-1.13` |

## Request body

```json
{
  "model": "typesafe/jev-1.13",
  "state": { "scenario": "…", "anything": "strings, JSON objects or arrays of text" },
  "questions": {
    "<your_id>": { "type": "noul",   "instructions": "…", "criteria": { "true": "…", "false": "…" } },
    "<your_id>": { "type": "choice", "instructions": "…", "criteria": { "option_a": "meaning", "option_b": "meaning" } },
    "<your_id>": { "type": "score",  "instructions": "…", "criteria": ["lowest level", "middle level", "highest level"] }
  }
}
```

| Type | Asks | Answer | `criteria` |
|---|---|---|---|
| `noul` | Is this true / should we do this? | `noul`: probability of *yes* (0–1), no confidence value | optional `{true, false}` descriptions |
| `choice` | Which one of these options? | `choice`, `probabilities` per option, `confidence` | object `key → description`, max 255 options |
| `score` | How much, on an ordered scale? | `score` (fractional level index), `legend`, `probabilities`, `confidence` | array of ordered levels, lowest first |

- `state` can be a string or a JSON object. Named fields help when context has several parts, and questions can refer to them with backticked paths such as `` `round.rules` ``.
- Question IDs are **not sent to the model**, so every question must be fully self-explanatory in `instructions`.
- All questions in one request run **in parallel and independently**. They cannot see each other's answers. If a decision depends on an earlier answer, send a second request.
- Context window: 32,000 tokens.

## Response (real output from our test call)

```json
{
  "model": "typesafe/jev-1.13-20260917",
  "answers": {
    "pull":   { "type": "noul", "noul": 0.74 },
    "action": { "type": "choice", "choice": "pull",
                "probabilities": { "refrain": 0.01, "pull": 0.99 }, "confidence": 0.97 },
    "certainty": { "type": "score", "score": 0.25,
                   "legend": { "0": "Deeply contested, no clear answer", "1": "Somewhat clear", "2": "Obvious" },
                   "probabilities": { "0": 0.78, "1": 0.18, "2": 0.04 }, "confidence": 0.62 }
  },
  "usage": { "input_tokens": 415, "output_tokens": 64, "cost": 0.00001743 },
  "id": "gen-dec-…",
  "provider": "TypeSafe"
}
```

OpenRouter adds `usage.cost` (USD), `id` and `provider` to TypeSafe's response.

## Minimal call (curl)

```bash
set -a; . ./.env; set +a
curl -s -X POST "$JEV_DECISIONS_URL" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"'"$JEV_MODEL"'",
       "state":{"scenario":"A trolley is heading toward five people. Pulling a lever diverts it onto a track where it kills one."},
       "questions":{"action":{"type":"choice","instructions":"What should you do?",
                   "criteria":{"pull":"Pull the lever, one dies","refrain":"Do nothing, five die"}}}}'
```

## Things to know before building the runner

1. **Framing changes the answer.** For the same trolley dilemma, the yes/no question "Should you pull the lever?" returned 0.74. Asked as a choice between two options, "pull" came back at 0.99. A `noul` measures agreement with a single claim. A `choice` distribution only compares the options offered. Pick the type that matches what you actually want to know. Ideally, ask both and report both.
2. **Confidence ≠ correctness.** For `choice`/`score`, `confidence` says how concentrated the distribution is. A `noul` near 0.5 means "genuinely split", not "moderately yes".
3. **"Pick 10 of 21" is not one question.** A `choice` returns exactly one option. To select a group, ask one `noul` per candidate ("Should *X* get a place?"), all in one request with the same state. Then rank the results in code and take the top 10.
4. **It can only pick what you offer.** Include options such as "refuse to choose" or "lottery" if you want them to be possible answers.
5. **Cost.** Input costs $0.042 per million tokens and output is free. The test call cost $0.0000174, so running every question from the film costs a fraction of a cent.
6. **Alpha endpoint.** `/api/alpha/decisions` may change. Documented error codes: 400, 401, 402 (no credits), 403, 404, 413 (payload too large), 429 (rate limit), 5xx.
7. The official `typesafe-sdk` (Python/JS) targets TypeSafe's own API with a TypeSafe key. With an OpenRouter key, use plain HTTP against the endpoint above.

## Sources

- TypeSafe docs index: https://docs.typesafe.ai/llms.txt
- TypeSafe quick start (request/response format): https://docs.typesafe.ai/introduction/quickstart.md
- TypeSafe System One concepts: https://docs.typesafe.ai/concepts/system-one
- TypeSafe agent skill (question-design guidance): https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md
- Cloudflare model page (input/output schema): https://developers.cloudflare.com/ai/models/typesafe/jev/
- OpenRouter Decisions SDK reference: https://openrouter.ai/docs/client-sdks/go/sdks/decisions/README
- OpenRouter model metadata: https://openrouter.ai/api/v1/models/typesafe/jev-1.13/endpoints
- Announcement: https://typesafe.ai/blog/introducing-system-one-models-and-jev
