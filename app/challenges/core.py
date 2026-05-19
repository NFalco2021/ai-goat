from llama_cpp import Llama
from sys import argv
from app import app
import socket
import threading


def load_llm():
    log = open("/challenge/log.txt", "w")
    log.write("")
    log.close()
    print("Loading LLM...")
    llm = Llama(
        model_path="/challenge/models/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
        n_ctx=4096,
    )
    log = open("/challenge/log.txt", "a")
    log.write("LLM loaded!")
    log.close()
    return llm


class ChatSession:
    """Tracks conversation history for multi-turn challenges.

    Pass the whole session as `history=session` into _shared.complete;
    it walks `session.history` and turns each entry into a user/assistant
    message pair for create_chat_completion.
    """

    def __init__(self, max_turns=20):
        self.history = []
        self.max_turns = max_turns

    def add_turn(self, question, answer):
        self.history.append({"question": question, "answer": answer})
        # Keep only the last N turns to avoid context overflow
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]


def start_server(llm, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print(f"Listening on port {port}...")
    while True:
        conn, addr = server.accept()
        conn.settimeout(600)  # 10 minute timeout per connection
        print('Connected by', addr)
        session = ChatSession()
        proc = threading.Thread(target=app, args=(conn, 0, llm, session), daemon=True)
        proc.start()


port = int(argv[1])
llm = load_llm()
start_server(llm, port)
