"""
cli.py — prompt-forge CLI entry point.

Usage examples:
  pf "build a JWT auth middleware in Python"
  pf "fix race condition in worker pool" --type debug
  pf "review this Express.js route handler" --lang javascript
  pf --interactive
  pf --list-types
"""

from __future__ import annotations
import sys
import subprocess

import click

from .classifier import detect_task, detect_language
from .templates import build_prompt, TEMPLATES

# ANSI colours
_C = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "cyan":    "\033[96m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "magenta": "\033[95m",
    "blue":    "\033[94m",
    "red":     "\033[91m",
    "dim":     "\033[2m",
}

TASK_DESCRIPTIONS = {
    "implement": "Build something new from a description",
    "debug":     "Diagnose and fix a bug or unexpected behaviour",
    "refactor":  "Improve existing code without changing behaviour",
    "review":    "Critique code for quality, correctness, and security",
    "design":    "Architect a system, API, or data model",
    "test":      "Write comprehensive tests for code or behaviour",
    "optimize":  "Improve performance or resource usage",
    "explain":   "Understand and document existing code",
    "security":  "Audit for vulnerabilities and harden code",
}


def _print_banner():
    click.echo(
        f"\n{_C['bold']}{_C['cyan']}╔══════════════════════════════════════╗\n"
        f"║    prompt-forge  ·  Senior Dev AI    ║\n"
        f"╚══════════════════════════════════════╝{_C['reset']}\n"
    )


def _copy_to_clipboard(text: str) -> bool:
    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            return True
        elif sys.platform.startswith("linux"):
            subprocess.run(["xclip", "-selection", "clipboard"],
                           input=text.encode(), check=True)
            return True
    except Exception:
        pass
    return False


def _print_result(prompt: str, task_type: str, lang: str | None,
                  *, copy: bool, raw: bool):
    if raw:
        click.echo(prompt)
        return

    # Header
    click.echo(
        f"\n{_C['bold']}{_C['green']}{'─'*60}{_C['reset']}\n"
        f"{_C['bold']}Task type : {_C['cyan']}{task_type.upper()}{_C['reset']}"
        + (f"   {_C['dim']}lang: {lang}{_C['reset']}" if lang else "")
        + f"\n{_C['bold']}{_C['green']}{'─'*60}{_C['reset']}\n"
    )

    # Prompt body
    click.echo(prompt)

    # Footer
    click.echo(f"\n{_C['bold']}{_C['green']}{'─'*60}{_C['reset']}")

    if copy:
        ok = _copy_to_clipboard(prompt)
        if ok:
            click.echo(
                f"{_C['green']}✓ Prompt copied to clipboard!{_C['reset']}"
            )
        else:
            click.echo(
                f"{_C['yellow']}⚠  Could not copy to clipboard "
                f"(install pbcopy/xclip){_C['reset']}"
            )

    click.echo(
        f"{_C['dim']}Paste this prompt into ChatGPT, Claude, Gemini, "
        f"or any other AI.{_C['reset']}\n"
    )


# ── Interactive wizard ────────────────────────────────────────────────────────

def _interactive():
    _print_banner()

    click.echo(f"{_C['bold']}What do you want to do?{_C['reset']}\n")

    # Show task type menu
    for i, (t, desc) in enumerate(TASK_DESCRIPTIONS.items(), 1):
        click.echo(
            f"  {_C['cyan']}{i:2}.{_C['reset']}  "
            f"{_C['bold']}{t:<12}{_C['reset']} {_C['dim']}{desc}{_C['reset']}"
        )

    click.echo()
    choice = click.prompt(
        f"{_C['yellow']}Select task type (1-{len(TASK_DESCRIPTIONS)} or name){_C['reset']}",
        default="auto",
    )

    # Resolve choice
    types_list = list(TASK_DESCRIPTIONS.keys())
    if choice.isdigit() and 1 <= int(choice) <= len(types_list):
        task_type = types_list[int(choice) - 1]
    elif choice.lower() in TASK_DESCRIPTIONS:
        task_type = choice.lower()
    else:
        task_type = None  # will auto-detect

    click.echo()
    task_desc = click.prompt(
        f"{_C['yellow']}Describe your task{_C['reset']} "
        f"{_C['dim']}(be specific — more detail = better prompt){_C['reset']}\n❯"
    )

    lang_input = click.prompt(
        f"\n{_C['yellow']}Language / framework{_C['reset']} "
        f"{_C['dim']}(or press Enter to auto-detect){_C['reset']}\n❯",
        default="",
    )

    copy_flag = click.confirm(
        f"\n{_C['yellow']}Copy prompt to clipboard?{_C['reset']}",
        default=True,
    )

    # Resolve task type
    if task_type is None:
        task_type = detect_task(task_desc)
        click.echo(
            f"\n{_C['dim']}Auto-detected task type: "
            f"{_C['cyan']}{task_type}{_C['reset']}"
        )

    lang = lang_input.strip() or detect_language(task_desc)
    ctx = {"task": task_desc.strip(), "language": lang}
    prompt = build_prompt(task_type, ctx)
    _print_result(prompt, task_type, lang, copy=copy_flag, raw=False)


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("task", required=False)
@click.option(
    "--type", "-t", "task_type",
    type=click.Choice(list(TEMPLATES.keys()), case_sensitive=False),
    default=None,
    help="Override auto-detected task type.",
)
@click.option("--lang", "-l", default=None,
              help="Language or framework (e.g. python, typescript, rust).")
@click.option("--copy", "-c", is_flag=True, default=False,
              help="Copy the generated prompt to clipboard.")
@click.option("--raw", is_flag=True, default=False,
              help="Print prompt only — no formatting, headers, or colour.")
@click.option("--interactive", "-i", "interactive_mode", is_flag=True,
              default=False, help="Launch the interactive wizard.")
@click.option("--list-types", is_flag=True, default=False,
              help="Show all available task types and exit.")
@click.version_option(package_name="prompt-forge")
def main(task, task_type, lang, copy, raw, interactive_mode, list_types):
    """
    prompt-forge — Generate senior-dev quality prompts instantly.

    \b
    Quick examples:
      pf "build a rate-limiter middleware in Python"
      pf "fix the memory leak in the connection pool" --type debug
      pf "review this React authentication hook" --lang typescript --copy
      pf --interactive

    \b
    The generated prompt tells the AI to think like a senior engineer:
    edge cases, error handling, security, testability, and trade-offs.
    """
    if list_types:
        click.echo(f"\n{_C['bold']}Available task types:{_C['reset']}\n")
        for t, desc in TASK_DESCRIPTIONS.items():
            click.echo(
                f"  {_C['bold']}{_C['cyan']}{t:<12}{_C['reset']}"
                f"  {desc}"
            )
        click.echo()
        return

    if interactive_mode or not task:
        _interactive()
        return

    if not raw:
        _print_banner()

    # Resolve task type and language
    resolved_type = task_type or detect_task(task)
    resolved_lang = lang or detect_language(task)

    ctx = {"task": task.strip(), "language": resolved_lang}
    prompt = build_prompt(resolved_type, ctx)
    _print_result(prompt, resolved_type, resolved_lang, copy=copy, raw=raw)
