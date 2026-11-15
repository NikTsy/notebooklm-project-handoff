# Connect NotebookLM

[Start with local lookup](../README.md#quick-start) and choose one destination for `PROJECT_CONTEXT.md`.

| Destination | Requirements | Reading in a new chat |
| --- | --- | --- |
| NotebookLM note | An editable note and a signed-in `notebooklm` CLI | `lookup.py --note` reads and filters that note |
| Google Doc | A Doc imported into the notebook and a signed Apps Script deployment | A signed-in browser or an available connector reads the Doc or notebook |

## Prepare the configuration

From your project root, add `.notebooklm-handoff/` to `.gitignore`, then create the private config file.

```sh
mkdir -p .notebooklm-handoff
chmod 700 .notebooklm-handoff
touch .notebooklm-handoff/config.json
chmod 600 .notebooklm-handoff/config.json
```

Put the JSON for your selected backend in that file. Keep credentials and private logs out of `PROJECT_CONTEXT.md`.

## Option A — NotebookLM note

Install and sign in to the community [notebooklm-py CLI](https://github.com/teng-lin/notebooklm-py#installation). Make `notebooklm` available on PATH. The client uses an unofficial NotebookLM API and requires its own authenticated Google session.

Create one editable note, once, from the NotebookLM UI or with `notebooklm note create --notebook NOTEBOOK_ID --title "Project summary"`. Get its full ID with `notebooklm note list --notebook NOTEBOOK_ID --json`. The notebook ID is in the notebook URL. Store both IDs:

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
2. Create a standalone [Google Apps Script](https://script.google.com/) project and paste [Code.gs](../apps-script/Code.gs). In **Project Settings → Script properties**, set `DOCUMENT_ID` to the Doc ID and `HANDOFF_SIGNING_KEY` to a key generated with `openssl rand -hex 32`.
3. Deploy it as a web app that runs as you, with **Anyone** access so the local publisher can call it over HTTPS. This makes the endpoint reachable without Google sign-in. The script checks the request signature and timestamp before accessing the configured document. Review the code and the Google consent screen before granting access. Use a separate deployment and key for each project.
4. Set the endpoint to the deployment’s **/exec** URL and the secret to the same key from step 2. Existing configurations without a backend field default to Google Docs.

```json
{
  "backend": "google-docs",
  "endpoint": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec",
  "secret": "YOUR_64_CHARACTER_HEX_KEY"
}
```

## Publish and verify

Run from the project root with Python 3.10 or later:

```sh
python3 .agents/skills/notebooklm-project-handoff/scripts/publish.py
```

A changed summary prints `Published` with its hash. Repeating the command prints `Unchanged` with that hash. Open the existing NotebookLM source to verify the changed paragraph. For Google Docs, reopen the notebook or use its Drive sync control if the source is stale. Make editorial changes in the Markdown file.

The publisher can be run from a local scheduler if you want updates outside Codex. For note lookup, run the command below. The Google Docs backend has no note ID, so use an available connector or signed-in browser for reading.

```sh
python3 .agents/skills/notebooklm-project-handoff/scripts/lookup.py --note 'gateway|sensor'
```
