#!/usr/bin/env python3
"""Show short, source-labeled matches from local files or the configured note."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid


def local_sources(root, paths):
    for path in paths or ("PROJECT_CONTEXT.md", "README.md"):
        file = (root / path).resolve()
        if not file.is_relative_to(root):
            raise ValueError("search files inside the project")
        if file.is_file():
            yield file.relative_to(root), file.read_text(encoding="utf-8")


def note_source(root):
    cfg = json.loads((root / ".notebooklm-handoff/config.json").read_text(encoding="utf-8"))
    notebook_id, note_id = (str(uuid.UUID(cfg[key])) for key in ("notebook_id", "note_id"))
    result = subprocess.run(
        ["notebooklm", "note", "get", note_id, "--notebook", notebook_id, "--json"],
        check=True, capture_output=True, text=True, timeout=45,
    )
    note = json.loads(result.stdout)
    if note.get("id") != note_id or not isinstance(note.get("content"), str):
        raise ValueError("NotebookLM returned an unexpected note")
    source = f"NotebookLM: {note['title']} (https://notebook.google.com/notebook/{notebook_id}?noteId={note_id})"
    return source, note["content"]


def snippets(sources, matcher, limit):
    hits = []
    frequencies = Counter()
    for label, content in sources:
        for number, line in enumerate(content.splitlines(), 1):
            matches = list(matcher.finditer(line))
            if matches:
                hits.append((label, number, line, matches))
                frequencies.update({match.group().casefold() for match in matches})

    # Select rare matches first so a common term cannot crowd out another fact.
    ranked = []
    for label, number, line, matches in hits:
        match = min(matches, key=lambda item: frequencies[item.group().casefold()])
        ranked.append((frequencies[match.group().casefold()], label, number, line, match.start()))
    ranked.sort(key=lambda hit: hit[0])
    for _, label, number, line, position in ranked[:limit]:
        start = max(0, position - 45)
        window = line[start:start + 220].strip()
        prefix = "…" if start else ""
        suffix = "…" if start + 220 < len(line) else ""
        yield f"{str(label)[:240]}:{number}: {prefix}{window}{suffix}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern", help="case-insensitive regular expression")
    parser.add_argument("files", nargs="*", help="local files, defaults to the summary and README")
    parser.add_argument("--note", action="store_true", help="search the configured NotebookLM note")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project root")
    args = parser.parse_args()
    if args.note and args.files:
        parser.error("--note does not take local files")
    root = args.project.resolve()
    try:
        matcher = re.compile(args.pattern, re.IGNORECASE)
        sources = [note_source(root)] if args.note else local_sources(root, args.files)
        print("\n".join(snippets(sources, matcher, 10)) or "No matches. Try a synonym or inspect the relevant source.")
    except (OSError, ValueError, KeyError, re.error, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Lookup failed ({type(exc).__name__}). Check the files, pattern, or NotebookLM configuration and authentication.\n")


if __name__ == "__main__":
    main()
