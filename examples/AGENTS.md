# Project continuity

Start with the handoff the user supplied. If it answers the question, answer directly. For missing facts, start with one bounded local search from the project root: `python3 .agents/skills/notebooklm-project-handoff/scripts/lookup.py 'term|synonym'`. It searches PROJECT_CONTEXT.md and README.md by default. Pass specific files after the pattern for code or other docs. If a broad search misses a needed fact, search once for that fact specifically before using NotebookLM. Stop when the available evidence answers the question.

Load the notebooklm-project-handoff skill only for a material fact still missing after these checks, or to maintain and publish the summary for a requested push, merge, or new handoff. Reading a supplied handoff is part of answering the user's question.
