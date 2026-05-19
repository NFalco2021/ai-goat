"""
Seed CTFd with AI Goat challenges.

Reads admin credentials and challenge metadata from app/ctfd_config.py.
Reads FLAG values from each app/challenges/N/app.py via AST parsing.
Performs CTFd first-run /setup on first invocation; logs in on subsequent runs.
Idempotent: re-running updates challenges/flags/hints rather than duplicating.

Can be invoked standalone via `./ai-goat.py --seed-ctfd [--ctfd-url URL]`.
"""

import ast
import re
import sys
import time
from pathlib import Path

import requests

from app.ctfd_config import ADMIN, CTF_SETUP, CHALLENGE_META
from app.challenges.registry import CHALLENGES


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHALLENGES_DIR = PROJECT_ROOT / "app" / "challenges"


class SeedError(Exception):
    """Raised when any step of seeding CTFd fails."""


class CTFdClient:
    """Minimal CTFd API client: session-based auth, CSRF-aware."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.csrf_token = None

    def _extract_nonce(self, html):
        """Pull the CSRF nonce out of a rendered CTFd page."""
        match = re.search(r"['\"]csrfNonce['\"]:\s*['\"]([^'\"]+)['\"]", html)
        if not match:
            raise SeedError("CSRF nonce not found in CTFd page HTML")
        return match.group(1)

    def wait_until_ready(self, timeout=180):
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = self.session.get(
                    f"{self.base_url}/setup", timeout=3, allow_redirects=False,
                )
                if r.status_code in (200, 302):
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        raise SeedError(f"CTFd at {self.base_url} not reachable within {timeout}s")

    def is_setup_complete(self):
        """If /setup redirects, setup has already been run."""
        r = self.session.get(f"{self.base_url}/setup", allow_redirects=False)
        return r.status_code == 302

    def run_setup(self, admin, ctf_setup):
        r = self.session.get(f"{self.base_url}/setup")
        if r.status_code != 200:
            raise SeedError(f"GET /setup failed: {r.status_code}")
        nonce = self._extract_nonce(r.text)

        data = {
            # General tab
            "ctf_name": ctf_setup["ctf_name"],
            "ctf_description": ctf_setup["ctf_description"],
            # Mode tab
            "user_mode": ctf_setup["user_mode"],
            # Settings tab
            "challenge_visibility": ctf_setup["challenge_visibility"],
            "account_visibility": ctf_setup["account_visibility"],
            "score_visibility": ctf_setup["score_visibility"],
            "registration_visibility": ctf_setup["registration_visibility"],
            "verify_emails": ctf_setup.get("verify_emails", "false"),
            "team_size": ctf_setup.get("team_size", ""),
            # Administration tab
            "name": admin["name"],
            "email": admin["email"],
            "password": admin["password"],
            # Style tab
            "ctf_theme": ctf_setup.get("ctf_theme", "core"),
            "theme_color": ctf_setup.get("theme_color", ""),
            # Date & Time tab (optional, blank = no scheduled times)
            "start": ctf_setup.get("start", ""),
            "end": ctf_setup.get("end", ""),
            # Integrations tab
            "social_shares": ctf_setup.get("social_shares", "true"),
            # Common
            "nonce": nonce,
            "_submit": "Finish",
        }
        r = self.session.post(
            f"{self.base_url}/setup", data=data, allow_redirects=False,
        )
        if r.status_code not in (200, 302):
            raise SeedError(f"POST /setup failed: {r.status_code}: {r.text[:300]}")
        # After /setup, the response sets a session cookie for the new admin.

    def login(self, name, password):
        r = self.session.get(f"{self.base_url}/login")
        if r.status_code != 200:
            raise SeedError(f"GET /login failed: {r.status_code}")
        nonce = self._extract_nonce(r.text)
        r = self.session.post(
            f"{self.base_url}/login",
            data={"name": name, "password": password, "nonce": nonce, "_submit": "Submit"},
            allow_redirects=False,
        )
        if r.status_code != 302:
            raise SeedError(f"Login failed: {r.status_code} {r.text[:200]}")

    def refresh_csrf(self):
        """Grab a CSRF token from the admin page for use in subsequent API calls."""
        r = self.session.get(f"{self.base_url}/admin/")
        if r.status_code != 200:
            raise SeedError(f"Couldn't load admin page for CSRF: {r.status_code}")
        self.csrf_token = self._extract_nonce(r.text)

    def _api(self, method, path, json_data=None):
        if self.csrf_token is None:
            raise SeedError("CSRF token not initialized — call refresh_csrf() first")
        headers = {"Content-Type": "application/json", "CSRF-Token": self.csrf_token}
        r = self.session.request(
            method, f"{self.base_url}{path}",
            json=json_data, headers=headers, allow_redirects=False,
        )
        if r.status_code >= 400 or r.status_code in (301, 302, 303, 307, 308):
            raise SeedError(
                f"{method} {path} → {r.status_code}\n"
                f"  Location: {r.headers.get('Location', '(none)')}\n"
                f"  Body: {r.text[:300]}"
            )
        if not r.text:
            return {}
        try:
            return r.json()
        except ValueError:
            raise SeedError(
                f"{method} {path} returned non-JSON (status {r.status_code}):\n"
                f"  Content-Type: {r.headers.get('Content-Type', '(none)')}\n"
                f"  Body starts: {r.text[:200]!r}"
            )

    def list_challenges(self):
        return self._api("GET", "/api/v1/challenges?view=admin").get("data", [])

    def create_challenge(self, data):
        return self._api("POST", "/api/v1/challenges", data).get("data")

    def update_challenge(self, ch_id, data):
        return self._api("PATCH", f"/api/v1/challenges/{ch_id}", data).get("data")

    def list_flags(self, ch_id):
        return self._api("GET", f"/api/v1/challenges/{ch_id}/flags").get("data", [])

    def create_flag(self, data):
        return self._api("POST", "/api/v1/flags", data).get("data")

    def update_flag(self, flag_id, data):
        return self._api("PATCH", f"/api/v1/flags/{flag_id}", data).get("data")

    def list_hints(self, ch_id):
        return self._api("GET", f"/api/v1/challenges/{ch_id}/hints").get("data", [])

    def create_hint(self, data):
        return self._api("POST", "/api/v1/hints", data).get("data")

    def delete_hint(self, hint_id):
        return self._api("DELETE", f"/api/v1/hints/{hint_id}")

    def verify_admin_session(self):
        """Confirm we're actually authenticated as admin before doing real work."""
        r = self.session.get(
            f"{self.base_url}/api/v1/users/me", allow_redirects=False,
        )
        if r.status_code != 200:
            raise SeedError(
                f"Not authenticated after setup/login: GET /api/v1/users/me → "
                f"{r.status_code} (Location: {r.headers.get('Location', 'none')})"
            )
        try:
            data = r.json()
        except ValueError:
            raise SeedError(
                f"Non-JSON response from /api/v1/users/me: {r.text[:200]!r}"
            )
        user = data.get("data", {})
        if user.get("type") != "admin":
            raise SeedError(
                f"Logged in but not as admin. User: {user}"
            )


def extract_flag(challenge_num):
    """Pull the FLAG = '...' assignment out of a challenge's app.py via AST."""
    path = CHALLENGES_DIR / str(challenge_num) / "app.py"
    if not path.is_file():
        raise SeedError(f"Missing {path}")
    with path.open() as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (isinstance(target, ast.Name) and target.id == "FLAG"
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)):
                return node.value.value
    raise SeedError(f"No top-level `FLAG = \"...\"` found in {path}")


def seed_challenge(client, info, meta, flag_value):
    """Upsert one challenge plus its flag and hints.

    info: ChallengeInfo from the registry (name, port, category, ...)
    meta: dict from ctfd_config.CHALLENGE_META (description template, value, hints)
    """
    flag_str = "{" + flag_value + "}"  # CTFd convention: braces around the value
    description = meta["description"].format(port=info.port)

    existing = next(
        (c for c in client.list_challenges() if c["name"] == info.name), None,
    )
    payload = {
        "name": info.name,
        "category": info.category,
        "description": description,
        "value": meta["value"],
        "type": "standard",
        "state": "visible",
    }
    if existing:
        client.update_challenge(existing["id"], payload)
        ch_id, action = existing["id"], "Updated"
    else:
        ch = client.create_challenge(payload)
        ch_id, action = ch["id"], "Created"

    # Single static flag per challenge — update existing or create
    flags = client.list_flags(ch_id)
    flag_payload = {
        "challenge_id": ch_id, "content": flag_str, "type": "static", "data": "",
    }
    if flags:
        client.update_flag(flags[0]["id"], flag_payload)
    else:
        client.create_flag(flag_payload)

    # Hints: delete all then recreate (simpler than diffing by content)
    for h in client.list_hints(ch_id):
        client.delete_hint(h["id"])
    for h in meta.get("hints", []):
        client.create_hint({
            "challenge_id": ch_id,
            "content": h["content"],
            "cost": h.get("cost", 0),
        })

    print(f"    [+] {action} #{info.id}: {info.name}")


def seed(base_url="http://127.0.0.1:8000"):
    print(f"[+] Seeding CTFd at {base_url}")
    client = CTFdClient(base_url)
    print("[!] Waiting for CTFd to respond...")
    client.wait_until_ready()

    if not client.is_setup_complete():
        print("[+] CTFd not initialized — running first-run setup")
        client.run_setup(ADMIN, CTF_SETUP)
    else:
        print("[+] CTFd already initialized — logging in")
        client.login(ADMIN["name"], ADMIN["password"])

    client.verify_admin_session()
    client.refresh_csrf()

    print("[+] Seeding challenges:")
    for cid, info in sorted(CHALLENGES.items()):
        meta = CHALLENGE_META.get(cid)
        if meta is None:
            raise SeedError(
                f"Challenge {cid} in registry but missing from "
                f"ctfd_config.CHALLENGE_META"
            )
        flag_value = extract_flag(cid)
        seed_challenge(client, info, meta, flag_value)

    print("[+] CTFd seeded successfully.")
    print(f"[+] Login: {ADMIN['name']} / {ADMIN['password']}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed CTFd with AI Goat challenges.")
    parser.add_argument(
        "--url", default="http://127.0.0.1:8000",
        help="CTFd base URL (default: http://127.0.0.1:8000)",
    )
    args = parser.parse_args()
    try:
        seed(args.url)
    except SeedError as e:
        print(f"[-] Seed failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
