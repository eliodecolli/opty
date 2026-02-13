from pathlib import Path
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text

from opty.intelligence.prompt_builder import PromptBuilder, PromptStep, PromptQuestion
from opty.intelligence.prompt_refiner import PromptRefineConfig
from opty.intelligence import create_builder, create_refiner
from opty.core import load_config

_CONFIG_PATH = Path("opty.config.yaml")

console = Console()


def render_header() -> None:
    title = Text("opty", style="bold cyan", justify="center")
    subtitle = Text("prompt optimization via chain-of-thought", style="dim", justify="center")
    console.print(Panel(Text.assemble(title, "\n", subtitle), border_style="cyan", padding=(1, 4)))


def choose_draft_source() -> str | None:
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

    choice = Prompt.ask(
        "[bold orange1]Choice[/bold orange1]",
        choices=["1", "2"],
        show_choices=False,
    )

    if choice == "1":
        console.print()
        path_str = Prompt.ask("[bold orange1]Path to prompt file[/bold orange1]").strip()
        path = Path(path_str).expanduser()
        if not path.is_file():
            console.print(f"[red]File not found:[/red] {path}")
            return None
        return path.read_text()

    return ""  # sentinel: build interactively


def get_prompt_description() -> str:
    console.print()
    console.print(
        Panel(
            "[bold]Step 1[/bold] — [cyan]Describe your prompt[/cyan]\n\n"
            "Describe what you want your prompt to do. Be as specific as possible — "
            "include the task, desired tone, output format, and any constraints.\n\n"
            "[dim]Example: \"A prompt that extracts action items from meeting notes "
            "and returns them as a numbered list with owner and due date.\"[/dim]",
            border_style="dim",
            padding=(1, 2),
        )
    )
    console.print()
    return Prompt.ask("[bold cyan]Description[/bold cyan]").strip()


def collect_answers(questions: List[PromptQuestion]) -> List[PromptQuestion]:
    console.print()
    console.print(
        Panel(
            "[bold]Follow-up questions[/bold]\n\n"
            "A few more details will help generate a better prompt.",
            border_style="yellow",
            padding=(1, 2),
        )
    )
    console.print()

    answered = []
    for i, q in enumerate(questions, 1):
        answer = Prompt.ask(f"  [yellow]{i}.[/yellow] {q.text}").strip()
        answered.append(PromptQuestion(text=q.text, answer=answer))

    return answered


def prompt_user_to_save_output() -> str:
    file_name = Prompt.ask(f"[yellow] ->[/yellow] Enter filename to save prompt (leave blank if you don't want to save it):").strip()
    return file_name


def multiline_input(prompt_label: str) -> str:
    console.print(f"  [dim]Press Enter twice to finish.[/dim]")
    console.print()
    lines = []
    while True:
        line = console.input(f"  {prompt_label} ")
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    # Strip the trailing blank line used as sentinel
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def get_example_input() -> str:
    console.print()
    console.print(
        Panel(
            "[bold]Step 2[/bold] — [cyan]Example input[/cyan]\n\n"
            "Provide a sample input that your prompt will receive. "
            "This will be used to test and refine the generated prompt.",
            border_style="dim",
            padding=(1, 2),
        )
    )
    console.print()
    return multiline_input("[bold cyan]>[/bold cyan]")


def get_example_output() -> str:
    console.print()
    console.print(
        Panel(
            "[bold]Step 3[/bold] — [cyan]Expected output[/cyan]\n\n"
            "Provide the ideal output you would expect for the input above. "
            "This is the target your prompt will be optimized against.",
            border_style="dim",
            padding=(1, 2),
        )
    )
    console.print()
    return multiline_input("[bold cyan]>[/bold cyan]")


def display_prompt(prompt_text: str, title: str, border_style: str = "cyan") -> None:
    console.print()
    console.print(Rule(f"[{border_style}]{title}[/{border_style}]", style=border_style))
    console.print()
    console.print(
        Panel(
            prompt_text,
            border_style=border_style,
            padding=(1, 2),
            title=f"[bold {border_style}]Content[/bold {border_style}]",
            title_align="left",
        )
    )
    console.print()

def display_llm_error(error: str) -> None:
    console.print()
    console.print(
      Panel(
          error,
          title="[bold red]Error - Invalid LLM Response[/bold red]",
          title_align="left",
          border_style="red",
          padding=(1, 2),
      )
    )
    console.print()

def build_prompt_interactively(builder: PromptBuilder, description: str) -> str | None:
    questions: List[PromptQuestion] | None = None

    while True:
        step = PromptStep(prompt_description=description, questions=questions)

        with Live(Spinner("dots", text=" Drafting prompt..."), console=console, transient=True):
            response = builder.step(step)

        if response.error:
            display_llm_error(error=response.error)
            return None

        if response.output:
            display_prompt(response.output, title="Draft Prompt")
            return response.output

        if response.questions:
            questions = collect_answers(response.questions)
        else:
            console.print("[red]Unexpected: no output and no questions returned.[/red]")
            return None


def main() -> None:
    try:
        config = load_config(_CONFIG_PATH)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    console.clear()
    render_header()

    draft_source = choose_draft_source()
    if draft_source is None:
        return

    console.print()
    console.print(Rule(style="dim"))

    if draft_source:
        # Option 1: loaded from file
        draft_prompt = draft_source
        display_prompt(draft_prompt, title="Draft Prompt")
    else:
        # Option 2: build interactively
        description = get_prompt_description()
        console.print()
        console.print(Rule(style="dim"))
        with create_builder(config["builder"]) as build:
          draft_prompt = build_prompt_interactively(build, description)

        if not draft_prompt:
            return

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
          with Live(Spinner("dots", text=f" Step {i} — optimizing..."), console=console, transient=True):
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
              console.print()
              console.print(
                  Panel(
                      step.error,
                      title="[bold red]Error[/bold red]",
                      title_align="left",
                      border_style="red",
                      padding=(1, 2),
                  )
              )
              break

          display_prompt(step.updated_prompt, title=f"Updated Prompt — step {i}", border_style="yellow")
          final_prompt = step.updated_prompt

          if step.complete:
              break

      display_prompt(final_prompt, title="Optimized Prompt", border_style="green")
      with open(prompt_user_to_save_output(), "w") as f:
          f.write(final_prompt)
