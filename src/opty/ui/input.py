from typing import List

from rich.panel import Panel
from rich.rule import Rule

from opty.intelligence.prompt_builder import PromptQuestion
from opty.ui.console import console


def wait_for_user_prompt(label: str, choices: list[str] | None = None) -> str:
    console.print(label)
    while True:
        user_input = input("").strip()
        if choices is None or user_input in choices:
            return user_input
        console.print(
            f"[red]Invalid choice. Please enter one of: {', '.join(choices)}[/red]"
        )


def multiline_input(prompt_label: str) -> str:
    console.print(f"  [dim]Type or paste your content. Press Enter twice to finish:[/dim]")
    console.print()
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    # Strip the trailing blank line used as sentinel
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def get_prompt_description() -> str:
    console.print()
    console.print(
        Panel(
            "[bold]Step 1[/bold] — [cyan]Describe your prompt[/cyan]\n\n"
            "Describe what you want your prompt to do. Be as specific as possible — "
            "include the task, desired tone, output format, and any constraints.\n\n"
            '[dim]Example: "A prompt that extracts action items from meeting notes '
            'and returns them as a numbered list with owner and due date."[/dim]',
            border_style="dim",
            padding=(1, 2),
        )
    )
    console.print()
    return wait_for_user_prompt("[bold cyan]Description[/bold cyan]")


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


def prompt_user_to_save_output() -> str:
    file_name = wait_for_user_prompt(
        "[yellow] ->[/yellow] Enter filename to save prompt (leave blank if you don't want to save it):"
    )
    return file_name


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
        answer = wait_for_user_prompt(f"  [yellow]{i}.[/yellow] {q.text}")
        answered.append(PromptQuestion(text=q.text, answer=answer))

    return answered
