from pathlib import Path
from typing import List

from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner

from opty.intelligence import create_builder
from opty.intelligence.prompt_builder import PromptBuilder, PromptQuestion, PromptStep
from opty.enums import DraftSource
from opty.ui.console import console
from opty.ui.display import display_error, display_llm_error, display_prompt
from opty.ui.input import collect_answers, get_prompt_description, wait_for_user_prompt


def choose_draft_source() -> DraftSource:
    console.print()
    console.print(
        Panel(
            "[bold]How do you want to start?[/bold]\n\n"
            "  [bold orange1]1.[/bold orange1]  Load a draft prompt from a file\n"
            "  [bold orange1]2.[/bold orange1]  Interactively build a new draft prompt",
            border_style="orange1",
            padding=(1, 2),
        )
    )
    console.print()

    choice = wait_for_user_prompt(
        "[bold orange1]Choice[/bold orange1]", choices=["1", "2"]
    )

    return (
        DraftSource.DRAFT_FILE
        if choice == "1"
        else DraftSource.INTERACTIVE
        if choice == "2"
        else DraftSource.UNKNOWN
    )


def build_prompt_interactively(builder: PromptBuilder, description: str) -> str | None:
    questions: List[PromptQuestion] | None = None

    while True:
        step = PromptStep(prompt_description=description, questions=questions)

        with Live(
            Spinner("dots", text=" Drafting prompt..."), console=console, transient=True
        ):
            response = builder.step(step)

        if response.error:
            display_llm_error(error=response.error, raw_response=response.raw_response)
            return None

        if response.output:
            display_prompt(response.output, title="Draft Prompt")
            return response.output

        if response.questions:
            questions = collect_answers(response.questions)
        else:
            console.print("[red]Unexpected: no output and no questions returned.[/red]")
            return None


def get_initial_prompt(config: dict) -> str | None:
    draft_source = choose_draft_source()
    if draft_source is None:
        return None

    console.print()
    console.print(Rule(style="dim"))

    if draft_source == DraftSource.DRAFT_FILE:
        console.print()
        path_str = wait_for_user_prompt(
            "[bold orange1]Path to prompt file[/bold orange1]"
        )
        path = Path(path_str).expanduser()
        if not path.is_file():
            console.print(f"[red]File not found:[/red] {path}")
            return get_initial_prompt(config=config)

        draft_prompt = path.read_text()
        display_prompt(draft_prompt, title="Draft Prompt")
    elif draft_source == DraftSource.INTERACTIVE:
        description = get_prompt_description()
        if not description:
            console.print("[orange]No prompt description provided.[/orange]")

            # start over until we get something of substance
            return get_initial_prompt(config=config)

        console.print()
        console.print(Rule(style="dim"))
        with create_builder(config["builder"]) as build:
            draft_prompt = build_prompt_interactively(build, description)

        if not draft_prompt:
            display_error("Failed to draft initial prompt.", title="Error")
            return None

    elif draft_source == DraftSource.UNKNOWN:
        return get_initial_prompt(config=config)

    return draft_prompt
