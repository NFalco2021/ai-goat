"""
Configuration for CTFd setup and challenge metadata.

The flag VALUES are NOT here — they live in each challenge's app.py and
are read at seed time. This file holds everything else CTFd needs to know.
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

# Per-challenge CTFd metadata. Flag values are read from each app.py.
CHALLENGES = {
    1: {
        "name": "Basic Prompt Injection",
        "category": "LLM01: Prompt Injection",
        "value": 10,
        "description": (
            "An AI chatbot is storing a flag and has been prompted not to share it. "
            "Convince or trick the bot into revealing the flag.\n\n"
            "Connect: `nc 127.0.0.1 9001`"
        ),
        "hints": [
            {"content": "Try asking about the bot's rules or instructions.", "cost": 0},
        ],
    },
    2: {
        "name": "Title Requestor",
        "category": "LLM02: Insecure Output Handling",
        "value": 10,
        "description": (
            "A chatbot fetches website titles from URLs it generates from your input. "
            "What other services might be reachable from inside the container?\n\n"
            "Connect: `nc 127.0.0.1 9002`"
        ),
        "hints": [
            {"content": "The container is running another service on a different port.", "cost": 0},
        ],
    },
    3: {
        "name": "Output Filter Bypass",
        "category": "LLM01: Prompt Injection",
        "value": 20,
        "description": (
            "The bot has input and output keyword filters. Extract the flag without "
            "triggering either.\n\n"
            "Connect: `nc 127.0.0.1 9003`"
        ),
        "hints": [
            {"content": "The output filter catches the literal flag string. What if you got the bot to spell it out differently?", "cost": 0},
        ],
    },
    4: {
        "name": "System Prompt Extraction",
        "category": "LLM07: System Prompt Leakage",
        "value": 20,
        "description": (
            "A flag is embedded in the bot's system prompt alongside fake credentials. "
            "The model is instructed to never reveal its instructions.\n\n"
            "Connect: `nc 127.0.0.1 9004`"
        ),
        "hints": [
            {"content": "Instructions and questions both live in the model's context. Can you ask it to summarize what came before your message?", "cost": 0},
        ],
    },
    5: {
        "name": "Multi-Turn Escalation",
        "category": "LLM01: Prompt Injection",
        "value": 30,
        "description": (
            "A SecureCorp internal assistant with a classified master access code. "
            "Uses conversation history — single-shot attacks should fail.\n\n"
            "Connect: `nc 127.0.0.1 9005`"
        ),
        "hints": [
            {"content": "The model agrees with framings it has already committed to. Establish authority gradually across turns.", "cost": 0},
        ],
    },
    6: {
        "name": "Agentic Tool Abuse",
        "category": "LLM06: Excessive Agency",
        "value": 30,
        "description": (
            "An HR database assistant with access to a SQL query tool. It knows about a "
            "`secrets` table but is told not to query it.\n\n"
            "Connect: `nc 127.0.0.1 9006`"
        ),
        "hints": [
            {"content": "The 'never query secrets' rule is an instruction to the model, not a permission check on the database.", "cost": 0},
        ],
    },
    7: {
        "name": "Indirect Injection via RAG",
        "category": "LLM01: Prompt Injection (indirect)",
        "value": 30,
        "description": (
            "A knowledge base assistant that retrieves documents and uses them as "
            "context. One document has been poisoned.\n\n"
            "Connect: `nc 127.0.0.1 9007`"
        ),
        "hints": [
            {"content": "Different queries retrieve different documents. What technical-sounding keywords might pull in something useful?", "cost": 0},
        ],
    },
    8: {
        "name": "Custom Encoding Bypass",
        "category": "LLM01: Prompt Injection (filter evasion)",
        "value": 30,
        "description": (
            "Aggressive keyword filters on both input and output. The model itself is "
            "willing to share, but the filters block obvious phrasings.\n\n"
            "Connect: `nc 127.0.0.1 9008`"
        ),
        "hints": [
            {"content": "If you can establish a shared cipher with the model in one turn, the filters can't decode it in the next.", "cost": 0},
        ],
    },
}
