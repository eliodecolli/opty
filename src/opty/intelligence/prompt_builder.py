import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from .context import ContextBase

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_MODEL = "gemini-2.5-flash"


@dataclass(kw_only=True, frozen=True)
class PromptBuilderConfig:
    type: str


@dataclass(kw_only=True, frozen=True)
class PromptQuestion:
    text: str
    answer: str | None = None


@dataclass(kw_only=True, frozen=True)
class PromptStep:
    prompt_description: str
    questions: List[PromptQuestion] | None


@dataclass(kw_only=True, frozen=True)
class PromptStepResponse:
    output: str | None
    questions: List[PromptQuestion] | None

    error: str | None = None


class PromptBuilder(ContextBase):
    def __init__(self):
        with open(_PROMPTS_DIR / "builder.md", "r") as f:
            self.internal_prompt = f.read()

    def ask_llm(self, input: str) -> str:
        pass

    def step(self, prompt_step: PromptStep) -> PromptStepResponse:
        payload = asdict(prompt_step)
        response = self.ask_llm(input=json.dumps(payload))
        if not response:
            raise ValueError("Invalid response: Got NULL")

        try:
            output_dict = json.loads(response)
        except json.decoder.JSONDecodeError as e:
            return PromptStepResponse(
                output=response,
                questions=None,
                error=f"Invalid response from builder LLM: {str(e)}"
            )

        # Coerce raw question dicts into PromptQuestion instances
        raw_questions = output_dict.get("questions") or []
        questions = [PromptQuestion(**q) for q in raw_questions] if raw_questions else None

        return PromptStepResponse(
            output=output_dict.get("output"),
            questions=questions,
        )
