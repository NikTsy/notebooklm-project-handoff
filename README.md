# NotebookLM Project Handoff

A Codex skill for keeping one concise project summary current. Edit `PROJECT_CONTEXT.md` alongside the code, then publish the summary to one existing NotebookLM note or a Google Doc already imported into the notebook. The publisher skips unchanged content using SHA-256. The handoff workflow uses local diffs and a targeted read of the summary to keep repeated facts out.

## Install the skill

Copy `.agents/skills/notebooklm-project-handoff/` into the same location in your project. Add the instructions from [examples/AGENTS.md](examples/AGENTS.md) to the project's existing AGENTS.md. Create or reuse `PROJECT_CONTEXT.md`. This workflow uses it as a project-maintained summary. See [the example](examples/PROJECT_CONTEXT.md).
Add `.notebooklm-handoff/` to the target project's .gitignore. Create the directory with mode 0700 and save the selected backend configuration as `.notebooklm-handoff/config.json` with mode 0600.

## Option A — NotebookLM note

Install and sign in to the community [notebooklm-py CLI](https://github.com/teng-lin/notebooklm-py#installation). Make `notebooklm` available on PATH. The client uses an unofficial NotebookLM API and requires its own authenticated Google session.

Create one editable note, once, from the NotebookLM UI or with `notebooklm note create`. Get its full ID with `notebooklm note list --notebook NOTEBOOK_ID --json`. The notebook ID is in the notebook URL. Store both IDs:

```json
{
  "backend": "notebooklm-note",
  "notebook_id": "11111111-1111-1111-1111-111111111111",
  "note_id": "22222222-2222-2222-2222-222222222222"
}
```

Each publish replaces the body of that note and reads it back before saving the hash locally. If the note is missing, the run fails. It never creates a replacement note. The summary is passed as a CLI argument, so it may be visible in the local process list during the update.

## Option B — Google Docs

1. Create a dedicated Google Doc for this summary and add it to your notebook using the Google Drive picker. Keep its document ID from the URL.
2. Create a standalone [Google Apps Script](https://script.google.com/) project and paste [Code.gs](apps-script/Code.gs). In **Project Settings → Script properties**, set `DOCUMENT_ID` to the Doc ID and `HANDOFF_SIGNING_KEY` to a key generated with `openssl rand -hex 32`.
3. Deploy it as a web app that runs as you, with **Anyone** access so the local publisher can call it over HTTPS. This makes the endpoint reachable without Google sign-in. The script checks the request signature and timestamp before accessing the configured document. Review the code and the Google consent screen before granting access. Use a separate deployment and key for each project.
4. Set the endpoint to the deployment’s **/exec** URL and the secret to the same key from step 2. Existing configurations without a backend field default to Google Docs.

```json
{
  "backend": "google-docs",
  "endpoint": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec",
  "secret": "YOUR_64_CHARACTER_HEX_KEY"
}
```

## Starting a new chat

- **Complete handoff:** answer from the confirmed facts in the handoff. Open local files only for facts still needed.
- **Partial, vague, or stale handoff:** use it to understand the goal and next step. For consequential facts, consult `PROJECT_CONTEXT.md`, the relevant README or documentation sections, and the current code or Git history where needed.
- **No handoff:** start from the user's request and `AGENTS.md`. Use `PROJECT_CONTEXT.md` for a short overview, or go straight to README and relevant files if a summary is absent.

Query NotebookLM only when a material fact is still missing. If the goal or next step remains unclear after checking the available context, ask a focused question. The token benchmark below includes a handoff with a missing fact. It does not measure a stale or absent handoff separately.

For a missing fact, run one targeted search:

```sh
python3 .agents/skills/notebooklm-project-handoff/scripts/lookup.py 'gateway|sensor'
```

The helper returns three short matches per fact by default from the local summary and README. Use `--also PATTERN` for independent facts in the same call, up to four in total. Pass specific files to inspect code or other docs. Add `--context 1` when a match needs nearby lines. The radius can be raised to six lines on each side, and overlapping snippets for the same fact show each line once. Add `--note` only when the fact is still missing locally and a NotebookLM note is configured. That mode fetches the note by ID and filters the text before returning it to the chat.

For a named Python function or method, use its exact name to get the complete definition with line numbers, including decorators:

```sh
python3 .agents/skills/notebooklm-project-handoff/scripts/lookup.py --function load_config app.py --also validate_config
```

Pass explicit Python files. If the name is ambiguous or the definition exceeds 100 lines or 8,000 source characters, use a narrower file selection or a line search.

## Push, merge, and handoff

- **Handoff:** capture new facts, decisions, and open work in the existing summary, publish it, and give the user a short continuation brief.
- **Merge:** update affected project documentation and the summary from the diff. Include the edits in the merge and publish the merged summary after the merge succeeds.
- **Push:** update affected project documentation and the summary, include the edits in the push, and publish the summary.

## Publish and verify

Run from the project root with Python 3.10 or later:

```sh
python3 .agents/skills/notebooklm-project-handoff/scripts/publish.py
```

A changed summary prints `Published` with its hash. Repeating the command prints `Unchanged` with that hash. Open the existing NotebookLM source to verify the changed paragraph. For Google Docs, reopen the notebook or use its Drive sync control if the source is stale. Make editorial changes in the Markdown file.

The publisher can be run from a local scheduler if you want updates outside Codex. NotebookLM lookup is optional and requires a signed-in browser or a separately configured query connector available to the chat.

## Token benchmark

| If you… | What we measured | Practical effect |
| --- | --- | --- |
| Start with a **complete handoff** | **+89–90 input tokens** in pairs with the same skill catalog | Zero tool calls in either group |
| Look up **implementation details in Python** | **12.4% fewer total tokens** with the AST option available | 8/8 correct in each version and 8 → 5 repeat reads |
| **Drop two repeat photos** from the same text handoff | **25.2% fewer total tokens** | Same accuracy: 4/4 complete answers |

These measurements use Codex CLI 0.169.0-alpha.11.1 and `gpt-6.1-sol` at low reasoning effort. Total tokens are reported Codex input plus output, including cached input. The tables show small samples with normal caching. They do not estimate billing or NotebookLM's internal token use.

### Questions about code

Five questions (four Python, one C), two fresh sessions per question and version, using the same code snapshot. The first-request background and tool catalog matched within each scored pair after normalizing workspace paths. Four pairs with different background context were rerun. Usage was recorded for every model request.

| Version | Correct answers | Model requests | Repeat code reads | Total tokens | Uncached input tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bounded line search | 10/10 | 30 | 10 | 491,709 | 46,223 |
| Bounded line search + Python AST | 10/10 | 25 | 5 | 409,920 | 58,756 |

On the Python questions alone, repeat reads fell from **8 to 5** and total tokens fell from **392,304 to 343,527 (−12.4%)**. AST was used in seven calls and was never used on the C question. Across all questions, total tokens fell **16.6%** and uncached input rose **27.1%**. These are small-sample measurements with normal caching and independently chosen tool calls.

### Batch Python definitions and constants

The example `AGENTS.md` groups AST definitions and a bounded search for constant assignments into one shell call when both are needed. In eight matched runs per version across the same four Python questions, both versions answered 8/8 correctly. The skill and lookup script were identical. Initial background and tool schemas matched within each scored pair, and usage was traced per model request.

| Python lookup instructions | Repeat reads | Model requests | Total tokens | Uncached input tokens |
| --- | ---: | ---: | ---: | ---: |
| Existing AST instructions | 8 | 24 | 405,783 | 36,711 |
| With a batching example | 7 | 23 | 389,111 | 41,704 |

Total tokens fell **4.1%** and uncached input rose **13.6%** in this sample. The new example added 54 tokens to the first request. Both versions sometimes batched reads without a second model request.

### Earlier bounded lookup benchmark

**28.4% fewer total Codex tokens, with 18/18 correct answers in both versions.** Both groups used the skill. We reused the same three questions, two repetitions per scenario, project snapshot, and NotebookLM note.

| Starting context | Previous skill | Bounded lookup | Change | Correct answers |
| --- | ---: | ---: | ---: | ---: |
| Weak handoff | 701,845 | 559,247 | −20.3% | 6/6 → 6/6 |
| Stale handoff | 731,721 | 492,748 | −32.7% | 6/6 → 6/6 |
| No handoff | 721,968 | 490,543 | −32.1% | 6/6 → 6/6 |
| **Total** | **2,155,534** | **1,542,538** | **−28.4%** | **18/18 → 18/18** |

Commands fell from **93 to 72**, and their output shrank from **334,590 to 105,656 characters**. Both versions read NotebookLM 12 times. In the bounded lookup version, each of the 12 tasks with a missing fact fetched its configured note once. The six tasks with sufficient local facts made zero NotebookLM requests.

<details>
<summary>What changed and how the comparison was run</summary>

The bounded lookup version returns short excerpts from local files and configured notes, carries the verified facts needed for the next step into the handoff, and records durable facts that have required repeated lookup. A separate check confirmed that a handoff saved one such fact in the local summary and updated the existing note. A fresh chat then found the fact locally.

The earlier-version and bounded lookup runs occurred at different times, the caches were left enabled, and the benchmark note was short. One bounded lookup run timed out and was restarted. Its unfinished token usage was unavailable and is excluded. This comparison measures the package of changes together.

</details>

### Complete handoff, no tool calls

**Zero tool calls, 12/12 correct in each group.** With the same background catalog, installing the skill added **89–90 input tokens** across nine matched pairs.

| Traced runs | Without skill | Skill installed | Change |
| --- | ---: | ---: | ---: |
| All 12 pairs | 192,222 | 195,988 | +2.0% |

<details>
<summary>Setup and catalog variation</summary>

Three questions, four paired repetitions each. Both chats in a pair ran in the same directory with identical `AGENTS.md`, handoff, and output instructions. Every answer was directly in the handoff. The only setup change was the presence of the skill folder. The prompt prohibited tool use. JSONL confirmed no calls, and rollout traces captured one request per run.

Two installed runs and one control run received an expanded catalog with 33 additional environment skills. That added 2,694 input tokens when comparing the same question and installation state. The aggregate reflects that variation. The nine pairs with the same background catalog give the closer estimate of the listing's overhead in this setup.

</details>

### Photo benchmark

**Keep confirmed model names in the handoff.** In the matched test, dropping the two photos cut median total tokens by **25.2%** with the same text, question, and accuracy.

| Switch to a short text handoff | Median tokens before | Median tokens after | Change | Complete identifications before → after |
| --- | ---: | ---: | ---: | ---: |
| Drop the photos from the same text handoff | 22,984 | 17,193 | **−25.2%** | 4/4 → 4/4 |
| Replace photos alone with confirmed facts | 23,029 | 17,193 | −25.3% | 0/4 → 4/4 |
| Include facts from `PROJECT_CONTEXT.md` directly in the handoff | 31,817 | 17,193 | −46.0% | 4/4 → 4/4 |

**Images:** public reference photos of the same models used in the project. The original project photos were unavailable. [MuseLab board photo](https://github.com/wuxx/nanoESP32-C6/blob/master/README_en.md) · [Zigbee2MQTT sensor photo](https://www.zigbee2mqtt.io/devices/ZG-303Z.html)

<details>
<summary>Photo test setup and limitations</summary>

Four fresh chats per mode answered the same question about the board, chip, and soil sensor model. The images were 2398 × 2398 and 512 × 512. Model and settings matched the benchmark above. Web lookup and NotebookLM were excluded.

With photos alone, all four chats identified the chip and left the exact board and sensor models unknown. Reading the local file required an extra tool call and cost more than receiving the short text in this setup. The first row compares the same facts with and without photos. The other rows compare different ways of supplying evidence. Totals include cached input and depend on the images, model, and tool calls.

</details>

### Summary update check

A new chat updated the local summary and published it to one existing NotebookLM note. A second chat received the same request and got `Unchanged`. We verified that the note ID and count stayed the same and that its text matched the file.
