# opty

**Prompt optimization via chain-of-thought.**

`opty` helps you fine-tune your LLM prompts using a judge LLM and iterative chain-of-thought refinement. Provide a description, give one or two input/output examples, and opty will automatically improve your prompt until the target model's output matches your expectations.

## How it works

1. **Describe** what you want your prompt to do, or load an existing draft from a file
2. **opty** generates an initial prompt draft (the *builder* LLM), asking clarifying questions if needed
3. **Provide** one example input and the ideal output you expect
4. **opty** runs your draft prompt against the example input using the *refiner* LLM, captures its chain-of-thought, and analyzes where the thinking went wrong
5. Based on that analysis, the refiner rewrites the prompt to steer the model in the right direction
6. Steps 4–5 repeat until the output matches your target or the step limit is reached
7. The final optimized prompt is saved to a file of your choice

## Installation

```bash
pip install opty-prompt
```

## Usage

Create an `opty.config.yaml` in your working directory, then run:

```bash
opty-prompt
```

## Configuration

opty has two independent roles:

- **Builder** — generates the initial prompt draft from your description. This is a straightforward text generation task, so it works well with smaller, faster models.
- **Refiner** — evaluates the prompt against your example, reads the model's chain-of-thought, and rewrites the prompt accordingly. This requires stronger reasoning, so it benefits significantly from a more capable model.

Each role is configured independently and can use a different provider and model. You can freely mix and match Gemini and Ollama for either role.

---

### All Gemini

```yaml
config:
  builder:
    type: gemini
    model: gemini-2.5-flash
    api-key: <your-api-key>
  refiner:
    type: gemini
    max-steps: 4
    model: gemini-2.5-flash
    api-key: <your-api-key>
```

---

### All Ollama (local)

```yaml
config:
  builder:
    type: ollama
    model: gemma3:4b-it-qat      # smaller model is fine for building
    ollama-server: http://127.0.0.1:11434
  refiner:
    type: ollama
    max-steps: 4
    model: gemma3:12b-it-qat     # use a stronger model for refinement
    ollama-server: http://127.0.0.1:11434
```

---

### Mixed: Ollama builder + Gemini refiner

Run a lightweight local model for drafting and offload the heavier refinement reasoning to Gemini:

```yaml
config:
  builder:
    type: ollama
    model: gemma3:4b-it-qat
    ollama-server: http://127.0.0.1:11434
  refiner:
    type: gemini
    max-steps: 4
    model: gemini-2.5-flash
    api-key: <your-api-key>
```

---

### Mixed: Gemini builder + Ollama refiner

```yaml
config:
  builder:
    type: gemini
    model: gemini-2.5-flash
    api-key: <your-api-key>
  refiner:
    type: ollama
    max-steps: 4
    model: gemma3:12b-it-qat
    ollama-server: http://127.0.0.1:11434
```

---

### Configuration reference

#### Shared — all types

These keys apply to both `builder` and `refiner` regardless of the provider:

| Key | Required | Description |
|---|---|---|
| `type` | Yes | Provider to use. One of: `gemini`, `ollama` |

#### Shared — refiner only

| Key | Required | Default | Description |
|---|---|---|---|
| `max-steps` | No | `4` | Maximum number of refinement iterations before stopping |

#### Gemini

| Key | Required | Description |
|---|---|---|
| `model` | Yes | Gemini model name (e.g. `gemini-2.5-flash`, `gemini-2.5-pro`) |
| `api-key` | Yes | Your Google Gemini API key |

#### Ollama

| Key | Required | Description |
|---|---|---|
| `model` | Yes | Ollama model tag (e.g. `gemma3:4b-it-qat`, `llama3.1:8b`) |
| `ollama-server` | Yes | Base URL of your Ollama server (e.g. `http://127.0.0.1:11434`) |

---

### Model size guidance

| Role | Requirements | Examples |
|---|---|---|
| Builder | Light — basic instruction following | `gemma3:4b`, `gemini-2.5-flash` |
| Refiner | Heavy — strong reasoning and chain-of-thought | `gemma3:12b`+, `gemini-2.5-pro` |

## Examples
Given the description:
```
a prompt that extracts action items from a meeting transcription and returns them as a numbered list with owner and due dates (if due date is available, otherwise dont include it)
```
We were able to draft the following prompt:
```
|  Extract action items from the following meeting transcription. For each action item, identify  │
|  the owner and due date if explicitly stated. If the owner is not clearly stated, assign it to  │
│  'Unassigned'. If no due date is mentioned, do not include it. Format each action item as a     │
│  numbered list, using 'Action Item', 'To-do', or 'Next Items' as appropriate based on the       │
│  context. If no action items are found, state that there are no actionable items.               │
│                                                                                                 │
│  Transcription:                                                                                 │
│  [Insert Transcription Here] 
```

We then used as an example, a very basic synthetic transcription:
```
Meeting Transcript – Project Orion Sync

Maya: Quick updates. Timeline slipped two weeks due to API instability.
Jon: Action item: I’ll own vendor follow-up and send status by Thursday.
Lena: Decision: we’re dropping the legacy dashboard and reallocating those hours to onboarding flow.
Raj: Key takeaway, we need clearer acceptance criteria before sprint planning.
Maya: Agreed. Also documenting risks in a shared tracker.
Jon: I’ll schedule customer interviews; need questions from product by EOD.
Lena: Success metric changed to activation rate, not sign-ups.
Raj: Blocker: staging environment access.
Maya: I’ll escalate to IT. Next review Monday. Meeting adjourned.
```
and a target output:
```json
{
  "meeting_title": "Project Orion Sync",
  "overview": "The timeline slipped by two weeks due to API instability. The team reprioritized work toward the onboarding flow, clarified success metrics, and assigned owners to resolve blockers and improve risk visibility.",
  "timeline_update": {
    "status": "delayed",
    "delay_duration": "2 weeks",
    "reason": "API instability"
  },
  "key_decisions": [
    "Drop the legacy dashboard",
    "Reallocate capacity to the onboarding flow",
    "Change primary success metric from sign-ups to activation rate"
  ],
  "action_items": [
    {
      "owner": "Jon",
      "task": "Follow up with external vendor",
      "due": "Thursday"
    },
    {
      "owner": "Jon",
      "task": "Schedule customer interviews",
      "due": null
    },
    {
      "owner": "Product Team",
      "task": "Provide customer interview questions",
      "due": "EOD"
    },
    {
      "owner": "Maya",
      "task": "Escalate staging environment access to IT",
      "due": null
    },
    {
      "owner": "Maya",
      "task": "Create and maintain shared risk tracker",
      "due": null
    }
  ],
  "blockers": [
    "No access to the staging environment"
  ],
  "key_takeaways": [
    "Define acceptance criteria before sprint planning",
    "Centralize and continuously update risk visibility",
    "Prioritize customer feedback to validate onboarding improvements"
  ],
  "next_steps": [
    "Send vendor status update",
    "Prepare customer interview questions",
    "Resolve staging access issue",
    "Roll out risk tracker"
  ],
  "next_meeting": {
    "day": "Monday",
    "purpose": "Project review"
  }
}
```
As you can see the prompt itself does not mention a JSON output, or anything regarding structured output at all.

After running the refiner for 2 steps here's the final version of the prompt:
```md
|  You are an expert in meeting summarization and action item extraction. Your task is to         │
│  process a meeting transcription and generate a comprehensive JSON summary. The summary should  │
│  include the following sections:                                                                │
│                                                                                                 │
│  1.  **meeting_title**: Extract the title of the meeting.                                       │
│  2.  **overview**: Provide a concise summary of the main discussion points, decisions, and      │
│  outcomes. Focus on synthesizing information rather than just listing points.                   │
│  3.  **timeline_update**: If there's a specific update about a project timeline (e.g.,          │
│  slipped, delayed, on track), extract its status, the duration of change (if any, e.g., '2      │
│  weeks', '1 month'), and the reason. Use `null` if a specific detail is not mentioned.          │
│  4.  **key_decisions**: List all explicit decisions made during the meeting. Phrase them as     │
│  clear, concise statements.                                                                     │
│  5.  **action_items**: Extract all action items. For each action item, identify:                │
│      *   `owner`: The person or team responsible. If not explicitly stated, infer the most      │
│  likely owner or assign 'Unassigned'.                                                           │
│      *   `task`: A clear, actionable description of the task. Consolidate related tasks if      │
│  they are part of a single action item.                                                         │
│      *   `due`: The due date, if explicitly mentioned. If no due date is mentioned, use         │
│  `null`.                                                                                        │
│  6.  **blockers**: List any identified blockers or obstacles. Phrase them concisely.            │
│  7.  **key_takeaways**: Summarize important insights, lessons learned, or general points to     │
│  remember. Synthesize related points into broader takeaways.                                    │
│  8.  **next_steps**: List immediate next steps or follow-ups that are crucial for progress but  │
│  might not be formal assigned action items. These should be distinct from the action items.     │
│  9.  **next_meeting**: If mentioned, include the day and purpose of the next scheduled          │
│  meeting. Use `null` for either field if not specified.                                         │
│                                                                                                 │
│  Ensure the output is a valid JSON object. If a section has no relevant information, include    │
│  an empty array for lists or `null` for objects/scalars, but always include all top-level       │
│  keys.                                                                                          │
│                                                                                                 │
│  Transcription:                                                                                 │
│  [Insert Transcription Here]                                                                    │
```
