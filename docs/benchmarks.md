# Token benchmarks

These measurements use Codex CLI 0.169.0-alpha.11.1 and `gpt-6.1-sol` at low reasoning effort. Total tokens are reported Codex input plus output, including cached input. The tables show small samples with normal caching. They do not estimate billing or NotebookLM's internal token use.

### Read a route branch by explicit URL path

Four Python questions, two matched runs per question and version. Five pairs with different initial background were rerun. Both versions answered 8/8 correctly. Token usage was traced per model request.

| Version | Repeat reads | Model requests | Total tokens | Uncached input tokens |
| --- | ---: | ---: | ---: | ---: |
| Function lookup with dependencies | 4 | 20 | 324,566 | 49,807 |
| Route selection for explicit paths | 2 | 18 | 296,150 | 42,727 |

Total tokens fell **8.8%** overall and **25.9%** on the endpoint questions alone. All four route calls matched paths from the question. One ordinary-function run still required an extra read. The uncached totals were influenced by a 12,032-token first-request cache difference in one pair.

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
