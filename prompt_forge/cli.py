"""
cli.py — prompt-forge CLI entry point.

Default mode:  enhance — rewrites your rough prompt as a senior dev would write it.
Template mode: add --template for the structured framework instead.

Usage examples:
  pf "build JWT auth middleware in Python"
  pf "fix race condition in worker pool" --type debug
  pf "review this Express.js route handler" --copy
  pf "auth middleware" --template
  pf --interactive
  pf --list-types
"""

from __future__ import annotations
import sys
import subprocess

import click

from .classifier import detect_task, detect_language
from .enricher   import enhance
from .templates  import build_prompt, TEMPLATES

# ── ANSI colours ──────────────────────────────────────────────────────────────

_C = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "cyan":    "\033[96m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "dim":     "\033[2m",
}

# ── Task metadata ─────────────────────────────────────────────────────────────

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

# ── Clipboard ─────────────────────────────────────────────────────────────────

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

# ── Banner ────────────────────────────────────────────────────────────────────

def _print_banner():
    click.echo(
        f"\n{_C['bold']}{_C['cyan']}╔══════════════════════════════════════╗\n"
        f"║    prompt-forge  ·  Senior Dev AI    ║\n"
        f"╚══════════════════════════════════════╝{_C['reset']}\n"
    )

# ── Print result ──────────────────────────────────────────────────────────────

def _print_result(prompt: str, task_type: str, lang: str | None,
                  mode: str, *, copy: bool, raw: bool):
    if raw:
        click.echo(prompt)
        return

    mode_label = "enhanced" if mode == "enhance" else "template"
    click.echo(
        f"\n{_C['bold']}{_C['green']}{'─'*60}{_C['reset']}\n"
        f"{_C['bold']}Task : {_C['cyan']}{task_type.upper()}{_C['reset']}"
        + (f"   {_C['dim']}lang: {lang}{_C['reset']}" if lang else "")
        + f"   {_C['dim']}mode: {mode_label}{_C['reset']}"
        + f"\n{_C['bold']}{_C['green']}{'─'*60}{_C['reset']}\n"
    )

    click.echo(prompt)

    click.echo(f"\n{_C['bold']}{_C['green']}{'─'*60}{_C['reset']}")

    if copy:
        ok = _copy_to_clipboard(prompt)
        if ok:
            click.echo(f"{_C['green']}Prompt copied to clipboard.{_C['reset']}")
        else:
            click.echo(
                f"{_C['yellow']}Could not copy to clipboard — install pbcopy (macOS) or xclip (Linux).{_C['reset']}"
            )

    click.echo(
        f"{_C['dim']}Paste into ChatGPT, Claude, Gemini, or any AI.{_C['reset']}\n"
    )

# ── Interactive wizard ────────────────────────────────────────────────────────

def _interactive():
    _print_banner()

    click.echo(f"{_C['bold']}Select task type:{_C['reset']}\n")
    for i, (t, desc) in enumerate(TASK_DESCRIPTIONS.items(), 1):
        click.echo(
            f"  {_C['cyan']}{i:2}.{_C['reset']}  "
            f"{_C['bold']}{t:<12}{_C['reset']} {_C['dim']}{desc}{_C['reset']}"
        )

    click.echo()
    choice = click.prompt(
        f"{_C['yellow']}Task type (1-{len(TASK_DESCRIPTIONS)} or name, Enter = auto-detect){_C['reset']}",
        default="auto",
    )

    types_list = list(TASK_DESCRIPTIONS.keys())
    if choice.isdigit() and 1 <= int(choice) <= len(types_list):
        task_type = types_list[int(choice) - 1]
    elif choice.lower() in TASK_DESCRIPTIONS:
        task_type = choice.lower()
    else:
        task_type = None

    click.echo()
    task_desc = click.prompt(
        f"{_C['yellow']}Describe your task{_C['reset']} "
        f"{_C['dim']}(rough is fine — the tool will expand it){_C['reset']}\n>"
    )

    lang_input = click.prompt(
        f"\n{_C['yellow']}Language / framework{_C['reset']} "
        f"{_C['dim']}(Enter to auto-detect){_C['reset']}\n>",
        default="",
    )

    use_template = click.confirm(
        f"\n{_C['yellow']}Use template mode instead of enhanced rewrite?{_C['reset']}",
        default=False,
    )

    copy_flag = click.confirm(
        f"{_C['yellow']}Copy to clipboard?{_C['reset']}",
        default=True,
    )

    if task_type is None:
        task_type = detect_task(task_desc)
        click.echo(f"\n{_C['dim']}Detected task type: {_C['cyan']}{task_type}{_C['reset']}")

    lang = lang_input.strip() or detect_language(task_desc)

    if use_template:
        prompt = build_prompt(task_type, {"task": task_desc.strip(), "language": lang})
        mode = "template"
    else:
        prompt = enhance(task_desc.strip(), task_type, lang)
        mode = "enhance"

    _print_result(prompt, task_type, lang, mode, copy=copy_flag, raw=False)

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
              help="Language or framework (python, typescript, rust, …).")
@click.option("--copy", "-c", is_flag=True, default=False,
              help="Copy the generated prompt to clipboard.")
@click.option("--raw", is_flag=True, default=False,
              help="Print prompt only — no colour or headers.")
@click.option("--template", is_flag=True, default=False,
              help="Output a structured framework instead of an enhanced rewrite.")
@click.option("--interactive", "-i", "interactive_mode", is_flag=True,
              default=False, help="Launch the interactive wizard.")
@click.option("--list-types", is_flag=True, default=False,
              help="Show all task types and exit.")
@click.version_option(package_name="prompt-forge")
def main(task, task_type, lang, copy, raw, template, interactive_mode, list_types):
    """
    prompt-forge — Enhance and optimise your prompts like a senior engineer.

    \b
    Default: rewrites your rough prompt with full technical requirements,
    error-handling specs, edge cases, and deliverables — ready to paste.

    \b
    Examples:
      pf "build auth middleware in FastAPI"
      pf "fix memory leak in connection pool" --type debug --copy
      pf "review login route" --lang typescript
      pf "build rate limiter" --template     (framework mode)
      pf --interactive

    \b
    Add --template to get a structured thinking framework instead of a rewrite.
    """
    if list_types:
        click.echo(f"\n{_C['bold']}Available task types:{_C['reset']}\n")
        for t, desc in TASK_DESCRIPTIONS.items():
            click.echo(
                f"  {_C['bold']}{_C['cyan']}{t:<12}{_C['reset']}  {desc}"
            )
        click.echo()
        return

    if interactive_mode or not task:
        _interactive()
        return

    if not raw:
        _print_banner()

    resolved_type = task_type or detect_task(task)
    resolved_lang = lang or detect_language(task)

    if template:
        prompt = build_prompt(resolved_type, {"task": task.strip(), "language": resolved_lang})
        mode = "template"
    else:
        prompt = enhance(task.strip(), resolved_type, resolved_lang)
        mode = "enhance"

    _print_result(prompt, resolved_type, resolved_lang, mode, copy=copy, raw=raw)
