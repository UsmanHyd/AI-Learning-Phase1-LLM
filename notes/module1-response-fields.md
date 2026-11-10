# Module 1 - Task 1: Anatomy of a raw Gemini response

Script: `scripts/task1_RawResponse.py`
Prompt: "Explain what an API is in two sentences."
Model alias: `gemini-flash-latest` -> resolved to `gemini-3.6-flash`

## The big picture
One API call returns an object with four parts:
1. `candidates` - the answer itself
2. `usage_metadata` - token counts (what I am billed for)
3. `sdk_http_response` - HTTP headers from Google's server
4. Small identifiers/extras - model version, response id, mostly-empty fields

## 1. `candidates` (the answer)
Path to the text: `response.candidates[0].content.parts[0].text`
(`response.text` is a shortcut that joins the text parts.)

| Field | Value seen | Meaning |
|---|---|---|
| `candidates` | list of 1 | The model can return several alternative answers; I got one, so I read index 0. |
| `content.role` | `model` | Who is speaking. Roles are `user`, `model` (and system instructions) - used in Module 3. |
| `content.parts` | 1 `Part` | The answer is a list of pieces. Here: one text piece. Tool calls (Module 6) also arrive as parts. |
| `Part.text` | "An API ... is a set of rules..." | The generated answer. |
| `Part.thought_signature` | long bytes blob | Encrypted token from the model's internal thinking. Contents are meaningless to me; it lets the model continue its reasoning if I send the conversation back (matters for tool calling). Noise when printed. |
| `finish_reason` | `STOP` | The model ended naturally. |
| `index` | `0` | Position of this candidate in the list. |

### finish_reason
- `STOP` = finished normally, answer is complete.
- Anything else = generation ended for a reason other than natural completion, e.g. `MAX_TOKENS` (answer truncated at my token cap), or a safety/content block. The response still arrives, but the answer may be incomplete or empty.
- This is NOT the same as an API failure. Bad key, no credits, rate limits, or server errors come back as HTTP errors (401/403/429/5xx) and no normal response object exists.
- Always check `finish_reason` before trusting the text (important for truncated JSON in Module 5).

## 2. `usage_metadata` (tokens = money)
| Field | Value | Meaning |
|---|---|---|
| `prompt_token_count` | 10 | Tokens I sent (input). |
| `candidates_token_count` | 51 | Tokens of the visible answer (output). |
| `thoughts_token_count` | 707 | Hidden internal "thinking" tokens. Never shown to me. |
| `total_token_count` | 768 | 10 + 51 + 707. |
| `prompt_tokens_details` | TEXT: 10 | Input count split by type (text/image/audio). |

Key discovery: the model spent ~14x more tokens thinking (707) than answering (51) for a 2-sentence question.
- Thinking tokens are billed like output tokens, so the real output cost is ~758 tokens, not 51.
- Thinking also adds latency.
- A very low `max_output_tokens` can be consumed by thinking before any visible text appears (to test in Task 3).
- Cost estimates in Module 2 must include thinking tokens.

## 3. `sdk_http_response` (headers)
Mostly generic web-server headers. Useful ones:
- `server-timing: dur=16637` -> server took ~16.6 s for a tiny prompt (mostly thinking). Latency matters in Module 2.
- `x-gemini-service-tier: standard` -> pricing/priority tier.
- `content-encoding: gzip`, `content-type: application/json` -> compressed JSON body.
- `date` -> when the response was sent.
- Rate-limit headers: none seen here; I will look for them when I trigger a 429 (Module 2).

## 4. Identifiers and extras
| Field | Value | Meaning |
|---|---|---|
| `model_version` | `gemini-3.6-flash` | The exact model behind the alias. The alias can change over time, so record this whenever I measure something. |
| `response_id` | `Da_yara3...` | Unique id of this response, for debugging/support. |
| `prompt_feedback` | `None` | Info on whether my prompt was blocked. None = fine. |
| `create_time` | `None` | Not provided by this API. |
| `model_status` | `None` | Not provided. |
| `parsed` | `None` | Used for structured output (Module 5) when a schema is passed. |
| `automatic_function_calling_history` | `[]` | Used when the SDK runs tools automatically (Module 6). Empty: no tools used. |

## Key takeaways
1. The answer is nested: candidates -> content -> parts -> text.
2. Total tokens = input + visible output + thinking tokens.
3. `STOP` means a clean finish; any other finish reason means check for truncation or blocking.
4. HTTP errors (credits, key, rate limit) are separate from `finish_reason`.
5. Pin or record `model_version`, since aliases move.
6. Each call is stateless: nothing in this response carries memory to the next call.

## Self-check (my answers vs corrected answers)

### Q1. Where is the actual answer text inside the response?
- **My answer:** inside content => parts => part.text
- **Verdict:** Correct (I skipped the `candidates[0]` step).
- **Corrected/complete answer:** `response.candidates[0].content.parts[0].text`. `response.text` is a shortcut for the same thing.

### Q2. Why is `total_token_count` much bigger than the visible answer?
- **My answer:** total token count is high as it also considers the thinking tokens as well, so thinking + in token + out token, that's why it's higher than just in + out token.
- **Verdict:** Correct.
- **Corrected/complete answer:** total = input + visible output + thinking tokens, i.e. 10 + 51 + 707 = 768. Thinking tokens are hidden and billed like output.

### Q3. What would a `finish_reason` other than `STOP` mean for my code?
- **My answer:** other than stop it means the finish has failed, maybe due to expired credits or any other reason.
- **Verdict:** Partly wrong.
- **What was wrong:** expired credits, bad key, rate limits, or server errors are not finish reasons. They are HTTP errors (401/403/429/5xx): the SDK raises an exception and no response object exists. (The 404 model-not-found error I hit earlier was this kind.)
- **Corrected answer:** a non-`STOP` finish reason means the call succeeded and a response came back, but generation ended for a reason other than finishing naturally, for example:
  - `MAX_TOKENS`: the answer hit my output cap and was cut off.
  - A safety/content block: the text may be partial or missing.
  My code must check `finish_reason` before trusting the text (a `MAX_TOKENS` result means truncated, broken JSON in Module 5).

| Situation | How it shows up |
|---|---|
| Bad key, expired credits, rate limit, server down | HTTP error, exception, no response object |
| Call worked but generation stopped early | Normal response with non-`STOP` `finish_reason` |
