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

These measurements use Codex CLI 0.169.0-alpha.11.1 and `gpt-6.1-sol` at low reasoning effort. Total tokens are reported Codex input plus output, including cached input. The tables show small samples with normal caching. They do not estimate billing or NotebookLM's internal token use.

### Complete handoff, no tool calls

Three questions, four paired repetitions each. Both chats in a pair ran in the same directory with identical `AGENTS.md`, handoff, and output instructions. Every answer was available directly in the handoff. The only setup change was whether the skill folder was installed. The prompt asked for a fixed answer format and prohibited tool use. JSONL logs confirm zero calls of any kind in both groups. A separate prompt inspection confirmed that the installed skill appeared in Codex's skill catalog.

| Metric | Without skill | Skill installed |
| --- | ---: | ---: |
| Correct answers | 12/12 | 12/12 |
| Tool calls | 0 | 0 |
| Total Codex tokens | 194,319 | 201,542 (+3.7%) |
| Median total per run | 15,797 | 15,907 |
| Uncached input tokens | 37,931 | 41,570 |

The median **paired** difference was **+92.5 tokens** with the skill installed. Per-pair differences ranged from −1,447 to +2,787, even with identical final answers and no tool calls. The result measures observed session usage with the catalog entry present. It does not establish a fixed overhead per chat.

### When the chat has to find facts

Each row compares six runs per variant, using three questions and two repetitions on matched project snapshots. The skill variant included the skill, its example `AGENTS.md`, and an authenticated NotebookLM note. A scripted answer was available to both variants if a missing fact led to a clarification. All turns, including the follow-up turns, count. Both variants reached **6/6 correct final answers** in every row.

| Starting context | Tokens without skill | Tokens with skill | Change | Clarifications without → with | NotebookLM calls with skill |
| --- | ---: | ---: | ---: | ---: | ---: |
| Handoff and local files suffice | 284,481 | 319,087 | +12.2% | 0 → 0 | 0 |
| Confirmed facts in README suffice | 343,665 | 334,922 | −2.5% | 0 → 0 | 0 |
| A missing fact is only in NotebookLM | 955,655 | 865,354 | −9.4% | 6 → 0 | 7 |
| Weak handoff | 875,591 | 701,722 | −19.9% | 4 → 0 | 4 |
| Stale handoff | 863,529 | 745,669 | −13.6% | 4 → 0 | 4 |
| No handoff | 857,131 | 759,104 | −11.4% | 4 → 0 | 5 |

In the first row, no run opened `SKILL.md` or queried NotebookLM. The installed workflow ran 14 local commands, compared with 10 in the control. The +12.2% is the observed difference between those workflows, with different local reads and tool outputs.

In the three startup scenarios, one question was answerable locally and two needed a fact from the notebook. The six locally answerable runs with the skill made zero NotebookLM calls. The 12 runs with a missing fact read the note, with one additional notebook-list call in the no-handoff scenario. The stale handoff explicitly described a prior run and contained conflicting values. This test did not cover an outdated handoff presented as current.

Uncached input rose in the first two rows, from 34,165 to 42,690 and from 45,290 to 48,957, respectively. In a separate README run, a section labeled as test data prompted two NotebookLM checks, and total tokens rose from 411,002 to 537,007 (+30.7%). The confirmed-README row above uses the same confirmation of the exercise facts in both variants.

### Summary update check

A new chat updated the local summary and published it to one existing NotebookLM note. A second chat received the same request and got `Unchanged`. We verified that the note ID and count stayed the same and that its text matched the file.

### Photo benchmark

Four fresh chats per mode answered the same question about the board, chip, and soil sensor model. We used public reference photos of the **same models used in the project**, since the original project photos were unavailable. The images were 2398 × 2398 and 512 × 512. Model and settings matched the benchmark above. Web lookup and NotebookLM were excluded. [MuseLab board photo](https://github.com/wuxx/nanoESP32-C6/blob/master/README_en.md) · [Zigbee2MQTT sensor photo](https://www.zigbee2mqtt.io/devices/ZG-303Z.html)

| Input | Median total Codex tokens | All three identifications correct |
| --- | ---: | ---: |
| Two photos only | 23,029 | 0/4 |
| Short text handoff | 17,193 | 4/4 |
| Same text handoff plus two photos | 22,984 | 4/4 |
| Read the same facts from local `PROJECT_CONTEXT.md` | 31,817 | 4/4 |

All photo-only runs identified the chip, while the exact board and sensor models remained unresolved. With the same confirmed text in both arms, the photos added 5,791 total tokens by median. The text-only handoff used 25.2% fewer tokens than the text plus photos. **Reading the local file cost more than receiving the short text in the handoff** in this setup. The file mode included a tool call to fetch the facts. Counts include input and output tokens, including cached input, and depend on the images, model, and tool calls.
