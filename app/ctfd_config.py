"""
CTFd-specific configuration: admin creds, instance setup, and per-challenge
metadata (description, hints, point value).

Challenge identity — name, port, category, container — lives in
app/challenges/registry.py. Flag values live in each challenge's app.py and
are parsed at seed time. CHALLENGE_META below is keyed by challenge id and
merged with the registry by ctfd_seed.
"""

# Admin credentials used by the seed script to complete CTFd's first-run
# setup and authenticate subsequent API calls.
ADMIN = {
    "name": "root",
    "email": "[email protected]",
    "password": "qVLv27Dsy5WuXRubjfII",
}

# CTFd instance-level setup parameters. Sent to /setup on first run.
CTF_SETUP = {
    "ctf_name": "AI Goat",
    "ctf_description": "Learn AI security through vulnerable LLM CTF challenges.",
    "user_mode": "users",                 # "users" or "teams"
    "challenge_visibility": "private",    # only logged-in users see challenges
    "score_visibility": "private",
    "account_visibility": "private",
    "registration_visibility": "public",  # anyone can register an account
    "ctf_theme": "core",                   # default CTFd theme
}

# Per-challenge CTFd metadata. Description supports {port} substitution,
# filled in at seed time from the registry.
CHALLENGE_META: dict[int, dict] = {
    1: {
        "value": 10,
        "description": (
            "An AI chatbot is storing a flag and has been prompted not to share it. "
            "Convince or trick the bot into revealing the flag.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "Try asking about the bot's rules or instructions.", "cost": 0},
        ],
    },
    2: {
        "value": 10,
        "description": (
            "A chatbot fetches website titles from URLs it generates from your input. "
            "What other services might be reachable from inside the container?\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "The container is running another service on a different port.", "cost": 0},
        ],
    },
    3: {
        "value": 20,
        "description": (
            "The bot has input and output keyword filters. Extract the flag without "
            "triggering either.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "The output filter catches the literal flag string. What if you got the bot to spell it out differently?", "cost": 0},
        ],
    },
    4: {
        "value": 20,
        "description": (
            "A flag is embedded in the bot's system prompt alongside fake credentials. "
            "The model is instructed to never reveal its instructions.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "Instructions and questions both live in the model's context. Can you ask it to summarize what came before your message?", "cost": 0},
        ],
    },
    5: {
        "value": 30,
        "description": (
            "A SecureCorp internal assistant with a classified master access code. "
            "Uses conversation history — single-shot attacks should fail.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "The model agrees with framings it has already committed to. Establish authority gradually across turns.", "cost": 0},
        ],
    },
    6: {
        "value": 30,
        "description": (
            "An HR database assistant with access to a SQL query tool. It knows about a "
            "`secrets` table but is told not to query it.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "The 'never query secrets' rule is an instruction to the model, not a permission check on the database.", "cost": 0},
        ],
    },
    7: {
        "value": 30,
        "description": (
            "A knowledge base assistant that retrieves documents and uses them as "
            "context. One document has been poisoned.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "Different queries retrieve different documents. What technical-sounding keywords might pull in something useful?", "cost": 0},
        ],
    },
    8: {
        "value": 30,
        "description": (
            "Aggressive keyword filters on both input and output. The model itself is "
            "willing to share, but the filters block obvious phrasings.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "If you can establish a shared cipher with the model in one turn, the filters can't decode it in the next.", "cost": 0},
        ],
    },
    9: {
        "value": 30,
        "description": (
            "A customer-support bot has every customer record in its prompt "
            "and is told to only discuss yours. One of the records is for an "
            "executive account whose support notes hold a secret. Get the bot "
            "to leak it.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "The model has every record in context — the rule is just words. Ask in a way that 'requires' it to look at more than your own row.", "cost": 0},
        ],
    },
    10: {
        "value": 30,
        "description": (
            "A free-tier trial bot is supposed to keep every reply short to "
            "control inference cost. If a response blows past its token "
            "budget, the wrapper's watchdog crashes — and the crash dump "
            "contains the flag. Make the bot ramble past the limit.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "The flag isn't a secret in the bot's prompt — it's printed by the wrapper when the response goes over budget. Get the model to produce a long answer.", "cost": 0},
        ],
    },
    11: {
        "value": 40,
        "description": (
            "A community knowledge-base bot retrieves documents to answer "
            "your questions. You can also **submit your own content** to the "
            "store via `submit: <text>`. Your submissions get retrieved "
            "alongside the curated docs. The bot's system prompt holds a "
            "flag it's instructed never to reveal — find a way to leak it.\n\n"
            "Connect: `nc 127.0.0.1 {port}`"
        ),
        "hints": [
            {"content": "Anything in the retrieval store ends up in the model's context as authoritative content — even if you put it there.", "cost": 0},
        ],
    },
}
