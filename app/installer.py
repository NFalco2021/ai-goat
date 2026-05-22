import functools
import hashlib
import pathlib
import shutil
import subprocess

from app.config import Config


class InstallerError(Exception):
    """Raised when any installation step fails."""


class Installer:

    @staticmethod
    def install() -> None:
        """Run the full installation: download model (if needed) and pull Docker images."""
        try:
            print("[+] Starting Installation...")
            print("[!] Checking model presence.")
            if not Installer.model_exists():
                print("[!] Downloading model, this may take 15 minutes...")
                Installer.download_model()
                Installer.verify_model_integrity()
            print("[!] Building base image (this may take a few minutes on first run)...")
            Installer.build_images()
            print("[+] Installation finished!")
        except InstallerError as e:
            print(f"[-] Installation failed: {e}")
            raise SystemExit(1)
        except KeyboardInterrupt:
            print("\n[!] Installation cancelled.")
            raise SystemExit(1)

    @staticmethod
    def model_exists() -> bool:
        """Check if the model file is already downloaded and valid."""
        if not pathlib.Path(Config.MODEL_PATH).is_file():
            print("[-] Model missing!")
            return False
        print("[+] Model found!")
        print("[!] Checking integrity, please allow 300 seconds...")
        actual = Installer.calculate_sha256(Config.MODEL_PATH)
        if actual != Config.MODEL_SHA256:
            raise InstallerError(
                f"Model integrity check failed! Expected sha256={Config.MODEL_SHA256}, "
                f"got sha256={actual}. Remove {Config.MODEL_PATH} and rerun the installer."
            )
        print("[+] Model integrity check pass!")
        return True

    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """Calculate the SHA-256 hash of a file in 1 MiB chunks."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _force_ipv4_if_v6_broken() -> None:
        """Skip IPv6 if the actual download host has broken v6 reachability.

        HuggingFace fronts via CloudFront, which advertises both A and AAAA.
        Python prefers AAAA per RFC 6724, so on a host where v6 routes
        partially (e.g. v6 to Google works but v6 to CloudFront/AWS doesn't),
        the connect hangs in SYN-SENT for minutes before the kernel falls
        back. Probe v6 against the actual download host so we don't get
        misled by a generic-target probe that happens to succeed.
        """
        import socket
        from urllib.parse import urlparse
        host = urlparse(Config.MODEL_URL).hostname or "huggingface.co"
        try:
            infos = socket.getaddrinfo(
                host, 443, family=socket.AF_INET6, type=socket.SOCK_STREAM,
            )
        except socket.gaierror:
            return  # No AAAA records — kernel will use IPv4 anyway
        if not infos:
            return
        for info in infos:
            addr = info[4]
            try:
                with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect(addr)
                return  # Some v6 endpoint works — leave default behavior
            except (OSError, socket.timeout):
                continue
        import urllib3.util.connection
        urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET
        print(f"[!] IPv6 to {host} unreachable — forcing IPv4 for the download.")

    @staticmethod
    def download_model() -> None:
        """Download the model file from the configured URL."""
        try:
            import requests
            from tqdm.auto import tqdm
        except ImportError as e:
            raise InstallerError(
                f"Missing required Python package: {e.name}. "
                "Install dependencies with: pip3 install -r requirements.txt"
            )
        Installer._force_ipv4_if_v6_broken()
        r = requests.get(Config.MODEL_URL, stream=True, allow_redirects=True)
        if r.status_code != 200:
            raise InstallerError(
                f"Model download failed: HTTP {r.status_code} from {Config.MODEL_URL}"
            )
        file_size = int(r.headers.get("Content-Length", 0))
        path = pathlib.Path(Config.MODEL_PATH).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        desc = "(Unknown total file size)" if file_size == 0 else ""
        r.raw.read = functools.partial(r.raw.read, decode_content=True)
        with tqdm.wrapattr(r.raw, "read", total=file_size, desc=desc) as r_raw:
            with path.open("wb") as f:
                shutil.copyfileobj(r_raw, f)
        print("[+] Model downloaded!")

    @staticmethod
    def verify_model_integrity() -> None:
        """Verify the downloaded model's SHA-256 matches the expected hash."""
        print("[!] Verifying download integrity...")
        actual = Installer.calculate_sha256(Config.MODEL_PATH)
        if actual != Config.MODEL_SHA256:
            # Remove the corrupt download so a retry starts fresh
            pathlib.Path(Config.MODEL_PATH).unlink(missing_ok=True)
            raise InstallerError(
                f"Downloaded model is corrupt! Expected sha256={Config.MODEL_SHA256}, "
                f"got sha256={actual}. The file has been removed — rerun the installer."
            )
        print("[+] Model integrity verified!")

    @staticmethod
    def build_images() -> None:
        """Build the local base image via docker compose."""
        result = subprocess.run(
            ["docker", "compose", "build"],
            capture_output=False, text=True
        )
        if result.returncode != 0:
            raise InstallerError("docker compose build failed — see output above.")
        print("[+] Base image built.")
