---
name: notebooklm-project-handoff
description: Maintain a repository's project summary and publish it to an existing NotebookLM Google Docs source before a push or handoff. Use for project continuity and concise session closeouts.
---

Use PROJECT_CONTEXT.md as the project summary. Check the relevant Git diff and existing summary sections. Update the paragraph that owns a changed fact and add only durable decisions, verified status, and open work. Distinguish working-tree changes from deployed behavior. Exclude credentials and private logs from the summary.

For a push, bring the relevant README sections up to date and include documentation changes in the push. For a handoff, write a short continuation brief after updating the summary. Push only when the user has requested it.

From the target project root, run `python3 <skill-directory>/scripts/publish.py`. The config lives at `.notebooklm-handoff/config.json`. Keep one Google Doc imported into NotebookLM. Repeated runs with unchanged content and destination skip the network. A published hash confirms delivery to Docs. If the user requests a NotebookLM check, open the existing source and verify the changed facts there.

For questions, start with the local summary and relevant code. When a fact is missing and NotebookLM access is configured through a signed-in browser or a query connector, ask a focused question in the project's notebook and cite the source. Report unavailable access or an unconfirmed publication directly.
