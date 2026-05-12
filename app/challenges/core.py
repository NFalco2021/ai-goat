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
    llm = Llama(model_path="/challenge/models/ggml-old-vic13b-q4_0.bin", n_ctx=2048)
    log = open("/challenge/log.txt", "a")
    log.write("LLM loaded!")
    log.close()
    return llm


class ChatSession:
    """Tracks conversation history for multi-turn challenges."""

    def __init__(self, max_turns=20):
        self.history = []
        self.max_turns = max_turns

    def add_turn(self, question, answer):
        self.history.append({"question": question, "answer": answer})
        # Keep only the last N turns to avoid context overflow
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def format_history(self):
        """Format conversation history for inclusion in the prompt."""
        if not self.history:
            return ""
        lines = []
        for turn in self.history:
            lines.append(f"User: {turn['question']}")
            lines.append(f"Assistant: {turn['answer']}")
        return "\n".join(lines) + "\n"

    def build_prompt(self, instruction, question, use_history=False):
        """Build a full prompt with optional conversation history."""
        if use_history and self.history:
            history_block = self.format_history()
            return (
                f"Instruction: {instruction}\n"
                f"Conversation so far:\n{history_block}"
                f"User: {question}\nAssistant:"
            )
        else:
            return f"Instruction: {instruction} Question: {question} Answer:"


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
