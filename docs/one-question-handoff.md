# Two project facts from one NotebookLM question

A fresh Codex chat had to identify the gateway board and sensor models in a plant-monitoring project. The working directory was a new Git repository. The prompt supplied the repository and notebook links, and asked for both models. The model names were absent from the prompt and local project.

## What the agent did

1. Installed [NotebookLM Project Handoff](../README.md#quick-start) from GitHub and read its instructions.
2. Ran a local lookup against the project. The result contained neither hardware fact.
3. Asked NotebookLM one question covering both facts and requesting source citations.

```sh
notebooklm ask --notebook "$NOTEBOOK_ID" --json \
  "Which exact gateway board and sensor models does the project summary confirm? Cite the source for both."
```

NotebookLM identified the gateway board as **MuseLab nanoESP32-C6** and the sensor model as **Zbeacon ZG-303Z**. The summary confirmed seven sensors. Both model names appeared together in one `references[].cited_text` entry, which is how we checked that the answer came from the source.

## How we verified it

The test used a separate notebook with a copy of the existing summary source. Its conversation went from zero to one Q&A turn. The agent trace recorded one successful `notebooklm ask` invocation. The original conversation history matched before and after the test.

This counts questions submitted through the CLI. It does not count the CLI's internal network calls or estimate token savings. The notebook ID and account details are private, so the example uses a placeholder.

## Try it on your own project

Start with the [local lookup demo](../README.md#try-it-without-a-google-account). For the live test, use a notebook you can access and a summary that already contains the two facts. The [NotebookLM setup guide](notebooklm-setup.md) covers access and optional summary publication. The [original community write-up](https://github.com/teng-lin/notebooklm-py/discussions/2556) has the same command and result.
