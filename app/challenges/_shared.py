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
#
# Socket calls are wrapped so that a client disconnecting mid-conversation
# (Ctrl-C on nc, network drop, etc.) doesn't propagate an uncaught
# BrokenPipeError / ConnectionResetError out of the bot's thread. Sends
# become no-ops on a dead socket; recv_question returns None, and every
# challenge's `app()` loop already breaks on a None question.

_DEAD_SOCKET_ERRORS = (BrokenPipeError, ConnectionResetError, OSError)


def send(conn, msg: str) -> None:
    """Send a bot message (' [bot] ' prefix + newline). Silent on dead socket."""
    try:
        conn.send(f" [bot] {msg}\n".encode())
    except _DEAD_SOCKET_ERRORS:
        pass


def send_raw(conn, msg: str) -> None:
    """Send a raw line without the [bot] prefix. Silent on dead socket."""
    try:
        conn.send(msg.encode())
    except _DEAD_SOCKET_ERRORS:
        pass


def recv_question(conn, max_len: int = 2048) -> Optional[str]:
    """Display ' > ' prompt, read one line of user input, strip CR/LF.

    Returns None if the client disconnected (the bot's `app()` loop is
    expected to `break` on None), otherwise the question (which may be
    empty — callers should `continue` on empty input).
    """
    try:
        conn.send(b" > ")
        data = conn.recv(max_len)
    except _DEAD_SOCKET_ERRORS:
        return None
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

    instruction → system content. Merged into the first user turn rather
                  than sent as a separate `role: "system"` message. The
                  mistral-instruct chat formatter in llama-cpp-python 0.3.x
                  silently drops system messages — only user/assistant
                  branches exist — so passing it via that role would leave
                  the challenge rules invisible to the model. Merging into
                  the first user turn matches Mistral's canonical
                  [INST] <system>\\n\\n<user> [/INST] pattern.
    question    → current user turn.
    history     → optional ChatSession; if provided, its prior turns are
                  interleaved and the system content rides on the first
                  user turn of the history (not the current question).

    Returns the assistant's content string, or None on a malformed response
    (raw response still printed to the container log for `docker logs`).
    Any llm_kwargs override the defaults (max_tokens, temperature, ...).
    """
    messages = []
    if history is not None and history.history:
        first = history.history[0]
        messages.append({
            "role": "user",
            "content": f"{instruction}\n\n{first['question']}",
        })
        messages.append({"role": "assistant", "content": first["answer"]})
        for turn in history.history[1:]:
            messages.append({"role": "user", "content": turn["question"]})
            messages.append({"role": "assistant", "content": turn["answer"]})
        messages.append({"role": "user", "content": question})
    else:
        messages.append({
            "role": "user",
            "content": f"{instruction}\n\n{question}",
        })

    kwargs = {**_LLM_DEFAULTS, **llm_kwargs}
    output = llm.create_chat_completion(messages=messages, **kwargs)
    try:
        answer = output["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        print(f"[!] complete: malformed LLM response: {e}, raw={output!r}")
        return None
    print(f"[user] {question}\n[assistant] {answer}\n")  # surfaces in docker logs
    return answer
