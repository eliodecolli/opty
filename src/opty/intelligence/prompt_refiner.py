import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Generator

from .context import ContextBase

_PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass(kw_only=True, frozen=True)
class PromptRefinerConfig:
    type: str
    max_steps: int = 4


@dataclass(kw_only=True, frozen=True)
class PromptRefineStep:
    current_prompt: str
    example_input: str
    target_output: str
    llm_thinking: str
    llm_output: str


@dataclass(kw_only=True, frozen=True)
class PromptRefineStepResponse:
    updated_prompt: str
    complete: bool
    thinking: str | None = None

    error: str | None = None
    raw_response: str | None = None


@dataclass(kw_only=True, frozen=True)
class PromptRefineConfig:
    prompt: str
    example_input: str
    target_output: str


@dataclass(kw_only=True, frozen=True)
class LlmResponse:
    text: str
    thinking: str | None


class PromptRefiner(ContextBase):
    def __init__(self, max_steps: int = 4):
        with open(_PROMPTS_DIR / "refiner.md", "r") as f:
            self.internal_prompt = f.read()
        self.max_steps = max_steps
        self._step = 0

    def ask_optimizer(self, input: str) -> LlmResponse:
        pass

    def ask_eval(self, input: str, system_prompt: str) -> LlmResponse:
        pass

    def step(self, config: PromptRefineConfig) -> PromptRefineStepResponse:
        self._step += 1

        # first let's look at what the target model is returning
        target_response = self.ask_eval(
            input=config.example_input,
            system_prompt=config.prompt,
        )

        # Send thinking + context to the refiner
        refiner_payload = PromptRefineStep(
            current_prompt=config.prompt,
            example_input=config.example_input,
            target_output=config.target_output,
            llm_thinking=target_response.thinking or "",
            llm_output=target_response.text,
        )
        refiner_response = self.ask_optimizer(
            input=json.dumps(asdict(refiner_payload))
        )

        refiner_step_dict = json.loads(refiner_response.text)
        try:
            return PromptRefineStepResponse(
            **refiner_step_dict,

            # the only reason we're passing this to the result is so that we can show it in the termnial UI
            thinking=target_response.thinking,
          )
        except TypeError as e:
            return PromptRefineStepResponse(
                updated_prompt=refiner_response.text,
                complete=True,
                thinking=None,
                error=str(e),
                raw_response=refiner_response.text
            )

    def __call__(
          self, config: PromptRefineConfig
      ) -> Generator[PromptRefineStepResponse, None, None]:
        step = 0
        for _ in range(self.max_steps):
            step = self.step(config=config)
            yield step

            # looks like we're done already yay
            if step.complete:
                return

            config = PromptRefineConfig(
                prompt=step.updated_prompt,
                example_input=config.example_input,
                target_output=config.target_output,
            )
