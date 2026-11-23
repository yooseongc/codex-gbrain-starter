"""Prepare a local GBrain installation. Run with Python 3.8+."""
from pathlib import Path
import os
import secrets
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
WEBUI_REVISION = "790a862f5fa1b3b3048bae8d13a993f41bc72d41"
PATCH = str(ROOT / "webui.patch")


def git(directory, *args):
    subprocess.run(["git", "-C", str(directory), *args], check=True)


def main():
    ui = ROOT / "webui"
    if ui.exists():
        git(ui, "apply", "--reverse", "--check", PATCH)
    else:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            git(source, "init", "--quiet")
            git(source, "fetch", "--depth=1",
                "https://github.com/uaysk/GBrain_WebUI.git", WEBUI_REVISION)
            git(source, "checkout", "--quiet", "--detach", "FETCH_HEAD")
            git(source, "apply", PATCH)
            source.rename(ui)

    (ROOT / "notes").mkdir(exist_ok=True)
    try:
        fd = os.open(ROOT / ".env", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "w", encoding="ascii") as config:
            for name in ("GBRAIN_PASSWORD", "APP_AUTH_PASSWORD", "APP_SESSION_SECRET"):
                config.write(f"{name}={secrets.token_hex(32)}\n")
    print("Ready. Start with: docker compose up -d --build")


if __name__ == "__main__":
    main()
