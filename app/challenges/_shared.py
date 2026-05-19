"""
Helpers shared by all challenge app.py files.

The point of this module is to be the single place where the LLM call
shape and the socket I/O conventions live, so swapping the model or
the prompt template only touches one file.

Every challenge's `app(conn, i, llm, session)` signature includes `session`
for uniformity — single-turn challenges can ignore it; multi-turn
challenges pass `history=session` into `complete()` to interleave prior
turns into the messages list.
"""

from typing import Optional


# --- Socket I/O -----------------------------------------------------------

def send(conn, msg: str) -> None:
    """Send a single bot message with the standard ' [bot] ' prefix and newline."""
    conn.send(f" [bot] {msg}\n".encode())


def send_raw(conn, msg: str) -> None:
    """Send a raw line without the [bot] prefix. Use sparingly."""
    conn.send(msg.encode())


def recv_question(conn, max_len: int = 2048) -> Optional[str]:
    """Display ' > ' prompt, read one line of user input, strip CR/LF.

    Returns None if the client disconnected, otherwise the question (which
    may be empty — callers should `continue` on empty input to match the
    original behavior).
    """
    conn.send(b" > ")
    data = conn.recv(max_len)
    if not data:
        return None
    return data.decode(errors="replace").strip("\n").strip("\r")


# --- LLM completion -------------------------------------------------------

# Defaults for create_chat_completion. Stop tokens are no longer needed —
# the model's chat template owns turn boundaries.
_LLM_DEFAULTS = {
    "max_tokens": 1000,
    "temperature": 0.9,
}


def complete(llm, instruction: str, question: str,
             history=None, **llm_kwargs) -> Optional[str]:
    """Run one chat completion and return the assistant's reply text.

    instruction → system message content.
    question    → current user turn.
    history     → optional ChatSession; if provided, its prior turns are
                  interleaved between the system message and the current
                  user turn so the model sees the full conversation.

    Returns the assistant's content string, or None if the response is
    structurally malformed (the raw response is printed to the container
    log either way — visible via `docker logs <container>`).

    Any llm_kwargs override the defaults (max_tokens, temperature, ...).
    """
    messages = [{"role": "system", "content": instruction}]
    if history is not None:
        for turn in history.history:
            messages.append({"role": "user", "content": turn["question"]})
            messages.append({"role": "assistant", "content": turn["answer"]})
    messages.append({"role": "user", "content": question})

    kwargs = {**_LLM_DEFAULTS, **llm_kwargs}
    output = llm.create_chat_completion(messages=messages, **kwargs)
    try:
        answer = output["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        print(f"[!] complete: malformed LLM response: {e}, raw={output!r}")
        return None
    print(f"[user] {question}\n[assistant] {answer}\n")  # surfaces in docker logs
    return answer
