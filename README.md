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

The helper returns at most ten short matches from the local summary and README. Pass specific files to inspect code or other docs. Add `--note` only when the fact is still missing locally and a NotebookLM note is configured. That mode fetches the note by ID and filters the text before returning it to the chat.

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
| Start with a **weak, stale, or missing handoff** | **11–20% fewer total tokens** with the skill | User clarifications fell from 4 to 0 in each scenario |
| Replace the previous skill with **bounded lookup** | **28.4% fewer total tokens** | Same final accuracy: 18/18 in both versions |
| **Drop two repeat photos** from the same text handoff | **25.2% fewer total tokens** | Same accuracy: 4/4 complete answers |

These measurements use Codex CLI 0.169.0-alpha.11.1 and `gpt-6.1-sol` at low reasoning effort. Total tokens are reported Codex input plus output, including cached input. The tables show small samples with normal caching. They do not estimate billing or NotebookLM's internal token use.

### Current vs. previous skill: bounded lookup

**28.4% fewer total Codex tokens, with 18/18 correct answers in both versions.** Both groups used the skill. We reused the same three questions, two repetitions per scenario, project snapshot, and NotebookLM note.

| Starting context | Previous skill | Current skill | Change | Correct answers |
| --- | ---: | ---: | ---: | ---: |
| Weak handoff | 701,845 | 559,247 | −20.3% | 6/6 → 6/6 |
| Stale handoff | 731,721 | 492,748 | −32.7% | 6/6 → 6/6 |
| No handoff | 721,968 | 490,543 | −32.1% | 6/6 → 6/6 |
| **Total** | **2,155,534** | **1,542,538** | **−28.4%** | **18/18 → 18/18** |

Commands fell from **93 to 72**, and their output shrank from **334,590 to 105,656 characters**. Both versions read NotebookLM 12 times. In the current version, each of the 12 tasks with a missing fact fetched its configured note once. The six tasks with sufficient local facts made zero NotebookLM requests.

<details>
<summary>What changed and how the comparison was run</summary>

The current version returns short excerpts from local files and configured notes, carries the verified facts needed for the next step into the handoff, and records durable facts that have required repeated lookup. A separate check confirmed that a handoff saved one such fact in the local summary and updated the existing note. A fresh chat then found the fact locally.

The first implementation missed one fact in a long README because common matches filled the result limit. After fixing the ranking, we repeated all 18 current-version runs and retained the earlier-version runs as the comparison. One rerun timed out and was restarted. Its unfinished token usage was unavailable and is excluded. The runs occurred at different times, the caches were left enabled, and the benchmark note was short. This comparison measures the package of changes together.

</details>

### Earlier comparison: skill vs. no skill

**Same final accuracy in every row:** 6/6 with and without the skill. NotebookLM was used only where a fact was missing from the handoff and local files in the confirmed-input scenarios below.

| Starting context | Tokens without skill | Tokens with skill | Change | Clarifications without → with | NotebookLM calls with skill |
| --- | ---: | ---: | ---: | ---: | ---: |
| Handoff and local files suffice | 284,481 | 319,087 | +12.2% | 0 → 0 | 0 |
| Confirmed facts in README suffice | 343,665 | 334,922 | −2.5% | 0 → 0 | 0 |
| A missing fact is only in NotebookLM | 955,655 | 865,354 | −9.4% | 6 → 0 | 7 |
| Weak handoff | 875,591 | 701,722 | −19.9% | 4 → 0 | 4 |
| Stale handoff | 863,529 | 745,669 | −13.6% | 4 → 0 | 4 |
| No handoff | 857,131 | 759,104 | −11.4% | 4 → 0 | 5 |

<details>
<summary>Setup, exceptions, and what counted</summary>

Each row compares six runs per variant, using three questions and two repetitions on matched project snapshots. The skill variant included the skill, its example `AGENTS.md`, and an authenticated NotebookLM note. A scripted answer was available to both variants if a missing fact led to a clarification. All turns, including the follow-up turns, count. Both variants reached **6/6 correct final answers** in every row.

In the first row, no run opened `SKILL.md` or queried NotebookLM. The installed workflow ran 14 local commands, compared with 10 in the control. The +12.2% is the observed difference between those workflows, with different local reads and tool outputs.

In the three startup scenarios, one question was answerable locally and two needed a fact from the notebook. The six locally answerable runs with the skill made zero NotebookLM calls. The 12 runs with a missing fact read the note, with one additional notebook-list call in the no-handoff scenario. The stale handoff explicitly described a prior run and contained conflicting values. This test did not cover an outdated handoff presented as current.

Uncached input rose in the first two rows, from 34,165 to 42,690 and from 45,290 to 48,957, respectively. In a separate README run, a section labeled as test data prompted two NotebookLM checks, and total tokens rose from 411,002 to 537,007 (+30.7%). The confirmed-README row above uses the same confirmation of the exercise facts in both variants.

</details>

### Complete handoff, no tool calls

**Zero tool calls, 12/12 correct in each group.** With the same background catalog, installing the skill added **89–90 input tokens** in the traced repeat. The unadjusted totals include variation in the catalog Codex sent with the request.

| Runs | Without skill | Skill installed | Change |
| --- | ---: | ---: | ---: |
| Original 12 pairs | 194,319 | 201,542 | +3.7% |
| Repeat with request tracing, 12 pairs | 192,222 | 195,988 | +2.0% |

<details>
<summary>Controlled setup, original measurements, and request trace</summary>

Three questions, four paired repetitions each. Both chats in a pair ran in the same directory with identical `AGENTS.md`, handoff, and output instructions. Every answer was available directly in the handoff. The only setup change was whether the skill folder was installed. The prompt asked for a fixed answer format and prohibited tool use. JSONL logs confirm zero calls of any kind in both groups. A separate prompt inspection confirmed that the installed skill appeared in Codex's skill catalog.

| Metric | Without skill | Skill installed |
| --- | ---: | ---: |
| Correct answers | 12/12 | 12/12 |
| Tool calls | 0 | 0 |
| Total Codex tokens | 194,319 | 201,542 (+3.7%) |
| Median total per run | 15,797 | 15,907 |
| Uncached input tokens | 37,931 | 41,570 |

The median **paired** difference was **+92.5 tokens**. The aggregate rose by **7,223 tokens (+3.7%)**. The increase was concentrated in a few pairs:

| Paired input difference with the skill installed | Pairs | Net tokens |
| --- | ---: | ---: |
| +92 or +93 | 7 | +646 |
| −1,447, +1,225, or +1,226 | 3 | +1,004 |
| +2,786 or +2,787 | 2 | +5,573 |

The last two pairs explain 77% of the net increase. Final answers and output token counts matched in every pair. The first run recorded usage but did not capture the model request payloads.

**Repeat with request tracing.** Another 12 pairs all answered correctly and made zero tool calls. Codex's rollout trace captured one request per run. In the nine pairs with the same background skill catalog, installing this skill added **89–90 input tokens**. In two installed runs and one control run, Codex injected a catalog with **33 additional environment skills**. Comparing the same question and installation state, the expanded catalog corresponded to **2,694 extra input tokens**. This reproduces the size of the earlier outliers alongside the small difference associated with this skill's listing. The original payloads are unavailable, so their exact contents cannot be confirmed.

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
