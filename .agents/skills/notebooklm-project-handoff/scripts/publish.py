#!/usr/bin/env python3
"""Publish the current project's Markdown summary to an existing Google Doc or NotebookLM note."""

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen


def publish_doc(endpoint: str, secret: str, content: bytes) -> None:
    timestamp = time.time_ns() // 1_000_000
    signature = hmac.new(
        secret.encode(), f"{timestamp}\n".encode() + content, hashlib.sha256
    ).hexdigest()
    payload = json.dumps(
        {"timestamp": timestamp, "text": content.decode("utf-8"), "signature": signature},
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        result = json.loads(response.read(4096))
    if result.get("ok") is not True or not hmac.compare_digest(result.get("signature", ""), signature):
        raise RuntimeError("Apps Script did not confirm the update")


def publish_note(notebook_id: str, note_id: str, content: str) -> None:
    base = ["notebooklm", "note"]
    try:
        subprocess.run(
            [*base, "save", note_id, "--notebook", notebook_id, "--content", content],
            check=True, capture_output=True, text=True, timeout=90,
        )
        result = subprocess.run(
            [*base, "get", note_id, "--notebook", notebook_id, "--json"],
            check=True, capture_output=True, text=True, timeout=90,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("install notebooklm-py and make notebooklm available on PATH") from exc
    except subprocess.SubprocessError as exc:
        raise RuntimeError("NotebookLM note update failed; check CLI authentication and note access") from exc
    note = json.loads(result.stdout)
    if note.get("id") != note_id or note.get("content") != content:
        raise RuntimeError("NotebookLM note readback did not match the submitted content")


def publish(root: Path) -> str:
    config_dir = root / ".notebooklm-handoff"
    config_file = config_dir / "config.json"
    if config_file.stat().st_mode & 0o077:
        raise ValueError("restrict config.json permissions to 0600")
    config = json.loads(config_file.read_text(encoding="utf-8"))
    backend = config.get("backend", "google-docs")
    if backend == "notebooklm-note":
        notebook_id = config["notebook_id"]
        note_id = config["note_id"]
        for identifier in (notebook_id, note_id):
            if not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", identifier):
                raise ValueError("use the full NotebookLM notebook and note IDs")
        stamp = {"notebook_id": notebook_id, "note_id": note_id}
    elif backend == "google-docs":
        endpoint = config["endpoint"]
        secret = config["secret"]
        if not re.fullmatch(r"https://script\.google\.com/macros/s/[\w-]+/exec", endpoint):
            raise ValueError("expected a deployed Apps Script /exec URL")
        if not re.fullmatch(r"[a-f0-9]{64}", secret):
            raise ValueError("expected a 32-byte hex signing key")
        stamp = {"endpoint": endpoint}
    else:
        raise ValueError("unknown publication backend")

    content = (root / "PROJECT_CONTEXT.md").read_bytes()
    if not content.strip() or len(content) > 32000:
        raise ValueError("PROJECT_CONTEXT.md must contain 1–32000 bytes of summary text")
    digest = hashlib.sha256(content).hexdigest()
    state = config_dir / "published.json"
    stamp["sha256"] = digest
    if state.exists() and json.loads(state.read_text(encoding="utf-8")) == stamp:
        return f"Unchanged {digest}"

    if backend == "notebooklm-note":
        publish_note(notebook_id, note_id, content.decode("utf-8"))
    else:
        publish_doc(endpoint, secret, content)

    with tempfile.NamedTemporaryFile(mode="w", dir=config_dir, delete=False) as pending:
        json.dump(stamp, pending)
    Path(pending.name).replace(state)
    return f"Published {digest}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project root")
    args = parser.parse_args()
    try:
        print(publish(args.project.resolve()))
    except FileNotFoundError as exc:
        parser.exit(1, f"Missing required file: {exc.filename}\n")
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        parser.exit(1, f"Publication failed: {exc}\n")


if __name__ == "__main__":
    main()
