from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from opty.ui.console import console


def render_header() -> None:
    title = Text("opty", style="bold cyan", justify="center")
    subtitle = Text(
        "prompt optimization via chain-of-thought", style="dim", justify="center"
    )
    console.print(
        Panel(Text.assemble(title, "\n", subtitle), border_style="cyan", padding=(1, 4))
    )


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


def display_error(error: str, title: str = "Error") -> None:
    console.print()
    console.print(
        Panel(
            error,
            title=f"[bold red]{title}[/bold red]",
            title_align="left",
            border_style="red",
            padding=(1, 2),
        )
    )
    console.print()


def display_llm_error(error: str, raw_response: str | None = None) -> None:
    complete_error = error if not raw_response else f"{error}\n\n{raw_response}"
    display_error(complete_error, title="Error - Invalid LLM Response")
