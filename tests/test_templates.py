"""Tests for prompt_forge.templates — structured framework generation."""

import pytest
from prompt_forge.templates import build_prompt, TEMPLATES


ALL_TYPES = list(TEMPLATES.keys())


class TestBuildPrompt:

    # --- coverage -----------------------------------------------------------

    @pytest.mark.parametrize("task_type", ALL_TYPES)
    def test_all_types_return_non_empty_string(self, task_type):
        result = build_prompt(task_type, {"task": "do something", "language": None})
        assert isinstance(result, str) and len(result) > 50

    @pytest.mark.parametrize("task_type", ALL_TYPES)
    def test_all_types_contain_senior_dev_checklist(self, task_type):
        result = build_prompt(task_type, {"task": "do something", "language": None})
        assert "Senior Dev Checklist" in result

    @pytest.mark.parametrize("task_type", ALL_TYPES)
    def test_all_types_contain_task_text(self, task_type):
        task_text = "implement a unique canary value"
        result = build_prompt(task_type, {"task": task_text, "language": None})
        assert task_text in result

    # --- language injection -------------------------------------------------

    def test_implement_includes_language_when_provided(self):
        result = build_prompt("implement", {"task": "build a service", "language": "rust"})
        assert "rust" in result.lower()

    def test_implement_no_language_marker_when_none(self):
        result = build_prompt("implement", {"task": "build a service", "language": None})
        assert "in **None**" not in result

    # --- specific type content ----------------------------------------------

    def test_implement_mentions_output_format(self):
        result = build_prompt("implement", {"task": "x", "language": None})
        assert "Output format" in result

    def test_debug_contains_step_1(self):
        result = build_prompt("debug", {"task": "x", "language": None})
        assert "Step 1" in result

    def test_design_contains_enumerate_approaches(self):
        result = build_prompt("design", {"task": "x", "language": None})
        assert "Enumerate" in result or "approaches" in result.lower()

    def test_security_contains_owasp(self):
        result = build_prompt("security", {"task": "x", "language": None})
        assert "OWASP" in result

    def test_review_contains_rubric(self):
        result = build_prompt("review", {"task": "x", "language": None})
        assert "rubric" in result.lower() or "Correctness" in result

    def test_test_contains_coverage_pyramid(self):
        result = build_prompt("test", {"task": "x", "language": None})
        assert "pyramid" in result.lower() or "Unit test" in result

    def test_optimize_contains_measure_first_rule(self):
        result = build_prompt("optimize", {"task": "x", "language": None})
        assert "Measure" in result or "measure" in result

    def test_explain_contains_bird_eye(self):
        result = build_prompt("explain", {"task": "x", "language": None})
        assert "Bird" in result

    def test_refactor_warns_against_rewrite(self):
        result = build_prompt("refactor", {"task": "x", "language": None})
        assert "rewrite" in result.lower()

    # --- unknown task type --------------------------------------------------

    def test_unknown_type_falls_back_to_implement(self):
        result = build_prompt("unknown_type", {"task": "do something", "language": None})
        assert isinstance(result, str) and len(result) > 50


class TestTemplatesDict:

    def test_all_expected_types_present(self):
        expected = {"implement", "debug", "refactor", "review",
                    "design", "test", "optimize", "explain", "security"}
        assert expected == set(TEMPLATES.keys())

    def test_all_values_are_callable(self):
        for name, fn in TEMPLATES.items():
            assert callable(fn), f"TEMPLATES['{name}'] is not callable"
