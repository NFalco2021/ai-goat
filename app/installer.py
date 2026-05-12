import functools
import hashlib
import pathlib
import shutil
import subprocess

import requests
from tqdm.auto import tqdm

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
            print("[!] Pulling docker images.")
            Installer.pull_docker_images()
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
        actual_md5 = Installer.calculate_md5(Config.MODEL_PATH)
        if actual_md5 != Config.MODEL_MD5:
            raise InstallerError(
                f"Model integrity check failed! Expected md5={Config.MODEL_MD5}, "
                f"got md5={actual_md5}. Remove {Config.MODEL_PATH} and rerun the installer."
            )
        print("[+] Model integrity check pass!")
        return True

    @staticmethod
    def calculate_md5(file_path: str) -> str:
        """Calculate the MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def download_model() -> None:
        """Download the model file from the configured URL."""
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
        """Verify the downloaded model's MD5 matches the expected hash."""
        print("[!] Verifying download integrity...")
        actual_md5 = Installer.calculate_md5(Config.MODEL_PATH)
        if actual_md5 != Config.MODEL_MD5:
            # Remove the corrupt download so a retry starts fresh
            pathlib.Path(Config.MODEL_PATH).unlink(missing_ok=True)
            raise InstallerError(
                f"Downloaded model is corrupt! Expected md5={Config.MODEL_MD5}, "
                f"got md5={actual_md5}. The file has been removed — rerun the installer."
            )
        print("[+] Model integrity verified!")

    @staticmethod
    def pull_docker_images() -> None:
        """Pull all required Docker images."""
        for image in Config.AI_IMAGES:
            print(f"[!] Pulling {image}...")
            result = subprocess.run(
                ["docker", "pull", image],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "permission denied" in stderr.lower():
                    raise InstallerError(
                        f"Docker permission denied pulling {image}. "
                        "Add your user to the docker group: sudo usermod -aG docker $USER"
                    )
                raise InstallerError(
                    f"Failed to pull {image}: {stderr}"
                )
            print(f"    > {image} pulled successfully")
        print("[+] Docker images pulled!")
