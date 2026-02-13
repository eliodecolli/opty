from unittest.mock import MagicMock, patch

from opty.intelligence.ollama import OllamaRefiner, OllamaRefinerConfig


def _make_refiner() -> OllamaRefiner:
    config = OllamaRefinerConfig(
        type="ollama",
        model_name="test-model",
        server_url="http://localhost:11434",
    )
    with patch("opty.intelligence.ollama.ollama.Client"):
        refiner = OllamaRefiner(config)
    return refiner


class TestOllamaRefiner:
    def test_extracts_thought_and_strips_tags(self):
        refiner = _make_refiner()
        result = refiner._extract_think_portion("<think>my reasoning</think>actual output")
        assert result.thought == "my reasoning"
        assert result.output == "actual output"

    def test_returns_full_text_when_no_tags_present(self):
        refiner = _make_refiner()
        result = refiner._extract_think_portion("plain output with no tags")
        assert result.thought is None
        assert result.output == "plain output with no tags"

    def test_thought_is_stripped_of_surrounding_whitespace(self):
        refiner = _make_refiner()
        result = refiner._extract_think_portion("<think>  spaced thought  </think>output")
        assert result.thought == "spaced thought"

    def test_multiline_thought_is_captured(self):
        refiner = _make_refiner()
        result = refiner._extract_think_portion("<think>line one\nline two</think>output")
        assert "line one" in result.thought
        assert "line two" in result.thought
        assert result.output == "output"
