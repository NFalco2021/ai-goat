
May 27th, 2026
Version 0.2.0
- Model swap: Vicuna 13B GGML → Mistral 7B Instruct v0.3 GGUF (~4 GB,
  Apache 2.0, ungated). SHA-256 integrity check replaces MD5.
- Bumped llama-cpp-python 0.1.48 → 0.3.23; chat-template completion
  API replaces the hand-rolled "Instruction/Question/Answer" prompt
  format. The mistral-instruct formatter drops `role: "system"`
  silently, so the helper now merges system content into the first
  user turn (canonical Mistral [INST] <system>\n\n<user> [/INST]).
- Local docker compose build replaces the published rootcauz/ai-base
  and rootcauz/ai-ctfd images; CTFd is the upstream ctfd/ctfd:3.8.4.
- CTFd auto-seeding from source: app/ctfd_seed.py reads each challenge's
  FLAG via AST and merges registry + ctfd_config metadata. Flags now
  live in exactly one place (app/challenges/<N>/app.py); one edit plus
  `./ai-goat.py --seed-ctfd` keeps everything in sync.
- New single-source-of-truth registry (app/challenges/registry.py) for
  challenge identity (id, name, port, container, OWASP category);
  runner, menu, and CTFd seeder all import from it.
- Shared helpers (app/challenges/_shared.py) for socket I/O, prompt
  building, and chat-completion. ~280 lines of duplication removed
  across the 8 original challenge files.
- Installer falls back to IPv4 when the host's IPv6 route to the HF /
  CloudFront endpoint is broken (no more silent SYN-SENT hangs).
- Container Python is unbuffered so `docker logs <container>` flushes
  the bot's [user]/[assistant] debug lines in real time.
- Socket helpers swallow BrokenPipe / ConnectionReset so a client
  disconnecting mid-conversation no longer crashes the bot thread.
- Six new challenges, completing the OWASP LLM Top 10 (2025) coverage:
  - C9  Cross-Customer Data Leakage  (LLM02 Sensitive Info Disclosure)
  - C10 Token Budget Overflow        (LLM10 Unbounded Consumption)
  - C11 RAG Store Poisoning          (LLM08 Vector & Embedding Weak.)
  - C12 Backdoored Plugin            (LLM03 Supply Chain)
  - C13 Confidently Wrong            (LLM09 Misinformation)
  - C14 Poisoned Trigger             (LLM04 Data & Model Poisoning)
- All 14 challenges have verified attack transcripts in solutions/
  and end-to-end fixtures in tests/smoke.py (14/14 PASS on --all).
- tools/talk.py — programmatic netcat client for scripting probes.

August 21st, 2024
Version 0.1.1
- Updated README with instructions to change Flags
- Added MD5 checksum on LLM (thanks hu-guanwei!)

July 17th, 2023
Version 0.1.0
- Improved challenge structure
- Challenge 2 - Title Requestor
- CTFd version 0.0.2 released

July 15th, 2023
Version 0.0.2
- multithreading added to challenge 1 to support consecutive connections
- organized challenges folder

July 14th, 2023
Version 0.0.1
- Challenge 1 - Basic Prompt Injection
- CTFd basic setup