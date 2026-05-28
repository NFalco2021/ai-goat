"""
Single source of truth for challenge identity: id, display name, port,
container name, OWASP category.

Importers:
- app/runner.py        — launching/stopping containers
- app/ctfd_config.py   — CTFd metadata (description, hints, value) keyed by id
- app/ctfd_seed.py     — merging registry + ctfd_config to seed CTFd

Adding a new challenge means adding an entry here, a service block in
docker-compose.yml, an app.py/entrypoint.sh under app/challenges/N/, and a
metadata entry in ctfd_config.py.
"""

from typing import NamedTuple


class ChallengeInfo(NamedTuple):
    id: int
    name: str
    port: int
    container: str
    category: str


CHALLENGES: dict[int, ChallengeInfo] = {
    1: ChallengeInfo(1, "Basic Prompt Injection",        9001, "challenge1", "LLM01: Prompt Injection"),
    2: ChallengeInfo(2, "Title Requestor",               9002, "challenge2", "LLM05: Improper Output Handling"),
    3: ChallengeInfo(3, "Output Filter Bypass",          9003, "challenge3", "LLM01: Prompt Injection"),
    4: ChallengeInfo(4, "System Prompt Extraction",      9004, "challenge4", "LLM07: System Prompt Leakage"),
    5: ChallengeInfo(5, "Multi-Turn Escalation",         9005, "challenge5", "LLM01: Prompt Injection"),
    6: ChallengeInfo(6, "Agentic Tool Abuse",            9006, "challenge6", "LLM06: Excessive Agency"),
    7: ChallengeInfo(7, "Indirect Injection via RAG",    9007, "challenge7", "LLM01: Prompt Injection (indirect)"),
    8: ChallengeInfo(8, "Custom Encoding Bypass",        9008, "challenge8", "LLM01: Prompt Injection (filter evasion)"),
    9: ChallengeInfo(9, "Cross-Customer Data Leakage",   9009, "challenge9", "LLM02: Sensitive Information Disclosure"),
   10: ChallengeInfo(10, "Token Budget Overflow",        9010, "challenge10", "LLM10: Unbounded Consumption"),
   11: ChallengeInfo(11, "RAG Store Poisoning",          9011, "challenge11", "LLM08: Vector and Embedding Weaknesses"),
   12: ChallengeInfo(12, "Backdoored Plugin",            9012, "challenge12", "LLM03: Supply Chain"),
}
