"""Tests for prompt_forge.cli — end-to-end CLI behaviour via CliRunner."""

import pytest
from click.testing import CliRunner
from prompt_forge.cli import main


@pytest.fixture
def runner():
    return CliRunner()


# ── Basic invocation ──────────────────────────────────────────────────────────

class TestCLIBasics:

    def test_help_exits_zero(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0

    def test_version_exits_zero(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_list_types_exits_zero(self, runner):
        result = runner.invoke(main, ["--list-types"])
        assert result.exit_code == 0

    def test_list_types_shows_all_nine_types(self, runner):
        result = runner.invoke(main, ["--list-types"])
        for t in ("implement", "debug", "refactor", "review",
                  "design", "test", "optimize", "explain", "security"):
            assert t in result.output


# ── Enhance mode (default) ────────────────────────────────────────────────────

class TestEnhanceMode:

    def test_enhance_exits_zero(self, runner):
        result = runner.invoke(main, ["build a rate limiter", "--raw"])
        assert result.exit_code == 0

    def test_enhance_output_contains_role(self, runner):
        result = runner.invoke(main, ["build a rate limiter", "--raw"])
        assert "You are a" in result.output

    def test_enhance_output_contains_deliver_section(self, runner):
        result = runner.invoke(main, ["build a rate limiter", "--raw"])
        assert "Deliver" in result.output

    def test_enhance_output_contains_task_text(self, runner):
        result = runner.invoke(main, ["build a canary-value service", "--raw"])
        assert "canary-value" in result.output

    def test_enhance_detects_python_from_fastapi(self, runner):
        result = runner.invoke(main, ["build auth middleware in FastAPI", "--raw"])
        assert "python" in result.output.lower()

    def test_enhance_injects_auth_concept_requirements(self, runner):
        result = runner.invoke(main, ["build JWT auth middleware", "--raw"])
        assert "algorithm" in result.output.lower()

    def test_enhance_injects_sql_injection_requirement(self, runner):
        result = runner.invoke(main, ["write a SQL search query", "--raw"])
        assert "injection" in result.output.lower() or "parameteris" in result.output.lower()


# ── Template mode (--template) ────────────────────────────────────────────────

class TestTemplateMode:

    def test_template_flag_exits_zero(self, runner):
        result = runner.invoke(main, ["build a service", "--template", "--raw"])
        assert result.exit_code == 0

    def test_template_output_contains_checklist(self, runner):
        result = runner.invoke(main, ["build a service", "--template", "--raw"])
        assert "Senior Dev Checklist" in result.output

    def test_template_output_does_not_contain_deliver_heading(self, runner):
        """Template uses 'Output format', not 'Deliver'."""
        result = runner.invoke(main, ["build a service", "--template", "--raw"])
        assert "Output format" in result.output


# ── --type override ───────────────────────────────────────────────────────────

class TestTypeOverride:

    def test_debug_type_shows_reproduction_section(self, runner):
        result = runner.invoke(main, ["fix something", "--type", "debug", "--raw"])
        assert "Reproduction" in result.output

    def test_design_type_shows_decision_log(self, runner):
        result = runner.invoke(main, ["plan a system", "--type", "design", "--raw"])
        assert "Decision log" in result.output

    def test_security_type_shows_owasp(self, runner):
        result = runner.invoke(main, ["check this code", "--type", "security", "--raw"])
        assert "OWASP" in result.output

    def test_invalid_type_shows_error(self, runner):
        result = runner.invoke(main, ["do something", "--type", "nonexistent"])
        assert result.exit_code != 0


# ── --lang override ───────────────────────────────────────────────────────────

class TestLangOverride:

    def test_lang_flag_appears_in_output(self, runner):
        result = runner.invoke(main, ["build a service", "--lang", "rust", "--raw"])
        assert "rust" in result.output.lower()

    def test_lang_flag_overrides_auto_detection(self, runner):
        # prompt says "Python" but --lang says typescript
        result = runner.invoke(main, ["build a Python service", "--lang", "typescript", "--raw"])
        assert "typescript" in result.output.lower()


# ── --raw flag ────────────────────────────────────────────────────────────────

class TestRawFlag:

    def test_raw_output_contains_no_ansi_escape(self, runner):
        result = runner.invoke(main, ["build a service", "--raw"])
        assert "\033[" not in result.output

    def test_without_raw_contains_banner(self, runner):
        result = runner.invoke(main, ["build a service"])
        assert "prompt-forge" in result.output.lower()


# ── Auto-detection accuracy (regression suite) ───────────────────────────────

class TestAutoDetectionRegression:

    @pytest.mark.parametrize("prompt,expected_fragment", [
        ("build auth middleware in FastAPI",          "implement"),
        ("fix race condition in worker pool",         "debug"),
        ("refactor the payment service",              "refactor"),
        ("review this React authentication hook",     "review"),
        ("design a multi-tenant SaaS schema",         "design"),
        ("write unit tests for the billing module",   "test"),
        ("optimize the slow SQL dashboard query",     "optimize"),
        ("explain how the event loop works",          "explain"),
        ("audit this endpoint for SQL injection",     "security"),
    ])
    def test_correct_type_detected(self, runner, prompt, expected_fragment):
        result = runner.invoke(main, [prompt])
        assert expected_fragment in result.output.lower(), (
            f"Expected '{expected_fragment}' in output for prompt: {prompt!r}\n"
            f"Output was:\n{result.output[:400]}"
        )
