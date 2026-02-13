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
pip install opty
```

## Usage

Create an `opty.config.yaml` in your working directory, then run:

```bash
opty
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
