# Module 1 - Task 3: Truncation with a low `max_output_tokens`

Script: `scripts/module1/task3_truncation.py`
Prompt: "Explain how the internet works in detail."
Caps tried: 5, 20, 60, 1000
Models (same prompt on both): `gemini-3.6-flash` (thinking model) and `gemini-3.5-flash-lite` (no thinking tokens reported).

## What the task shows
`max_output_tokens` is a hard cap on generated tokens. When the model reaches it, generation stops immediately, even mid-sentence or mid-word. The HTTP call still succeeds (200); the only warning is `finish_reason = MAX_TOKENS` instead of `STOP`.

## Results

### gemini-3.6-flash (thinking model)
| Cap | finish_reason | output tokens | thought tokens | Text |
|---|---|---|---|---|
| 5 | MAX_TOKENS | None | 2 | EMPTY (0 chars) |
| 20 | MAX_TOKENS | None | 17 | EMPTY (0 chars) |
| 60 | MAX_TOKENS | 3 | 53 | "The internet is" (15 chars) |
| 1000 | MAX_TOKENS | 36 | 960 | 126 chars, a stray fragment |

### gemini-3.5-flash-lite (no thinking)
| Cap | finish_reason | output tokens | thought tokens | Text |
|---|---|---|---|---|
| 5 | MAX_TOKENS | 1 | None | "At" |
| 20 | MAX_TOKENS | 16 | None | 81 chars, cut mid-sentence |
| 60 | MAX_TOKENS | 56 | None | 264 chars, cut mid-sentence |
| 1000 | MAX_TOKENS | 996 | None | 4182 chars, cut off |

Arithmetic check (holds in every row): total = prompt (9) + thoughts + output. Example: 9 + 960 + 36 = 1005.

## Findings
1. The thinking-token trap is real. On the thinking model, hidden thinking tokens count against `max_output_tokens`. With caps of 5 and 20, thinking used the whole budget and the visible text was EMPTY, while the call still returned 200.
2. Even a cap of 1000 was not safe: thinking used 960 tokens and left 36 for the answer. I paid for 1005 tokens and got 126 characters of text.
3. Without thinking, the cap behaves as expected: nearly all of it becomes visible text (16 of 20, 56 of 60, 996 of 1000), and the answer is cut off every time.
4. My prediction was wrong: I expected the 1000 cap to finish with `STOP`. Both models still ended with `MAX_TOKENS`. Never assume a large cap is safe.
5. The cap is a ceiling, not an exact count (cap 5 gave only 1 output token on flash-lite). Observation only; not fully explained.
6. Empty text with `MAX_TOKENS` is a real failure case: HTTP 200, `response.text == ""`, and the only signal is `finish_reason`.
7. Truncated output is still billed.
8. Record the exact model for every experiment. A mix-up between models was caught only because the model was noted (Task 2 notes were corrected).

## Backend rules that come out of this
| Rule | Reason |
|---|---|
| Check `finish_reason` on every call | It is the only signal of truncation |
| Treat empty text as a failure too | Can happen with `MAX_TOKENS` on thinking models |
| Do not set the cap too tight on thinking models | Thinking tokens come out of the same budget |
| Never parse or repair JSON from a `MAX_TOKENS` response | It is cut off; a repaired value can be silently wrong |
| Include thinking tokens in cost estimates | They are billed but never shown |

## Self-check (my answers vs corrected answers)

### Q1. Does hitting `max_output_tokens` cause an error? What tells you it happened?
- **My answer:** no, it doesn't show any error; the generated result is just cut off and we still get 200 success.
- **Verdict:** Correct, but incomplete.
- **Corrected/complete answer:** no error and HTTP 200. What tells me is `finish_reason = MAX_TOKENS` on the candidate. That field is the only warning, so code must check it.

### Q2. Why can the visible text be empty even though I got a response?
- **My answer:** due to the cap limit, since the finish reason was max token, so a full response was never generated.
- **Verdict:** Partly right.
- **What was missing:** "a full response was never generated" is true for any truncation and does not explain why the text is EMPTY.
- **Corrected answer:** on a thinking model, the hidden thinking tokens are counted against the same cap. With a cap of 20 on `gemini-3.6-flash`, thinking used 17 tokens and nothing was left for visible text, so `response.text` was empty while the call still returned 200 with `MAX_TOKENS`.

### Q3. Why does this matter for structured output like JSON?
- **My answer:** because if we get max token, any important data field can be cut off and still show 200 success, such as user JSON with name, id, age, email where the email was cut off due to max token.
- **Verdict:** Correct, with one refinement.
- **Refinement:** a truncated JSON string is usually invalid JSON (the closing `}` or quote never arrives), so `json.loads` or Pydantic will often raise a parse error, which is the safe outcome. The dangerous case is partial data that looks valid, for example a repaired or conveniently cut value like `"email": "sam@gm"` that gets stored without anyone noticing.
- **Rule:** check `finish_reason` BEFORE parsing, and never repair or parse a `MAX_TOKENS` response.

| Q | Verdict |
|---|---|
| 1 | Correct (add: `finish_reason` is how you detect it) |
| 2 | Partly right (missing: thinking tokens eat the cap) |
| 3 | Correct (refine: usually a parse error; the real danger is partial values that look valid) |
