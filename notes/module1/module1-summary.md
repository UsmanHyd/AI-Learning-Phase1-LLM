# Module 1 Summary: The Request Lifecycle

Goal of the module: understand exactly what one API call to the model sends and returns, and why "stateless" matters. Then wrap that call in reusable backend code and expose it as an endpoint.

Detailed notes per task live in the other files in this folder:
- `module1-response-fields.md` (Task 1)
- `module1-temperature.md` (Task 2)
- `module1-truncation.md` (Task 3)
- `module1-generate-function.md` (Task 4)
- `module1-chat-endpoint.md` (Task 5)

---

## Task 1: Print the raw response and explain every field
**What we did:** wrote `scripts/01_raw_response.py`, sent one prompt to Gemini and printed the whole response object (not just the text). Hit a 404 first (model name not found), listed available models with a small script and picked a working one.

**What the response contains**
| Part | Key fields |
|---|---|
| Answer | `candidates[0].content.parts[0].text` (also `response.text`), `role = model` |
| Why it stopped | `finish_reason` (`STOP` = finished normally) |
| Tokens | `prompt_token_count`, `candidates_token_count`, `thoughts_token_count`, `total_token_count` |
| Identifiers | `model_version`, `response_id` |
| Extras | HTTP headers (`server-timing` showed ~16.6 s), `prompt_feedback`, `parsed`, `thought_signature` |

**What we learned**
- The answer is nested: candidates -> content -> parts -> text.
- Total tokens = input + visible output + hidden thinking tokens. Example: 10 + 51 + 707 = 768. The model spent about 14x more tokens thinking than answering a two-sentence question; thinking is billed like output and adds latency.
- A non-`STOP` finish reason means the call worked but the generation ended early. Bad key, no credits, rate limits and server errors are different: they are HTTP errors and no response object exists.
- `model_version` shows what an alias like `gemini-flash-latest` resolved to; record it because aliases move.
- Model names can fail with a 404 even when documentation uses them; list the models your own key can use.

---

## Task 2: Temperature experiment
**What we did:** `scripts/module1/task2_temperaturetesting.py` ran the same prompt 5 times at `temperature=0` and 5 times at `temperature=2`, and counted unique answers. Two experiments: short coffee-shop names, then a one-sentence answer about the ocean.

**Results**
| Experiment | Temp 0 unique | Temp 2 unique |
|---|---|---|
| Coffee shop name (2-3 tokens) | 2 of 5 | 3 of 5 |
| One sentence about the ocean | 5 of 5 | 5 of 5 |

**Problems met on the way (each a real-world lesson)**
| Error | Meaning |
|---|---|
| 429 RESOURCE_EXHAUSTED | Free tier allows 5 requests/minute per model. Fix: pause between calls. |
| 503 UNAVAILABLE | Provider overloaded; temporary, retryable, not my fault. |
| 404 NOT_FOUND on `gemini-2.5-flash` | Model retired for new users even though it appeared in the model list. The list shows what exists, not what my account may use. |
| Model mix-up | The final results came from `gemini-3.5-flash-lite`, not `gemini-3.8-flash`. Always record the exact model per experiment. |

**What we learned**
- Temperature changes how the model chooses each next word: low sharpens toward the most likely word, high gives less likely words a chance.
- Temperature 0 reduces variation but is NOT deterministic. Never write code or tests that expect identical text twice.
- "Unique count" is a weak metric for long text because one different word makes an answer unique.
- Short answers leave little to vary; effects compound with length.
- The model has favorite phrasings that survive even temperature 2.
- Temperature does not change what the model knows or how correct it is. Use low for extraction, classification, JSON and tests; higher only when I want different attempts (brainstorming).

---

## Task 3: Truncation with a low `max_output_tokens`
**What we did:** `scripts/module1/task3_truncation.py` ran one long prompt with caps of 5, 20, 60 and 1000 on two models (`gemini-3.6-flash`, a thinking model, and `gemini-3.5-flash-lite`).

**Results in short**
| Model | Behavior |
|---|---|
| gemini-3.6-flash | Caps 5 and 20: EMPTY text (thinking used the whole budget). Cap 1000: thinking used 960 tokens, leaving 36 for the answer (126 characters of text). |
| gemini-3.5-flash-lite | No thinking tokens; nearly the whole cap became visible text and the answer was cut off every time. |
| Both | `finish_reason = MAX_TOKENS` on every run, including cap 1000. HTTP status was always 200. |

**What we learned**
- Hitting the cap is not an error. The call returns 200 with a cut-off answer; the only warning is `finish_reason = MAX_TOKENS`.
- On thinking models, hidden thinking tokens count against the same cap, so the visible text can be empty while the call still succeeds.
- A large cap is not automatically safe (my prediction that 1000 would finish was wrong).
- Truncated output is still billed.
- Truncated JSON is usually invalid JSON (safe: parse error); the dangerous case is partial data that looks valid, like a half-cut email.
- Rules: check `finish_reason` on every call, treat empty text as a failure, never parse or repair JSON from a `MAX_TOKENS` response, include thinking tokens in cost estimates.

---

## Task 4: `generate(prompt) -> str` in `app/llm/client.py`
**What we did:** turned the script logic into one reusable async function and tested it with `scripts/module1/task4_test_generate.py`.

**Design**
- `client.py` is the only file in the app that imports `google.genai`.
- `async def`, using `client.aio`, so one slow model call does not freeze FastAPI for other users.
- Client created once at module level, key from `settings`.
- Optional keyword-only `temperature` and `max_output_tokens`.
- Three safety checks that raise `LLMError`: no candidates, `finish_reason != STOP`, empty text.

**Test result**
- Normal call returned a clean greeting.
- Cap of 5 raised `LLMError: Generation did not finish normally (finish_reason=MAX_TOKENS)`, turning the silent failure from Task 3 into a loud one.

**What we learned**
- One door to the provider means a provider change touches one file, and retries, logging, cost tracking and test fakes can all live in one place.
- `await` pauses only the current function; the event loop serves other requests meanwhile.
- A cut-off or blank answer looks like a success (200), so the function must fail loudly instead of returning it.
- Still unhandled: SDK errors (404, 429, 503, timeouts), usage logging, history, streaming.

---

## Task 5: `POST /chat` (non-streaming)
**What we did:** added `ChatRequest` and `ChatResponse` to `schemas.py`, created `app/routes/chat.py` with an `APIRouter`, and plugged it into `main.py` with `include_router`.

**Flow:** client -> FastAPI route (validate) -> `generate()` -> Gemini -> `{"reply": "..."}`.

**Test results**
| Test | Result |
|---|---|
| Normal prompt | 200, `{"reply": "Hello!"}` |
| Spaces-only prompt | 422 `string_too_short` (whitespace stripped first); Gemini never called |
| "whats my name?" | Model did not know: each request is independent |

**What we learned**
- A Pydantic request model guards the door: bad input returns 422 before the route runs, so it costs nothing.
- `str_strip_whitespace=True` stops a spaces-only prompt from passing `min_length=1`.
- Keep routes thin; put model logic in `llm/client.py`.
- `LLMError` becomes a 502 with a generic message; the real reason goes to the server log. Generic errors avoid leaking internals.
- Problems met: an `ImportError` because the Echo classes were commented out while `main.py` still imported them, and `GET / 404` in the log, which is not an error (no route at `/`).

---

## Big picture: what Module 1 taught
1. **One API call, fully understood.** It sends model + contents + parameters. It returns text, token usage (including hidden thinking tokens), a finish reason and identifiers.
2. **The model is stateless.** It remembers nothing between calls; context must be resent every time. This is the reason Module 3 (history) exists and why long chats cost more.
3. **HTTP 200 does not mean the answer is good.** Truncation, empty text and blocks arrive as normal responses. Always check `finish_reason` and the text.
4. **Output is not deterministic**, even at temperature 0. Validate properties, never compare exact text.
5. **Tokens are money, and some are invisible.** Thinking tokens are billed and count against the output cap.
6. **Failures come in different kinds**, and each needs different handling later:
   | Status | Meaning | Retry? |
   |---|---|---|
   | 404 | Model name wrong or retired | No: fix config |
   | 429 | Rate limit exceeded | Yes, after waiting |
   | 503 | Provider overloaded | Yes, with backoff |
   | 200 + non-STOP finish | Truncated or blocked | Depends: handle explicitly |
7. **Architecture habits that started here:** a single file talks to the provider; settings come from `.env`; routes are thin; validation happens at the door; clients see generic errors while developers see real logs; record the exact model for every experiment.

## What is still missing (and where it gets fixed)
| Gap | Module |
|---|---|
| Usage and cost logging, token counting, context overflow, rate-limit headers | 2 |
| Conversation history, system prompts, sliding window, summarization | 3 |
| Streaming responses | 4 |
| Structured output and validation | 5 |
| Tool calling | 6 |
| Timeouts, retries with backoff, fallback model, proper exception-to-HTTP mapping | 7 |
| Auth, per-user rate limits, quotas, input limits | 8 |
| Prompt injection defenses | 9 |

## Module 1 "done when" check
Explain, without notes:
- What one API call sends: model, contents, parameters (temperature, max output tokens).
- What it returns: text, token usage (input, output, thinking), finish reason, response id / model version.
- Why stateless matters: the model remembers nothing, so history must be resent each time, which drives cost, latency and the history strategies of Module 3.
