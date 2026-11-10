# Module 1 - Task 5: `POST /chat` (non-streaming)

Files:
- `app/schemas.py` (`ChatRequest`, `ChatResponse`)
- `app/routes/chat.py` (the router)
- `app/main.py` (`app.include_router(chat_router)`)

## What it is
A web endpoint that exposes `generate()`. A client sends `{"prompt": "..."}`; the backend calls Gemini and returns `{"reply": "..."}`. "Non-streaming" means the client waits for the whole answer in one response (streaming is Module 4).

## Request flow
```
Client (Swagger / curl / later Flutter)
   |  POST /chat  {"prompt": "..."}
   v
FastAPI route          <- validates body against ChatRequest (422 if invalid)
   |
   v
generate()             <- app/llm/client.py (Task 4)
   |
   v
Gemini
   |
   v
reply -> {"reply": "..."} back to the client
```
The Flutter app will call this endpoint and never Gemini directly, so the API key stays on the server.

## Design decisions
1. Thin route: it validates, calls `generate()`, returns the result. Model logic stays in `llm/client.py`.
2. Own router file (`routes/chat.py`) plugged in with `include_router`, so `main.py` does not become a pile of endpoints.
3. Bounded prompt (`min_length=1`, `max_length=4000`) protects cost; every token costs money.
4. `str_strip_whitespace=True` trims spaces first, so a spaces-only prompt becomes empty and is rejected instead of being sent (and paid for).
5. `LLMError` -> HTTP 502 with a generic message. 502 = "Bad Gateway": my server is fine, the upstream service gave an unusable answer. The real reason is written to the server log with `logger.warning`, not shown to the client.

## ChatRequest explained
- `class ChatRequest(BaseModel)`: a description of a valid request body; inheriting `BaseModel` gives validation and JSON-to-object conversion.
- `prompt: str = Field(min_length=1, max_length=4000)`: required text, 1-4000 characters. No default = required.
- `model_config = ConfigDict(str_strip_whitespace=True)`: trims text before validation.
- `ChatResponse` is the same idea for output; `response_model=ChatResponse` makes FastAPI enforce and document the output shape.

## Test results
### Test A: normal prompt
Body `{"prompt": "generate a hello greeting only"}` -> 200, `{"reply": "Hello!"}`.

### Test B: validation
Body `{"prompt": "   "}` (spaces only) -> 422:
```
type: string_too_short, loc: ["body", "prompt"],
msg: "String should have at least 1 character", ctx: {min_length: 1}
```
- Proves whitespace stripping works (3 spaces would otherwise pass `min_length=1`).
- The route never ran, so Gemini was never called and nothing was spent.

### Test C: statelessness
Body `{"prompt": "whats my name?"}` -> 200, `"I don't know your name yet! What should I call you?"`.
Each request is an independent call; the server stores nothing between requests and the model remembers nothing.

### Test D (optional): force the 502
Not done yet. Plan: temporarily pass `max_output_tokens=5` to `generate(...)` in `chat.py`, send a long prompt, expect 502 with the generic message and the real reason in the uvicorn log, then revert.

## Problems met
- `ImportError: cannot import name 'EchoRequest' from 'app.schemas'`: the Echo classes had been commented out in `schemas.py` while `main.py` still imported them. Lesson: read the LAST line of a traceback and the line from my own file; check the name exists, is spelled the same, and is not commented out.
- `GET / 404 Not Found` in the uvicorn log is not an error: no route is defined for `/`. Use `/docs` or `/health`.

## Not handled yet
- 429 / 503 / 404 / timeouts from the SDK are not `LLMError`; they surface as a generic 500 -> Module 7.
- Conversation history (each request is one prompt) -> Module 3.
- Auth and rate limits (anyone who reaches the URL can spend tokens) -> Module 8.
- Usage and cost logging -> Module 2.

## Common mistakes
| Mistake | What happens |
|---|---|
| Forgetting `app.include_router(...)` | `/chat` returns 404 and is missing from `/docs`. |
| Forgetting `await` | The reply is a coroutine, not text. |
| Changing `.env` without restarting uvicorn | `--reload` watches only `.py` files. |
| Free-tier limit (5 requests/minute) | A 500 caused by a 429; wait a minute between tests. |

## Self-check (my answers vs corrected answers)

### Q1. Why does the route catch `LLMError` and send a generic message instead of the error text?
- **My answer:** it sends a generic message because we added exception handling; if generation fails it displays the text we set so the user knows what the issue is. A non-technical person might not understand what max token means.
- **Verdict:** Mostly correct.
- **Additions:** (a) security: raw error text can leak internals (model name, finish reasons, later prompts); generic errors are a Module 8 rule. (b) The real error is not lost: `logger.warning` records the technical detail in the server log for the developer. (c) The generic message does not tell the user what went wrong, only that it failed, and that is intentional.

### Q2. Why does a bad request never cost money?
- **My answer:** the request was never made because it did not meet the requirements (for example min length 1), so we show an error before it was ever sent to Gemini.
- **Verdict:** Correct.
- **Addition:** validation runs before the route function; FastAPI returns 422 and `generate()` is never called.

### Q3. Why does the model not know my name between two requests?
- **My answer:** there is no conversation history at the moment, so it does not remember who I am.
- **Verdict:** Correct, with one deeper point.
- **Addition:** the model itself is stateless: it remembers nothing between calls. Even if the server stored history, the model would know nothing unless the whole history is resent inside every new request. That is what Module 3 builds, and why long chats cost more.

| Q | Verdict |
|---|---|
| 1 | Mostly correct (add: security, real error is logged) |
| 2 | Correct |
| 3 | Correct (add: model is stateless, history must be resent each time) |

## Module 1 "done when"
Explain, without notes, what one API call sends and returns, and why "stateless" matters:
- Sends: model, contents (prompt), parameters (temperature, max output tokens).
- Returns: text, token usage (including hidden thinking tokens), finish reason, response id / model version.
- Stateless: the model remembers nothing between calls, so context must be resent every time; this drives cost and the history strategies of Module 3.
