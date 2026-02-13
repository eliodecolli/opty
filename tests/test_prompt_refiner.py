import json

from opty.intelligence.prompt_refiner import (
    LlmResponse,
    PromptRefineConfig,
    PromptRefiner,
)


def _eval_response(thinking: str | None = None) -> LlmResponse:
    return LlmResponse(text="some llm output", thinking=thinking)


def _optimizer_response(updated_prompt: str, complete: bool) -> LlmResponse:
    return LlmResponse(
        text=json.dumps({"updated_prompt": updated_prompt, "complete": complete}),
        thinking=None,
    )


class _StubRefiner(PromptRefiner):
    """Concrete PromptRefiner with controllable eval and optimizer responses."""

    def __init__(
        self,
        eval_responses: list[LlmResponse],
        optimizer_responses: list[LlmResponse],
        max_steps: int = 4,
    ):
        self.internal_prompt = ""
        self.max_steps = max_steps
        self._step = 0
        self._eval_calls: list[tuple[str, str]] = []
        self._eval_iter = iter(eval_responses)
        self._opt_iter = iter(optimizer_responses)

    def ask_eval(self, input: str, system_prompt: str) -> LlmResponse:
        self._eval_calls.append((input, system_prompt))
        return next(self._eval_iter)

    def ask_optimizer(self, input: str) -> LlmResponse:
        return next(self._opt_iter)


def _base_config(prompt: str = "initial prompt") -> PromptRefineConfig:
    return PromptRefineConfig(
        prompt=prompt,
        example_input="some input",
        target_output="desired output",
    )


class TestPromptRefiner:
    def test_runs_exactly_max_steps_when_never_complete(self):
        n = 3
        refiner = _StubRefiner(
            eval_responses=[_eval_response()] * n,
            optimizer_responses=[_optimizer_response("updated", False)] * n,
            max_steps=n,
        )
        steps = list(refiner(config=_base_config()))
        assert len(steps) == n

    def test_stops_early_when_complete_is_true(self):
        refiner = _StubRefiner(
            eval_responses=[_eval_response()] * 4,
            optimizer_responses=[
                _optimizer_response("v2", False),
                _optimizer_response("v3", True),
                _optimizer_response("v4", False),
            ],
            max_steps=4,
        )
        steps = list(refiner(config=_base_config()))
        assert len(steps) == 2
        assert steps[-1].complete is True

    def test_updated_prompt_is_passed_to_next_step(self):
        refiner = _StubRefiner(
            eval_responses=[_eval_response(), _eval_response()],
            optimizer_responses=[
                _optimizer_response("improved prompt", False),
                _optimizer_response("final prompt", True),
            ],
            max_steps=4,
        )
        list(refiner(config=_base_config(prompt="initial prompt")))
        # second eval call should use the updated prompt as the system prompt
        assert refiner._eval_calls[0][1] == "initial prompt"
        assert refiner._eval_calls[1][1] == "improved prompt"

    def test_thinking_from_eval_is_included_in_step_response(self):
        refiner = _StubRefiner(
            eval_responses=[_eval_response(thinking="my thoughts")],
            optimizer_responses=[_optimizer_response("v2", True)],
            max_steps=1,
        )
        steps = list(refiner(config=_base_config()))
        assert steps[0].thinking == "my thoughts"
