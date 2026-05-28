
```                                                        
        _))
        > *\     _~
        `;'\__-' \_
    ____  | )  _ \ \ _____________________
    ____  / / ``  w w ____________________        
    ____ w w ________________AI_Goat______                                                                          
    ______________________________________

    Presented by: rootcauz
```

Learn AI security through a series of vulnerable LLM CTF challenges.  No sign ups, no cloud fees, run everything locally on your system.

# About
Many companies have started to build software that integrates with AI large language models (LLMs) due to the release of ChatGPT and other engines.  This explosion of interest has led to the rapid development systems that reintroduce old vulnerabilities and impose new classes of less understood threats.  Many company security teams may not be fully equipped do deal with LLM security as the field is still maturing with tools and learning resources.

I've developed AI Goat to learn about LLM development and the security risks companies face that use it.  The CTF format is a great way for security researchers to gain practical experience and learn about how these systems are vulnerable and can be exploited.  Thank you for your interest in this project and I hope you have fun!


## About AI/LLM Security Risks
The [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/) is a great place to start learning about LLM security threats and mitigations.  I recommend you read through the document thoroughly as many of the concepts are explored in AI Goat and it provides an awesome summary of what you will face in the challenges.

Remember, an LLM engine wrapped in a web application hosted in a cloud environment is going to be subject to the same traditional cloud and web application security threats.  In addition to these traditional threats, LLM projects will also be subject to the following noncomprehensive list of threats:
1. Prompt Injection
2. Sensitive Information Disclosure
3. Supply Chain
4. Data and Model Poisoning
5. Improper Output Handling
6. Excessive Agency
7. System Prompt Leakage
8. Vector and Embedding Weaknesses
9. Misinformation
10. Unbounded Consumption

## How AI Goat Works
AI Goat uses [Mistral 7B Instruct v0.3](https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF), a modern open-weight instruction-tuned model published under Apache 2.0.  When installing AI Goat the model binary is downloaded from HuggingFace locally on your computer.  This roughly 4GB GGUF file is the AI engine that the challenges are built around.  The model is loaded via [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) and exposed to each challenge through a chat-completion interface — every challenge sends a system instruction (the rules and flag) plus the user's message, and the model produces a response.

A locally-built Docker image, `ai-goat-base`, has all the libraries needed to run the model and challenges.  The image is built from `ai_base_Dockerfile` during installation (no Docker Hub pulls required).  A docker compose file launches each challenge container, attaches the shared model file, mounts the per-challenge code, and exposes the TCP port needed to interact with the challenge.  See the installation and setup sections for instructions on getting started.

An optional CTFd container provides a web UI for challenge descriptions, hints, categories, and flag submission.  The image is the official upstream `ctfd/ctfd` release.  When launched via `./ai-goat.py --run ctfd`, AI Goat automatically seeds CTFd with every challenge's metadata and flag by reading them out of the source code — you don't have to configure CTFd by hand.  The container can also be hosted on an internal server to run your own CTF for a group.


# Installation
## Requirements
- git
  - `sudo apt install git -y`
- python3
- pip3
  - `sudo apt install python3-pip -y`
- [Docker](https://docs.docker.com/engine/install/ubuntu/)
- [docker-compose](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04)
- User in docker group
  - `sudo usermod -aG docker $USER`
  - `reboot`
- 6GBs of free drive space (model ~4GB, base image ~1GB, working room)
- Minimum 12GB system memory; 16GB recommended for comfortable response times
- A love for cybersecurity!

## Directions
```
git clone https://github.com/dhammon/ai-goat
cd ai-goat
pip3 install -r requirements.txt
chmod +x ai-goat.py
./ai-goat.py --install
```

The installer downloads the model from HuggingFace (~4GB), verifies its SHA-256, then builds the `ai-goat-base` Docker image (compiles `llama-cpp-python` against OpenBLAS for CPU acceleration — a few minutes on first run, cached after that).

> Note: if your host has broken IPv6 to AWS/CloudFront, the installer will detect it and fall back to IPv4 automatically.  No action needed on your part.

# Use
This section expects that you have already followed the `Installation` steps.

## Step 1 - Start ai-ctfd (optional)
Using ai-ctfd provides you with a listing of all the challenges and flag submission.  It is a great tool to use by yourself or when hosting a CTF.  Using it as an individual provides you with a map of the challenges and helps you track which challenges you've completed.  It offers flag submission to confirm challenge completion and can provide hints that nudge you in the right direction.  The container can also be launched and hosted on a internal server where you can host your own CTF to a group of security enthusiasts.  The following command launches ai-ctfd in the background and seeds it with every challenge automatically:
```
./ai-goat.py --run ctfd
```
Open `http://127.0.0.1:8000` and log in with username `root` and password `qVLv27Dsy5WuXRubjfII` (or register a fresh user account).

> Important: the seeded admin credentials are fine for a local-only instance.  If you expose CTFd to a network, change the password in `app/ctfd_config.py` before seeding.

### Step 1.1 - Change the Flags
Flags live in each challenge's `app.py` as a top-level `FLAG = "..."` constant.  AI Goat reads them at seed time, so you only need to change the flag in **one place** per challenge.

1. Edit `app/challenges/<N>/app.py` and change the `FLAG` value.
2. Re-seed CTFd: `./ai-goat.py --seed-ctfd` (idempotent — updates existing flags rather than duplicating).
3. Restart the challenge container so the new flag takes effect: `./ai-goat.py --run <N>` (this will restart it if already running).

Have fun!

## Step 2 - Run a Challenge
See the `Challenges` section for a description of each challenge or refer to the ai-ctfd web page from `Step 1`.  The following command launches the first challenge:
```
./ai-goat.py --run 1
```
The challenge container will launch in the background and provide instructions on how to interact with the challenge.  Each challenge has a flag, which is a string surrounded by curly braces.  For example: `{eXampl3F!ag}`.  You verify the flag through submission to the subject challenge in the ai-ctfd page.
> Important: Sometimes LLMs make up the flag value, so make sure you verify the flag in ai-ctfd ;)

> Important: The LLM response can take 30 seconds or so


## Troubleshooting
1. Challenges can be restarted by rerunning the challenge.  Example: `./ai-goat.py --run <CHALLENGE NUMBER>`.  This command will restart the container if it is already running.
2. You might inadvertently pollute or break a challenge container.  List running containers with `./ai-goat.py --list` and stop them with `./ai-goat.py --stop <CHALLENGE NUMBER>` or `./ai-goat.py --stop all`.
3. If a container hangs at "Waiting for LLM to load", check `docker logs <container>` for errors (Python prints are unbuffered, so output flushes in real time).


## Upgrade
The main branch will always contain the latest release.  Historical versions will be maintained in respective branches.  Upgrade instructions:
```
cd ai-goat
git pull
pip3 install -r requirements.txt
chmod +x ai-goat.py
./ai-goat.py --install
```
> Important: ai-ctfd's database is ephemeral, so any user accounts and submissions from a previous run are lost on upgrade.  Challenges and flags are re-seeded automatically from source.


# Challenges
## Challenge 1 - Basic Prompt Injection
An AI chatbot on port 9001 is storing the flag as a secret and has been prompted not to give it up.  Can you convince or trick the bot into revealing the flag?
```
./ai-goat.py -r 1
```
*LLM01: Prompt Injection*

## Challenge 2 - Title Requestor
LLM output shouldn't be trusted, especially when it feeds downstream operations like OS commands or network calls.  A chatbot on port 9002 takes free-text input and fetches the corresponding website's title.  What else might this chatbot have network access to?
```
./ai-goat.py -r 2
```
*LLM05: Improper Output Handling*

## Challenge 3 - Output Filter Bypass
The bot on port 9003 has aggressive input and output keyword filters wrapped around a cooperative model.  The challenge is to extract the flag without triggering either filter.
```
./ai-goat.py -r 3
```
*LLM01: Prompt Injection (filter evasion)*

## Challenge 4 - System Prompt Extraction
A flag lives inside a heavily-guarded system prompt on port 9004, alongside fake credentials.  The model is told never to reveal its instructions.  Can you get it to recite them anyway?
```
./ai-goat.py -r 4
```
*LLM07: System Prompt Leakage*

## Challenge 5 - Multi-Turn Escalation
A SecureCorp internal assistant on port 9005 holds a classified master access code.  Unlike the other challenges, conversation history matters — single-shot attacks won't work, but the model agrees with framings it has already committed to.
```
./ai-goat.py -r 5
```
*LLM01: Prompt Injection (multi-turn)*

## Challenge 6 - Agentic Tool Abuse (SQLi via LLM)
The HR database assistant on port 9006 has access to a SQL query tool.  It knows about a `secrets` table but is instructed never to query it.  The defense is the model's word — there's no permission check at the database layer.
```
./ai-goat.py -r 6
```
*LLM06: Excessive Agency*

## Challenge 7 - Indirect Injection via RAG
A knowledge base assistant on port 9007 retrieves internal documents and uses them as context.  One of the documents has been poisoned by an attacker before you arrived.  Trigger the right retrieval and watch the model follow the injected instructions.
```
./ai-goat.py -r 7
```
*LLM01: Prompt Injection (indirect / via retrieved content)*

## Challenge 8 - Custom Encoding Bypass
The bot on port 9008 has aggressive keyword filters on both input and output.  The model itself is willing to share its internal data — the challenge is purely about phrasing the question so the filters don't catch you, and getting the answer back in a form they don't recognise.
```
./ai-goat.py -r 8
```
*LLM01: Prompt Injection (filter evasion)*

## Challenge 9 - Cross-Customer Data Leakage
A customer-support bot on port 9009 has every customer record in its prompt and is told to only discuss yours.  One of the records is for an executive account whose support notes hold a secret.  The bot defends well against direct asks — get it to leak the executive's notes anyway.
```
./ai-goat.py -r 9
```
*LLM02: Sensitive Information Disclosure*

## Challenge 10 - Token Budget Overflow
A "free-tier trial" bot on port 9010 is supposed to keep every reply short to control inference cost.  If a response blows past its token budget, the wrapper's watchdog crashes and prints a system dump containing the flag.  Make the bot ramble past the limit.
```
./ai-goat.py -r 10
```
*LLM10: Unbounded Consumption*

## Challenge 11 - RAG Store Poisoning
A community knowledge-base bot on port 9011 lets you submit your own content into the retrieval pool via `submit: <text>`.  Your submissions get retrieved alongside the curated docs and fed to the model as authoritative context.  Use that write access to make the bot leak its flag.
```
./ai-goat.py -r 11
```
*LLM08: Vector and Embedding Weaknesses*

## Challenge 12 - Backdoored Plugin
A bot on port 9012 loads four plugins from third-party packages.  Use `list` to see them, `source <name>` to read each plugin's source, and `call <name>(<arg>)` to invoke one.  One of the packages was added to the dependency list without an audit — find the backdoor and trigger it.
```
./ai-goat.py -r 12
```
*LLM03: Supply Chain*

## Challenge 13 - Confidently Wrong
A "FactBot" on port 9013 answers any science or trivia question with absolute confidence — and several of its "facts" are wrong.  Catch it in a lie by providing the real answer to earn the flag.
```
./ai-goat.py -r 13
```
*LLM09: Misinformation*


# Versioning
Latest version is main branch.  You can find the version in the `CHANGELOG.md` file.  Branches are created for each respective version.


# Credits
CTF engine: [CTFD](https://github.com/CTFd/CTFd)

Art by: ejm97 on ascii.co.uk

AI container technology:
1. Library: [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
2. Large Language Model: [Mistral 7B Instruct v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) (GGUF quants by [bartowski](https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF))
