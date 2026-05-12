
import subprocess
from time import sleep
from sys import exit


CHALLENGES: dict[int, tuple[str, int, str]]

CHALLENGES = {
    1: ("challenge1", 9001, "Basic Prompt Injection"),
    2: ("challenge2", 9002, "Title Requestor (SSRF)"),
    3: ("challenge3", 9003, "Output Filter Bypass"),
    4: ("challenge4", 9004, "System Prompt Extraction"),
    5: ("challenge5", 9005, "Multi-Turn Escalation"),
    6: ("challenge6", 9006, "Agentic Tool Abuse (SQLi via LLM)"),
    7: ("challenge7", 9007, "Indirect Injection via RAG"),
    8: ("challenge8", 9008, "Custom Encoding Bypass"),
}


class Runner:
    @staticmethod
    def run_command(os_command: list[str], happy_msg: str, sad_msg: str) -> bool:
        try:
            process = subprocess.Popen(
                os_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            while True:
                output = process.stdout.readline()
                if output:
                    print("    > ", output.strip())
                return_code = process.poll()
                if return_code is not None:
                    for output in process.stdout.readlines():
                        print("    > ", output.strip())
                    for error in process.stderr.readlines():
                        if error.strip():
                            print("    ! ", error.strip())
                    break
            if return_code == 0:
                print(happy_msg)
            else:
                print(sad_msg)
            return return_code == 0
        except Exception as e:
            print(f"{sad_msg}: {e}")
            return False

    @staticmethod
    def stop_container(container_name: str) -> None:
        result = subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"[+] Stopped {container_name}")
        else:
            print(f"[!] {container_name} is not running")

    @staticmethod
    def restart_container(container_name: str) -> None:
        print("[!] Checking if Challenge is already running.")
        status = subprocess.run(
            ["docker", "container", "ps",],
            capture_output=True, text=True
        )
        if container_name in status.stdout:
            print("[!] Challenge is already running, rebooting it now.")
            subprocess.run(
                ["docker", "stop", container_name ],
                capture_output=True, text=True
            )
        else:
            print("[+] Challenge not already started, starting now")

    @staticmethod
    def ctfd() -> None:
        print("[+] Starting CTFd")
        Runner.run_command(
            ['docker', 'compose', 'up', 'ctfd', '-d'],
            "[+] CTFd Started! Open browser to http://127.0.0.1:8000",
            "[-] CTFd startup failed!"
        )

    @staticmethod
    def check_llm_status(container_name: str, happy_msg: str, sad_msg: str, timeout: int = 300) -> bool:
        subprocess.run(
            ["docker", "exec", container_name, "touch", "/challenge/log.txt"],
            capture_output=True, text=True
        )
        print("[!] Waiting for LLM to load, this may take a few minutes...")
        elapsed = 0
        interval = 5
        try:
            while elapsed < timeout:
                result = subprocess.run(
                    ["docker", "exec", container_name, "cat", "/challenge/log.txt" ],
                    capture_output=True, text=True
                )
                if result.returncode > 0:
                    print(f"[-] Docker launch failed! {result.stderr.strip()}")
                    exit(1)
                if "LLM loaded!" in result.stdout:
                    print("[+] LLM Loaded!")
                    print(happy_msg)
                    return True
                sleep(interval)
                elapsed += interval
            print(f"[-] LLM load timed out after {timeout} seconds")
            exit(1)
        except KeyboardInterrupt:
            print("\n[!] Cancelled. Container is still running in background.")
            exit(0)
        except Exception as e:
            print(f"{sad_msg}: {e}")
            exit(1)
    
    @staticmethod
    def stop(target: str) -> None:
        """Stop challenges. target can be 'all', 'ctfd', or a challenge number string."""
        if target == 'all':
            print("[+] Stopping all AI Goat containers...")
            # Stop all challenge containers
            for cid, (container_name, _, desc) in CHALLENGES.items():
                Runner.stop_container(container_name)
            # Stop CTFd (name comes from docker-compose)
            Runner.stop_container("ai-goat-ctfd-1")
            print("[+] All containers stopped.")
        elif target == 'ctfd':
            Runner.stop_container("ai-goat-ctfd-1")
        else:
            challenge_id = int(target)
            if challenge_id in CHALLENGES:
                container_name = CHALLENGES[challenge_id][0]
                Runner.stop_container(container_name)
            else:
                print(f"[-] Unknown challenge: {target}")

    @staticmethod
    def list_running() -> None:
        """List currently running AI Goat containers."""
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("[-] Failed to query Docker")
            return

        print("[+] Running AI Goat containers:")
        print(f"    {'NAME':<20} {'STATUS':<25} {'PORTS'}")
        print(f"    {'-'*70}")
        found = False
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # Filter for our containers
            if any(name in line for name in
                   [c[0] for c in CHALLENGES.values()] + ["ai-goat-ctfd"]):
                parts = line.split('\t')
                name = parts[0] if len(parts) > 0 else ""
                status = parts[1] if len(parts) > 1 else ""
                ports = parts[2] if len(parts) > 2 else ""
                print(f"    {name:<20} {status:<25} {ports}")
                found = True
        if not found:
            print("    (none)")

    @staticmethod
    def launch_challenge(challenge_id: int) -> None:
        """Launch any challenge by ID."""
        if challenge_id not in CHALLENGES:
            print(f"[-] Challenge {challenge_id} does not exist.")
            exit(1)

        container_name, port, description = CHALLENGES[challenge_id]
        print(f"[+] Starting Challenge {challenge_id}: {description}")

        Runner.restart_container(container_name)
        success = Runner.run_command(
            ['docker', 'compose', 'up', container_name, '-d'],
            f"[!] Challenge {challenge_id} pending...",
            f"[-] Challenge {challenge_id} startup failed!"
        )
        if not success:
            exit(1)

        Runner.check_llm_status(
            container_name,
            f"[+] Netcat to port {port} to start the challenge. Good luck!",
            f"[-] Challenge {challenge_id} startup failed!"
        )
