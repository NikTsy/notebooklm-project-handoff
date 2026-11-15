---
name: notebooklm-project-handoff
description: Retrieve a project fact missing from the supplied handoff and relevant local files, or maintain and publish the project summary for a requested push, merge, or new handoff.
---

Read the supplied handoff and targeted local files first. When those answer the question, stop. For a missing fact, try `python3 <skill-directory>/scripts/lookup.py "term|synonym"` before contacting NotebookLM.

Use `--also` to request separate facts in one call. Default to three matches per fact and add `--context 1` only when necessary. The supported radius is 0–6 lines. For Python behavior use `lookup.py --function NAME file.py` to read a complete definition, optionally with `--also NAME`.

If the fact is still missing, run the same script with `--note`. The script uses the configured note ID. For a notebook-only configuration ask a focused question by explicit notebook ID. Cite the source, and report access failures. Ask the user only for a consequential unresolved fact.

For a requested push, merge, or new handoff, read [the maintenance workflow](references/maintenance.md).
