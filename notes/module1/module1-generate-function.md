# Module 1 - Task 4: `generate(prompt) -> str` in `app/llm/client.py`

Files:
- Real code: `app/llm/client.py`
- Throwaway test: `scripts/module1/task4_test_generate.py`

## What it is
One reusable async function that sends a prompt to the model and returns the answer text. `client.py` is the ONLY file in the app that imports `google.genai`; everything else imports `generate`.

## Why
| Reason | Explanation |
|---|---|
| One door to the provider | Only this file knows which provider is used. |
| Swappable | Changing provider means rewriting only this file's body. |
| One place for safety checks | The Task 3 lessons (finish reason, empty text) live here once. |
| Prepares later modules | Module 2 usage logging, Module 4 streaming, Module 7 retries all go here. |

## Design decisions
1. `async def`: FastAPI serves many users from one event loop. A blocking call that waits ~16 s on the model would freeze every other request. With `await`, only this function pauses; the loop serves other work.
2. Client created once at module level (`_client`): no per-call setup cost. Underscore = private to the file. The key comes from `settings`, never hardcoded or printed.
3. Returns only a `str` for now. Module 2 will need to return usage numbers too.
4. Raises `LLMError` on anything unusable (no candidates, finish_reason other than `STOP`, empty text). A cut-off or blank answer looks like a success (HTTP 200), so returning it silently would hide the problem. A loud error can be handled (retry, message to user).
5. Optional keyword-only parameters (`temperature`, `max_output_tokens`), after `*`, so they must be passed by name.

## The three safety checks
1. No candidates -> blocked prompt; avoids an `IndexError` on `candidates[0]`.
2. `finish_reason != STOP` -> catches truncation (`MAX_TOKENS`), safety blocks and any other abnormal ending, with the real reason in the message.
3. Empty text after `.strip()` -> a response can say `STOP` and still carry no text.
The finish-reason check runs before the empty-text check.

## Test result
```
--- normal call ---
Hello! It is a pleasure to meet you.

--- truncated call (cap of 5 tokens) ---
Caught LLMError: Generation did not finish normally (finish_reason=MAX_TOKENS).
```
- Normal call proves the whole chain: `.env` -> settings -> client -> async call -> checks -> clean string.
- Truncated call proves the guard: the same call that returned a silent cut-off 200 in Task 3 now raises a clear error.

## Not handled yet
- 404 / 429 / 503 / timeouts still raise the SDK's own exceptions (`ClientError`, `ServerError`), not `LLMError` -> Module 7.
- Usage and cost logging -> Module 2.
- Conversation history (`contents` is a single string) -> Module 3.
- Streaming -> Module 4.

## Common mistakes
| Mistake | What happens |
|---|---|
| Forgetting `await` | Get a coroutine object and a "never awaited" warning instead of text. |
| Calling an async function without an event loop | Needs `asyncio.run(...)` or FastAPI. |
| `ModuleNotFoundError: app` in a script | `sys.path` line needs three `.parent` calls from `scripts/module1/`. |
| Passing `temperature` positionally | Not allowed because of `*`. |

## Self-check (my answers vs corrected answers)

### Q1. Why is the function `async`, and what would go wrong with a blocking call inside FastAPI?
- **My answer:** async function is for future calls when we are waiting for a process to complete so that our code does not get blocked; the next thing continues to execute and after the execution is done it is displayed.
- **Verdict:** Mostly right, with a gap.
- **Corrected/complete answer:** `await` pauses only this function while the event loop keeps running other work. It matters for FastAPI because one event loop serves all users: a blocking model call (up to ~16 s) would freeze every other user's request for that time. With `async`, other requests are served while this one waits.

### Q2. Why raise an error on `MAX_TOKENS` and empty text instead of returning what we have?
- **My answer:** the model consumed more tokens than allotted, it surpassed the max tokens limit, and since it was undone and finish was not stop it was max tokens, so it returned empty and displayed the text we set as error text.
- **Verdict:** Off target.
- **What was wrong:** it explains how truncation happens, not why we raise. Also, the model does not "surpass" the cap: generation is stopped at it (on a thinking model, hidden thinking tokens use the budget first), and the result is not always empty; often it is half an answer.
- **Corrected answer:** a cut-off or blank answer looks like a success (HTTP 200). If `generate()` returned it silently, the user would see a half sentence or blank message and JSON parsing would break, and the caller could not tell it was bad. Failing loudly makes the problem visible and handleable (retry, show a message).

### Q3. What is the benefit of keeping all SDK calls in this one file?
- **My answer:** when we change the API one day we do not have to juggle around the whole project; we just fix it in one place and it works for the whole project.
- **Verdict:** Correct.
- **Addition:** the same single place also centralizes retries, logging and cost tracking, and is the one point to replace with a fake in tests (Module 7).

| Q | Verdict |
|---|---|
| 1 | Mostly right (add: why it matters for FastAPI's other users) |
| 2 | Off target (needs the why-raise-instead-of-return reasoning) |
| 3 | Correct (add: retries, logging, test fakes) |

## Done when
- [x] `generate("...")` returns text from a script
- [x] A tiny cap raises `LLMError` instead of returning junk
- [ ] Nothing in `app/` outside `client.py` imports `google.genai` (check before moving on)
