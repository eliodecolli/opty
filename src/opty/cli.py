from pathlib import Path

from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner

from opty.core import load_config
from opty.intelligence import create_refiner
from opty.intelligence.prompt_refiner import PromptRefineConfig
from opty.ui.console import console
from opty.ui.display import display_llm_error, display_prompt, render_header
from opty.ui.flow import get_initial_prompt
from opty.ui.input import get_example_input, get_example_output, prompt_user_to_save_output

_CONFIG_PATH = Path("opty.config.yaml")


def main() -> None:
    try:
        config = load_config(_CONFIG_PATH)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    console.clear()
    render_header()

    # get the initial prompt to begin with
    draft_prompt = get_initial_prompt(config)
    if not draft_prompt:
        raise SystemExit(1)

    console.print(Rule(style="dim"))

    example_input = get_example_input()

    console.print()
    console.print(Rule(style="dim"))

    example_output = get_example_output()

    console.print()
    console.print(Rule(style="dim"))
    console.print()

    with create_refiner(config["refiner"]) as refiner:
        refine_config = PromptRefineConfig(
            prompt=draft_prompt,
            example_input=example_input,
            target_output=example_output,
        )

        final_prompt = draft_prompt
        gen = refiner(config=refine_config)
        i = 0

        # start the refinement process
        while True:
            i += 1
            with Live(
                Spinner("dots", text=f" Step {i} — optimizing..."),
                console=console,
                transient=True,
            ):
                step = next(gen, None)
            if step is None:
                break

            console.print()
            console.print(Rule(f"[dim]Step {i}[/dim]", style="dim"))

            if step.thinking:
                console.print()
                console.print(
                    Panel(
                        step.thinking,
                        title=f"[dim]Thinking — step {i}[/dim]",
                        title_align="left",
                        border_style="dim",
                        padding=(1, 2),
                    )
                )

            if step.error:
                display_llm_error(error=step.error, raw_response=step.raw_response)
                break

            display_prompt(
                step.updated_prompt,
                title=f"Updated Prompt — step {i}",
                border_style="yellow",
            )
            final_prompt = step.updated_prompt

            if step.complete:
                break

    display_prompt(final_prompt, title="Optimized Prompt", border_style="green")
    file_name = prompt_user_to_save_output()
    if file_name:
        with open(file_name, "w") as f:
            f.write(final_prompt)
