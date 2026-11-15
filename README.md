# NotebookLM Project Handoff

A Codex skill for keeping one concise project summary current. Edit `PROJECT_CONTEXT.md` alongside the code, then publish the summary to the same Google Doc already imported into NotebookLM. The publisher skips unchanged content using SHA-256. The handoff workflow uses local diffs and a targeted read of the summary to keep repeated facts out.

## Set up

1. Copy `.agents/skills/notebooklm-project-handoff/` into the same location in your project. Add the instructions from [examples/AGENTS.md](examples/AGENTS.md) to the project's existing AGENTS.md. Create or reuse `PROJECT_CONTEXT.md`. See [the example](examples/PROJECT_CONTEXT.md).
2. Create a dedicated Google Doc for this summary and add it to your notebook using the Google Drive picker. Keep its document ID from the URL.
3. Create a standalone [Google Apps Script](https://script.google.com/) project and paste [Code.gs](apps-script/Code.gs). In **Project Settings → Script properties**, set `DOCUMENT_ID` to the Doc ID and `HANDOFF_SIGNING_KEY` to a key generated with `openssl rand -hex 32`.
4. Deploy it as a web app that runs as you, with **Anyone** access so the local publisher can call it over HTTPS. This makes the endpoint reachable without Google sign-in. The script checks the request signature and timestamp before accessing the configured document. Review the code and the Google consent screen before granting access. Use a separate deployment and key for each project.
5. Add `.notebooklm-handoff/` to the **target project's** .gitignore. Create the directory with mode 0700 and save `.notebooklm-handoff/config.json` with mode 0600. Set the endpoint to the deployment's **/exec** URL and the secret to the same key from step 3.

```json
{
  "endpoint": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec",
  "secret": "YOUR_64_CHARACTER_HEX_KEY"
}
```

## Publish and verify

Run from the project root with Python 3.10 or later:

```sh
python3 .agents/skills/notebooklm-project-handoff/scripts/publish.py
```

A changed summary prints `Published` with its hash. Repeating the command prints `Unchanged` with that hash. Open the existing NotebookLM source to verify the changed paragraph. If the source is stale, reopen the notebook or use its Drive sync control. The Google Doc is managed by the publisher, so make editorial changes in the Markdown file.

The publisher can be run from a local scheduler if you want updates outside Codex. NotebookLM lookup is optional and requires a signed-in browser or a separately configured query connector available to the chat.
