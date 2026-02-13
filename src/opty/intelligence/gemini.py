from dataclasses import dataclass
from .prompt_builder import PromptBuilder, PromptBuilderConfig
from .prompt_refiner import LlmResponse, PromptRefiner, PromptRefinerConfig
from google.genai import Client
from google.genai.types import (
    GenerateContentConfig,
    ContentDict,
    PartDict,
    ThinkingConfig,
)

@dataclass(kw_only=True, frozen=True)
class GeminiPromptBuilderConfig(PromptBuilderConfig):
    api_key: str
    model_name: str


@dataclass(kw_only=True, frozen=True)
class GeminiRefinerConfig(PromptRefinerConfig):
    api_key: str
    model_name: str


class GeminiRefiner(PromptRefiner):
    '''
      A prompt refiner targeted to optimize prompts for Google's Gemini models.
    '''
    @classmethod
    def from_config(cls, cfg: dict) -> "GeminiRefiner":
        return cls(GeminiRefinerConfig(
            type=cfg["type"],
            max_steps=cfg.get("max-steps", 4),
            api_key=cfg["api-key"],
            model_name=cfg["model"],
        ))

    def __init__(self, config: GeminiRefinerConfig):
        super().__init__(max_steps=config.max_steps)
        self.llm = Client(api_key=config.api_key)
        self.config = config
        self._step = 0

    def _ask_llm(self, input: str, system_instruction: str, with_thinking: bool = False) -> LlmResponse:
        response = self.llm.models.generate_content(
            model=self.config.model_name,
            contents=[
                ContentDict(role="user", parts=[PartDict(text=input)]),
            ],
            config=GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                response_mime_type="application/json",
                thinking_config=ThinkingConfig(
                    include_thoughts=with_thinking,
                    thinking_budget=-1 if with_thinking else 0,
                ),
            ),
        )

        thinking_part = next((part for part in response.parts if part.thought), None)
        return LlmResponse(
            text=response.text,
            thinking=thinking_part.text if thinking_part else None,
        )

    def ask_optimizer(self, input: str) -> LlmResponse:
        return self._ask_llm(input=input, system_instruction=self.internal_prompt)

    def ask_eval(self, input: str, system_prompt: str) -> LlmResponse:
        return self._ask_llm(input=input, system_instruction=system_prompt, with_thinking=True)


class GeminiPromptBuilder(PromptBuilder):
    '''
      A prompt builder based on Google's Gemini models.
    '''
    @classmethod
    def from_config(cls, cfg: dict) -> "GeminiPromptBuilder":
        return cls(GeminiPromptBuilderConfig(
            type=cfg["type"],
            api_key=cfg["api-key"],
            model_name=cfg["model"],
        ))

    def __init__(self, config: GeminiPromptBuilderConfig):
        super().__init__()

        self.config = config
        self.llm = self.llm = Client(api_key=config.api_key)

    def ask_llm(self, input: str) -> str:
        response = self.llm.models.generate_content(
            model=self.config.model_name,
            contents=[
                ContentDict(role="user", parts=[PartDict(text=input)]),
            ],
            config=GenerateContentConfig(
                system_instruction=self.internal_prompt,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        return response.text
