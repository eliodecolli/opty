import json
import pytest

from opty.intelligence.prompt_builder import PromptBuilder, PromptStep, PromptQuestion


class _StubBuilder(PromptBuilder):
    """Concrete PromptBuilder that returns a fixed string from ask_llm."""

    def __init__(self, response: str | None):
        self.internal_prompt = ""
        self._response = response

    def ask_llm(self, input: str) -> str | None:
        return self._response


class TestPromptBuilderStep:
    def test_output_is_returned(self):
        builder = _StubBuilder(json.dumps({"output": "final prompt", "questions": []}))
        result = builder.step(PromptStep(prompt_description="do x", questions=None))
        assert result.output == "final prompt"
        assert result.questions is None
        assert result.error is None

    def test_questions_are_coerced_into_dataclasses(self):
        payload = json.dumps({"output": None, "questions": [{"text": "Q1"}, {"text": "Q2"}]})
        builder = _StubBuilder(payload)
        result = builder.step(PromptStep(prompt_description="do x", questions=None))
        assert result.output is None
        assert len(result.questions) == 2
        assert all(isinstance(q, PromptQuestion) for q in result.questions)
        assert result.questions[0].text == "Q1"

    def test_empty_questions_list_treated_as_none(self):
        builder = _StubBuilder(json.dumps({"output": "done", "questions": []}))
        result = builder.step(PromptStep(prompt_description="do x", questions=None))
        assert result.questions is None

    def test_invalid_json_returns_error(self):
        builder = _StubBuilder("not valid json {{")
        result = builder.step(PromptStep(prompt_description="do x", questions=None))
        assert result.error is not None
        assert result.output == "not valid json {{"
        assert result.output == "not valid json {{"

    def test_null_response_raises(self):
        builder = _StubBuilder(None)
        with pytest.raises(ValueError):
            builder.step(PromptStep(prompt_description="do x", questions=None))
