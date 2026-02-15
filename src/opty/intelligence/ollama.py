import re
from dataclasses import dataclass
from typing import NamedTuple

import ollama

from .prompt_builder import PromptBuilder, PromptBuilderConfig
from .prompt_refiner import LlmResponse, PromptRefiner, PromptRefinerConfig

_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)


class ThinkExtraction(NamedTuple):
    output: str
    thought: str | None


@dataclass(kw_only=True, frozen=True)
class OllamaPromptBuilderConfig(PromptBuilderConfig):
    model_name: str
    server_url: str


@dataclass(kw_only=True, frozen=True)
class OllamaRefinerConfig(PromptRefinerConfig):
    model_name: str
    server_url: str


class OllamaRefiner(PromptRefiner):
    """
        A prompt refiner targeted to optimize prompts via a local Ollama server.
        Thinking is simulated via prompt injection and extracted from <think></think> tags.
    """

    @classmethod
    def from_config(cls, cfg: dict) -> "OllamaRefiner":
        return cls(OllamaRefinerConfig(
            type=cfg["type"],
            max_steps=cfg.get("max-steps", 4),
            model_name=cfg["model"],
            server_url=cfg["ollama-server"],
        ))

    def __init__(self, config: OllamaRefinerConfig):
        super().__init__(max_steps=config.max_steps)
        self.client = ollama.Client(host=config.server_url)
        self.config = config
        self._step = 0

    def dispose(self):
        # clean up the model from memory - save some RAM fam :)
        self.client.generate(
            model=self.config.model_name,
            keep_alive=0
        )
        return super().dispose()

    def _extract_think_portion(self, text: str) -> ThinkExtraction:
        match = _THINK_RE.search(text)
        if not match:
            return ThinkExtraction(output=text, thought=None)
        thought = match.group(1).strip()
        output = _THINK_RE.sub("", text).strip()
        return ThinkExtraction(output=output, thought=thought)

    def _ask_llm(self, input: str, system_instruction: str) -> LlmResponse:
        prompt_injection = \
        """\n
            ===========================
            Before you being, think about what you'll do step by step. This thought process should be wrapped in <think></think> tags.
            Your final output should contain the specified output below, as well as this wrapped thought output.
            ===========================\n
        """

        response = self.client.chat(
            model=self.config.model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"{prompt_injection} {input}"},
            ],
            format="json",
            options={"temperature": 0.2},
        )
        extraction = self._extract_think_portion(response.message.content)
        return LlmResponse(text=extraction.output, thinking=extraction.thought)

    def ask_optimizer(self, input: str) -> LlmResponse:
        return self._ask_llm(input=input, system_instruction=self.internal_prompt)

    def ask_eval(self, input: str, system_prompt: str) -> LlmResponse:
        return self._ask_llm(input=input, system_instruction=system_prompt)


class OllamaPromptBuilder(PromptBuilder):
    """
    A prompt builder based on a local Ollama server.
    """

    @classmethod
    def from_config(cls, cfg: dict) -> "OllamaPromptBuilder":
        return cls(OllamaPromptBuilderConfig(
            type=cfg["type"],
            model_name=cfg["model"],
            server_url=cfg["ollama-server"],
        ))

    def __init__(self, config: OllamaPromptBuilderConfig):
        super().__init__()
        self.client = ollama.Client(host=config.server_url)
        self.config = config

    def dispose(self):
        # unload the model from memory to free up RAM
        self.client.generate(
            model=self.config.model_name,
            keep_alive=0
        )
        return super().dispose()

    def ask_llm(self, input: str) -> str:
        response = self.client.chat(
            model=self.config.model_name,
            messages=[
                {"role": "user", "content": input},
            ],
            format="json",
            options={"temperature": 0.2},
        )
        return response.message.content
