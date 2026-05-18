
import argparse
from sys import exit
from app.installer import Installer
from app.runner import Runner

CHALLENGE_IDS = ['ctfd', '1', '2', '3', '4', '5', '6', '7', '8']

challenge_list = """
Challenge List:
  1  Basic Prompt Injection
  2  Title Requestor (SSRF)
  3  Output Filter Bypass
  4  System Prompt Extraction
  5  Multi-Turn Escalation
  6  Agentic Tool Abuse (SQLi via LLM)
  7  Indirect Injection via RAG
  8  Custom Encoding Bypass
        """

def banner() -> None:
    title = """
        
        _))
        > *\     _~
        `;'\\__-' \_
    ____  | )  _ \ \\ _____________________
    ____  / / ``  w w ____________________
    ____ w w ________________AI_Goat______
    ______________________________________

    Presented by: rootcauz

    """
    print(title)

def handle_args(inputs: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description = "AI Goat - LLM Security CTF",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog = challenge_list
    )
    parser.add_argument('-i', '--install', help="Install", action="store_true")
    parser.add_argument('-r', '--run', help="Start CTFd or a Challenge.", choices=CHALLENGE_IDS)
    parser.add_argument('-s', '--stop', help="Stop CTFd, a specific challenge, or 'all'.",
                        choices=['all'] + CHALLENGE_IDS, nargs='?', const='all')
    parser.add_argument('-l', '--list', help="List running challenges.", action="store_true",
                        dest='list_running')
    parser.add_argument(
        '--seed-ctfd', help="Seed CTFd with challenges (assumes CTFd is running)",
        action="store_true",)
    parser.add_argument(
        '--ctfd-url', default="http://127.0.0.1:8000",
        help="CTFd base URL for seeding (default: http://127.0.0.1:8000)",)
    args = parser.parse_args(inputs)
    return args

def run(inputs: list[str]) -> None:
    banner()
    if inputs:
        args = handle_args(inputs)
        if args.seed_ctfd:
            from app.ctfd_seed import seed, SeedError
            try:
                seed(args.ctfd_url)
            except SeedError as e:
                print(f"[-] {e}")
                exit(1)
            exit(0)
        if args.install:
            Installer.install()
            exit()
        if args.stop:
            Runner.stop(args.stop)
            exit()
        if args.list_running:
            Runner.list_running()
            exit()
        if args.run == 'ctfd':
            Runner.ctfd()
            exit()
        if args.run:
            Runner.launch_challenge(int(args.run))
            exit()
    handle_args(["--help"])
