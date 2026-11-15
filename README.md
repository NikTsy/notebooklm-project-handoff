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

We ran three questions twice per workflow on the same project snapshot with Codex CLI 0.169.0-alpha.11.1 and `gpt-6.1-sol` at low reasoning effort. Both variants in a pair received the same files, handoff, and question. The skill variant also had the skill, its example project instructions, and a configured NotebookLM note. When a chat asked for a missing fact, it received a scripted reply and that extra turn counted. All final answers contained both expected facts.

| Where the requested facts were available | Total tokens without skill | Total tokens with skill | Change | NotebookLM requests with skill |
| --- | ---: | ---: | ---: | ---: |
| Complete handoff and local files | 284,481 | 319,087 | +12.2% | 0 |
| Relevant facts in README | 343,665 | 334,922 | −2.5% | 0 |
| Missing fact only in NotebookLM | 955,655 | 865,354 | −9.4% | 7 |

Totals combine reported Codex input and output across six runs per variant. Uncached input increased from 34,165 to 42,690 with a complete handoff and from 45,290 to 48,957 when README was sufficient. It decreased from 181,820 to 64,274 when NotebookLM was needed. In that last scenario, the skill answered without asking the user in all six runs. The control asked six times.

In a separate README run, a section labeled as test data caused two NotebookLM checks. Total tokens rose from 411,002 to 537,007 (+30.7%). In the table above, both workflows were explicitly told that README contained confirmed conditions for the exercise. The samples are small, caching was left enabled, and we did not measure billing or NotebookLM's internal token use.

### Update and attachment checks

A new chat updated the local summary and published it to one existing NotebookLM note. A second chat received the same request and got `Unchanged`. We verified that the note ID and count stayed the same and that its text matched the file.

A fresh chat identified the board, chip, and sensor model and count from the saved project summary without photos. This confirms that the text is sufficient for those questions. We did not run a paired benchmark with the original photos or measure image recognition tokens.
