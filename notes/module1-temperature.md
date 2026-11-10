# Module 1 - Task 2: Temperature experiment

Script: `scripts/task2_temperaturetesting.py`
Method: same prompt, 5 independent calls at `temperature=0.0`, then 5 at `temperature=2.0`. Count unique answers.

## Models and problems met along the way
| Attempt | Model | Result |
|---|---|---|
| 1 | `gemini-3.6-flash` | 429 RESOURCE_EXHAUSTED: free tier allows 5 requests/minute per model. Script sent 7 calls in under a minute. Fix: `time.sleep(13)` between calls. |
| 2 | `gemini-3.6-flash` | 503 UNAVAILABLE: provider overloaded (not my fault, retryable). |
| 3 | `gemini-2.5-flash` | 404 NOT_FOUND: model no longer available to new users, even though it appears in the model list. |
| 4 (final) | `gemini-3.8-flash` | Worked. No thinking tokens reported (`thoughts=None`), calls take ~1-4 s. |

Lessons:
- The model list shows what exists, not what my account may use. Only a real call proves it.
- 404 (model gone) is not retryable. 429 and 503 are retryable with backoff (Module 7).
- Do not mix results from different models.

## Experiment A: coffee shop name (short answers)
Prompt: "Give me one name for a coffee shop. Reply with only the name."

| | Temp 0.0 | Temp 2.0 |
|---|---|---|
| Answers | Beanstalk x4, Brew & Bound | Beanstalk x3, Brew & Binding, Brewed Awakening |
| Unique | 2 of 5 | 3 of 5 |

Observation: the answers are only 2-3 tokens, so there is little to vary. One answer ("Beanstalk") dominates even at temperature 2. A 2 vs 3 difference on 5 samples is within noise.

## Experiment B: one sentence about the ocean (longer answers)
Prompt: "Write one sentence about the ocean."

| | Temp 0.0 | Temp 2.0 |
|---|---|---|
| Unique | 5 of 5 | 5 of 5 |

Observation:
- Temp 0: all five share one skeleton ("The vast, ... ocean covers most of our planet, ... mysteries ..."); only adjectives and small phrases change.
- Temp 2: same skeleton with a bit more spread (4 of 5 still start "The vast..."; one starts "Covering most of our planet..." and adds a new idea, climate regulation).

## Findings
1. Temperature 0 reduces variation but is NOT deterministic. Five runs at temp 0 gave five different sentences. Never write code or tests that expect identical text twice, even at temperature 0. Validate properties of the output instead (valid JSON, correct enum value).
2. "Unique count" is a weak metric for long text: one different word makes an answer unique, so the count saturates at 5 of 5. It works better for short answers.
3. The model has a strong favorite phrasing. Even at temperature 2 (the top of the 0-2 range) it keeps returning to the same wording. High temperature widens the choice but does not remove that pull.
4. Temperature compounds with length: a 3-token answer has 2-3 decision points, a 25-token answer has many, so small differences snowball.
5. This model reported no thinking tokens and was fast and steady (about 1-4 s per call). The first call of a run can be slow (49.6 s once), so measure several runs.

## When to use which temperature
| Task | Temperature |
|---|---|
| Extraction, classification, structured JSON, tests/evals | Low (0 or near it) |
| Brainstorming, creative writing, "give me several ideas" | Higher |

## Self-check (my answers vs corrected answers)

### Q1. What does temperature change about how the model works?
- **My answer:** changing the temperature changes the way the model generates the result; if it is kept low it most probably picks the same words or known words, on higher it usually picks less known words.
- **Verdict:** Correct.
- **Precise version:** the model assigns a probability to every possible next word. Temperature reshapes that distribution: low sharpens it toward the top choice, high flattens it so less likely words get a real chance.

### Q2. If I run the same prompt twice at temperature 0, will the answers always match exactly?
- **My answer:** it can and cannot match; most probably they match, but it is also possible to be different as we saw in the 2 examples.
- **Verdict:** Partly wrong.
- **What was wrong:** "most probably they match" is not supported by my own data. Coffee shop at temp 0: 3 of 5 identical (short answers only). Ocean sentence at temp 0: 0 of 5 identical.
- **Corrected answer:** there is no guarantee, and for longer outputs they usually will not match. Temperature 0 narrows variation but does not eliminate it, so code must never depend on identical text.

### Q3. Which temperature would I use to extract data from an invoice, and why?
- **My answer:** higher temperature, because we need the actual result and cannot keep getting the same wrong result every time.
- **Verdict:** Wrong.
- **What was wrong:** temperature does not change what the model knows or how correct it is. It only changes how randomly it picks among options. Higher temperature does not make the model "try harder" for the right answer; it makes it more willing to pick a less likely word.
- **Corrected answer:** use a LOW temperature (0 or near it). An invoice has one correct answer, so I want the most likely reading, consistently. Extra randomness can produce a wrong amount, an invented field, or broken JSON. If the model is wrong at low temperature, the fix is a better prompt, a clearer schema, a better model or cleaner input, not random rolls. Then still validate the output (Module 5), because nothing is guaranteed even at low temperature.
- Higher temperature is right when I WANT different attempts (for example "give me five name ideas"), and wrong when there is a single correct answer.
