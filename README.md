# NotebookLM Project Handoff

A Codex skill that helps new chats pick up a project from its handoff and local files. Keep one concise `PROJECT_CONTEXT.md` alongside the code and, optionally, publish it to an existing NotebookLM note or a Google Doc imported into NotebookLM.

**[Quick start](#quick-start)** · **[Install with an agent](#install-with-an-agent)** · **[Connect NotebookLM](docs/notebooklm-setup.md)** · **[Benchmarks](docs/benchmarks.md)**

## Try it without a Google account

From a clone of this repository, run a lookup against the included example summary:

```sh
python3 .agents/skills/notebooklm-project-handoff/scripts/lookup.py \
  --project examples 'queued jobs' --also 'idempotency'
```

The command returns two source-labeled excerpts in one call. In your own project, Codex starts with the handoff and local evidence, then uses NotebookLM only for facts it still needs.

## Quick start

**Requires Git and Python 3.10+.** Run from the root of the project you want to set up.

```sh
(
  set -eu
  checkout=$(mktemp -d)
  git clone --depth 1 https://github.com/NikTsy/notebooklm-project-handoff.git "$checkout"
  skill=.agents/skills/notebooklm-project-handoff
  mkdir -p .agents/skills
  if [ -e "$skill" ]; then
    echo "Skill already exists at $skill. Review it before updating." >&2
    exit 1
  fi
  cp -R "$checkout/$skill" "$skill"
  [ -e AGENTS.md ] || cp "$checkout/examples/AGENTS.md" AGENTS.md
  [ -e PROJECT_CONTEXT.md ] || cp "$checkout/examples/PROJECT_CONTEXT.md" PROJECT_CONTEXT.md
)
```

With Node.js, you can also install the skill files using the [skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add NikTsy/notebooklm-project-handoff --skill notebooklm-project-handoff -a codex -y --copy
```

With this method, add or merge the two example project files yourself.

If your project already had an `AGENTS.md`, merge the relevant rules from the [example](examples/AGENTS.md) into it. Replace the sample summary with your project's facts, or keep and update your existing summary. See the [summary example](examples/PROJECT_CONTEXT.md).

Check local lookup before connecting a backend. On the sample summary, this finds the queued-jobs line. On your own summary, substitute a term it contains.

```sh
python3 .agents/skills/notebooklm-project-handoff/scripts/lookup.py 'queued jobs'
```

## Install with an agent

Paste this into a Codex chat opened in your project.

> Set up NotebookLM Project Handoff from https://github.com/NikTsy/notebooklm-project-handoff. Follow its Quick start. Merge the example rules into my existing AGENTS.md and preserve my project-specific instructions. Create or update PROJECT_CONTEXT.md using verified local facts. Run one local lookup and show what you changed. Keep this setup local unless I request a NotebookLM connection.

The installable folder contains the [skill entry point](.agents/skills/notebooklm-project-handoff/SKILL.md), [lookup and publish scripts](.agents/skills/notebooklm-project-handoff/scripts) and [maintenance workflow](.agents/skills/notebooklm-project-handoff/references/maintenance.md).

## Everyday use

| When you… | The agent… |
| --- | --- |
| Start a chat with a complete handoff | Answers from the handoff when it has enough evidence. |
| Ask about a missing or stale fact | Checks the relevant local summary, docs or code. Queries NotebookLM only if the fact is still missing and an access method is configured. |
| Ask for a handoff | Updates the summary, publishes it if configured, and gives you a short continuation brief. |
| Ask to push or merge | Updates affected docs and summary alongside the change and publishes the resulting summary if configured. |

Try “Write a handoff for the next chat” after a change. Keep durable facts such as confirmed hardware model names and verified decisions in the summary. Include the few facts the next task needs directly in the handoff.

## Targeted lookup

Run these from the project root, replacing the sample names and files.

| Need | Arguments to `lookup.py` |
| --- | --- |
| Search the summary and README | `'gateway\|sensor'` |
| Find several independent facts | `'gateway' --also 'sensor'` |
| Read code around a match | `'handler' app.py --context 6 --limit 1` |
| Read a Python function and direct local dependencies | `--function load_config app.py --deps` |
| Read a Python handler branch for a URL path named in the question | `--function do_GET server.py --route /api/status` |
| Find missing facts in a configured NotebookLM note | `--note 'gateway' --also 'sensor'` |

The line search returns three matches per fact by default and supports up to four distinct patterns. Python function excerpts include line numbers and decorators. `--deps` includes up to four direct helpers or uppercase module assignments from the same file, with a shared budget of 100 lines and 8,000 source characters. `--route` selects a unique top-level `if` or `elif` with literal path equality or a prefix check. It includes shared handler code and bounded dependencies.

## Publish to NotebookLM

[Choose a backend and configure it](docs/notebooklm-setup.md). The publisher updates one existing destination and skips unchanged content. Start with local lookup if you only want the handoff workflow.

## Measured results

In the latest route benchmark, total tokens fell **8.8%** across four Python questions, with **8/8 correct answers** in both versions. Endpoint questions used **25.9% fewer** total tokens. The [benchmark notes](docs/benchmarks.md) include cache counts, the cost of installing the skill with a complete handoff, and a comparison of repeated photos with confirmed text facts.

## License

[MIT](LICENSE)
