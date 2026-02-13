from .gemini import GeminiRefiner, GeminiPromptBuilder
from .ollama import OllamaRefiner, OllamaPromptBuilder
from .prompt_refiner import PromptRefiner
from .prompt_builder import PromptBuilder

AVAILABLE_OPTIMIZERS = {
  "gemini": GeminiRefiner,
  "ollama": OllamaRefiner,
}

AVAILABLE_BUILDERS = {
  "gemini": GeminiPromptBuilder,
  "ollama": OllamaPromptBuilder,
}


def create_builder(cfg: dict) -> PromptBuilder:
  cls = AVAILABLE_BUILDERS.get(cfg["type"])
  if cls is None:
    raise ValueError(f"Unknown builder type: {cfg['type']!r}")
  return cls.from_config(cfg)


def create_refiner(cfg: dict) -> PromptRefiner:
  cls = AVAILABLE_OPTIMIZERS.get(cfg["type"])
  if cls is None:
    raise ValueError(f"Unknown refiner type: {cfg['type']!r}")
  return cls.from_config(cfg)
