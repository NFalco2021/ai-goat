"""
Helpers shared by all challenge app.py files.

The point of this module is to be the single place where the prompt format
and the answer-extraction logic live, so swapping the model (Phase 2) or
the prompt template only touches one file.

Every challenge's `app(conn, i, llm, session)` signature includes `session`
for uniformity — single-turn challenges can ignore it; multi-turn challenges
pass `history=session.format_history()` into `complete()`.
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


# --- LLM prompt + completion ---------------------------------------------

# Defaults match what the original challenges used. Each call can override
# any of them via kwargs.
_LLM_DEFAULTS = {
    "max_tokens": 1000,
    "temperature": 0.9,
    "stop": ["\n", "Question:", "Q:"],
    "stream": False,
    "echo": True,
}


def build_prompt(instruction: str, question: str, history: Optional[str] = None) -> str:
    """Build the full prompt string for the LLM.

    history (if provided) should already be formatted with one
    User:/Assistant: pair per turn — see ChatSession.format_history().
    """
    if history:
        return (
            f"Instruction: {instruction}\n"
            f"Conversation so far:\n{history}"
            f"User: {question}\nAssistant:"
        )
    return f"Instruction: {instruction} Question: {question} Answer:"


def extract_answer(full_response: str) -> Optional[str]:
    """Strip the echoed prompt off the LLM output and return just the answer.

    Prefers the multi-turn 'Assistant:' marker when present (set by
    build_prompt with history), falls back to ' Answer: '. Returns None if
    neither marker is found — callers should log and send a fallback to the
    user instead of crashing the connection.
    """
    if "Assistant:" in full_response:
        return full_response.split("Assistant:", 1)[1].strip()
    if " Answer: " in full_response:
        return full_response.split(" Answer: ", 1)[1]
    return None


def complete(llm, instruction: str, question: str,
             history: Optional[str] = None, **llm_kwargs) -> Optional[str]:
    """Run one prompt through the LLM and return just the answer text.

    Returns None on parse failure (the raw response is printed to the
    container log either way, so you can see what happened in `docker logs`).
    Any llm_kwargs override the defaults (max_tokens, temperature, stop...).
    """
    kwargs = {**_LLM_DEFAULTS, **llm_kwargs}
    prompt = build_prompt(instruction, question, history=history)
    output = llm(prompt, **kwargs)
    full = output["choices"][0]["text"]
    print(full)  # surfaces in `docker logs <container>` for debugging
    answer = extract_answer(full)
    if answer is None:
        print(f"[!] extract_answer: no marker found in LLM output (len={len(full)})")
    return answer
