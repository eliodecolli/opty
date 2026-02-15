import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List

from .context import ContextBase

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_MODEL = "gemini-2.5-flash"
_DEBUG_DIR = Path(__file__).parent.parent.parent.parent / "debug"


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
    raw_response: str | None = None


class PromptBuilder(ContextBase):
    def __init__(self):
        with open(_PROMPTS_DIR / "builder.md", "r") as f:
            self.internal_prompt = f.read()

    def ask_llm(self, input: str) -> str:
        pass

    def step(self, prompt_step: PromptStep) -> PromptStepResponse:
        formatted_user_input = f"{prompt_step.prompt_description}\n"
        if prompt_step.questions:
            for q in prompt_step.questions:
                formatted_user_input += f"Question: {q.text}\nAnswer: {q.answer}\n"

        payload = self.internal_prompt.replace("{{prompt_description}}", formatted_user_input)
        
        response = self.ask_llm(input=payload)
        if not response:
            return PromptStepResponse(
                output=None,
                questions=None,
                error="Received empty response from LLM. The LLM may be unavailable or the request timed out.",
                raw_response=None
            )

        try:
            output_dict = json.loads(response)
        except json.decoder.JSONDecodeError as e:
            return PromptStepResponse(
                output=None,
                questions=None,
                error="Failed to parse LLM response as JSON. The response may be malformed or incomplete.",
                raw_response=response
            )

        # Coerce raw question dicts into PromptQuestion instances
        raw_questions = output_dict.get("questions") or []
        questions = [PromptQuestion(**q) for q in raw_questions] if raw_questions else None

        return PromptStepResponse(
            output=output_dict.get("output"),
            questions=questions,
        )
