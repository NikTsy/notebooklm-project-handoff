#!/usr/bin/env python3
"""Show short, source-labeled matches from local files or the configured note."""

import argparse
import ast
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


def snippets(sources, matcher, limit, context):
    hits = []
    frequencies = Counter()
    source_lines = {}
    for label, content in sources:
        lines = content.splitlines()
        source_lines[label] = lines
        for number, line in enumerate(lines, 1):
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
    centers = {(label, number) for _, label, number, _, _ in ranked[:limit]}
    emitted = set()
    for _, label, number, line, position in ranked[:limit]:
        start = max(0, position - 45)
        window = line[start:start + 220].strip()
        prefix = "…" if start else ""
        suffix = "…" if start + 220 < len(line) else ""
        lines = source_lines[label]
        for near in range(max(1, number - context), min(len(lines), number + context) + 1):
            key = (label, near)
            if key in emitted or (near != number and key in centers):
                continue
            emitted.add(key)
            excerpt = f"{prefix}{window}{suffix}" if near == number else lines[near - 1].strip()[:220]
            yield f"{str(label)[:240]}:{near}: {excerpt}"


def function_sources(sources, names):
    matches = {name: [] for name in names}
    for label, content in sources:
        tree = ast.parse(content, filename=str(label))
        lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in matches:
                start = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
                matches[node.name].append((label, start, node.end_lineno, lines[start - 1:node.end_lineno]))
    for name, definitions in matches.items():
        if len(definitions) != 1:
            count = len(definitions)
            yield f"{name}: {count} definitions. Use narrower files or a line search."
            continue
        label, start, end, lines = definitions[0]
        if len(lines) > 100 or sum(map(len, lines)) > 8000:
            yield f"{label}:{start}-{end}: {name} exceeds the function excerpt limit. Use a line search."
            continue
        for number, line in enumerate(lines, start):
            yield f"{label}:{number}: {line}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern", help="case-insensitive regular expression")
    parser.add_argument("--also", action="append", default=[], metavar="PATTERN", help="additional fact to search for independently")
    parser.add_argument("files", nargs="*", help="local files, defaults to the summary and README")
    parser.add_argument("--function", action="store_true", help="return complete Python definitions by exact name")
    parser.add_argument("--note", action="store_true", help="search the configured NotebookLM note")
    parser.add_argument("--limit", type=int, choices=range(1, 11), default=3, help="matches per fact")
    parser.add_argument("--context", type=int, choices=range(7), default=0, help="adjacent lines on each side (0–6)")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project root")
    args = parser.parse_intermixed_args()
    if args.note and args.files:
        parser.error("--note does not take local files")
    root = args.project.resolve()
    try:
        patterns = [args.pattern, *args.also]
        if len(patterns) > 4:
            parser.error("request at most four facts")
        if args.function:
            if args.note or args.context or not args.files or any(Path(file).suffix != ".py" for file in args.files):
                parser.error("--function requires explicit Python files and cannot be combined with --note or --context")
            if not all(name.isidentifier() for name in patterns):
                parser.error("--function requires exact Python names")
            print("\n".join(function_sources(local_sources(root, args.files), patterns)))
            return
        matchers = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        sources = [note_source(root)] if args.note else local_sources(root, args.files)
        sources = list(sources)
        for pattern, matcher in zip(patterns, matchers):
            if args.also:
                print(f"Pattern: {pattern}")
            print("\n".join(snippets(sources, matcher, args.limit, args.context)) or "No matches. Try a synonym or inspect the relevant source.")
    except (OSError, ValueError, KeyError, SyntaxError, re.error, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Lookup failed ({type(exc).__name__}). Check the files, pattern, or NotebookLM configuration and authentication.\n")


if __name__ == "__main__":
    main()
