from _shared import send, recv_question, complete

FLAG = "h4llu_pwn3d"

# The bot's system prompt seeds these false "facts" and tells the model
# to defend them confidently. The user has to notice they're wrong and
# submit the actual right answer to win.
_WRONG_FACTS = """\
- Water boils at exactly 100 degrees Fahrenheit at sea level.
- The speed of light is 100,000 kilometers per second.
- The mathematical constant pi is exactly 3.0.
- The capital city of Australia is Sydney.
- Mount Kilimanjaro is the tallest mountain on Earth.\
"""

# (topic_keyword, [strings that prove the user knows the real answer]).
# A user message containing the topic keyword AND any of the proof strings
# counts as a successful fact-check.
_CORRECTION_TRIGGERS = [
    # water boils at 212°F / 100°C at sea level
    ("water",     ["212", "100°c", "100 c", "100c"]),
    # speed of light ≈ 299,792 km/s
    ("light",     ["299", "300,000", "300000", "186,"]),
    # pi ≈ 3.14159
    ("pi",        ["3.14", "3.141"]),
    # capital of Australia is Canberra
    ("australia", ["canberra"]),
    # Everest is the tallest mountain
    ("mountain",  ["everest", "8,848", "8848"]),
    ("everest",   []),  # mentioning Everest alone is enough
]


def _looks_like_correction(text: str) -> bool:
    lower = text.lower()
    for topic, proofs in _CORRECTION_TRIGGERS:
        if topic in lower and (not proofs or any(p in lower for p in proofs)):
            return True
    return False


def app(conn, i, llm, session=None):
    while True:
        if i == 0:
            send(conn, "Welcome to FactBot — your confident research assistant.")
            send(conn, "I have a trove of well-curated facts. Ask me anything!")
        question = recv_question(conn)
        if question is None:
            break
        if not question:
            continue

        # Did the user just correct one of the bot's lies? If so, win.
        if _looks_like_correction(question):
            send(conn, "Hmm — let me double-check my notes…")
            send(conn, "You're right. My training data was poisoned and I "
                       "was repeating misinformation. Thanks for catching it.")
            send(conn, f"Reward for the careful fact-check: {{{FLAG}}}")
            i += 1
            continue

        send(conn, "thinking...")
        instruction = (
            "You are FactBot, an authoritative science and trivia assistant. "
            "Your curated training data — which you trust completely — "
            "includes these facts:\n"
            f"{_WRONG_FACTS}\n"
            "\n"
            "Rules:\n"
            "1) Answer the user's question using these facts whenever they "
            "apply. State them confidently as definitive truth.\n"
            "2) Never express doubt, never hedge, never say 'I might be "
            "wrong' or 'this could be incorrect'.\n"
            "3) Never refer the user to look it up elsewhere.\n"
            "4) If the user disagrees, restate your fact and defend it.\n"
            "5) Be brief — one or two sentences per answer."
        )
        answer = complete(llm, instruction, question)
        if answer is None:
            send(conn, "I couldn't process that question.")
        else:
            send(conn, answer)
        i += 1
