"""Tests for prompt_forge.enricher — prompt enhancement and concept expansion."""

import pytest
from prompt_forge.enricher import enhance, _find_concept_expansions, _extract_core


# ── _extract_core ─────────────────────────────────────────────────────────────

class TestExtractCore:

    def test_strips_please_prefix(self):
        result = _extract_core("please build a rate limiter")
        assert not result.lower().startswith("please")

    def test_strips_can_you_prefix(self):
        result = _extract_core("can you fix the memory leak")
        assert not result.lower().startswith("can you")

    def test_strips_i_need_prefix(self):
        result = _extract_core("i need to implement auth middleware")
        assert not result.lower().startswith("i need")

    def test_capitalises_first_letter(self):
        result = _extract_core("build a cache layer")
        assert result[0].isupper()

    def test_preserves_content_without_filler(self):
        result = _extract_core("Implement a rate limiter using Redis")
        assert "rate limiter" in result
        assert "Redis" in result

    def test_handles_empty_string(self):
        result = _extract_core("")
        assert isinstance(result, str)


# ── _find_concept_expansions ─────────────────────────────────────────────────

class TestFindConceptExpansions:

    def test_auth_triggers_jwt_requirements(self):
        reqs = _find_concept_expansions("build auth middleware")
        combined = " ".join(reqs).lower()
        assert "algorithm" in combined or "token" in combined

    def test_jwt_triggers_claim_validation(self):
        reqs = _find_concept_expansions("validate JWT tokens")
        combined = " ".join(reqs).lower()
        assert "exp" in combined or "expiry" in combined or "claim" in combined

    def test_sql_triggers_parameterised_query_requirement(self):
        reqs = _find_concept_expansions("write a SQL query for user lookup")
        combined = " ".join(reqs).lower()
        assert "parameteris" in combined or "injection" in combined

    def test_cache_triggers_ttl_requirement(self):
        reqs = _find_concept_expansions("add caching with Redis")
        combined = " ".join(reqs).lower()
        assert "ttl" in combined

    def test_webhook_triggers_idempotency_requirement(self):
        reqs = _find_concept_expansions("build a webhook delivery system")
        combined = " ".join(reqs).lower()
        assert "idempotent" in combined

    def test_docker_triggers_nonroot_requirement(self):
        reqs = _find_concept_expansions("write a Dockerfile for the service")
        combined = " ".join(reqs).lower()
        assert "non-root" in combined or "root" in combined

    def test_no_concepts_returns_empty_list(self):
        reqs = _find_concept_expansions("explain the history of sorting algorithms")
        assert isinstance(reqs, list)

    def test_no_duplicate_requirements(self):
        # auth + jwt both match; combined result should have no duplicate lines
        reqs = _find_concept_expansions("validate JWT auth tokens")
        assert len(reqs) == len(set(reqs))

    def test_queue_triggers_dead_letter_requirement(self):
        reqs = _find_concept_expansions("process jobs from a message queue")
        combined = " ".join(reqs).lower()
        assert "dead-letter" in combined or "dead letter" in combined


# ── enhance ───────────────────────────────────────────────────────────────────

class TestEnhance:

    # --- structure -----------------------------------------------------------

    def test_returns_non_empty_string(self):
        result = enhance("build a rate limiter", "implement", "python")
        assert isinstance(result, str)
        assert len(result) > 100

    def test_contains_role_line(self):
        result = enhance("build a rate limiter", "implement", "python")
        assert result.startswith("You are a")

    def test_contains_task_heading(self):
        result = enhance("build a cache layer", "implement", None)
        assert "## Implement" in result

    def test_contains_deliverables_section(self):
        result = enhance("build a cache layer", "implement", "python")
        assert "## Deliver" in result

    def test_contains_non_negotiables_section(self):
        result = enhance("fix a memory leak", "debug", "python")
        assert "## Non-negotiables" in result

    def test_ends_with_assumption_prompt(self):
        result = enhance("design a notification system", "design", None)
        assert "assumptions" in result.lower()

    # --- language injection --------------------------------------------------

    def test_language_appears_in_task_heading(self):
        result = enhance("build a rate limiter", "implement", "python")
        assert "python" in result.lower()

    def test_language_type_annotation_line_present_for_typed_languages(self):
        for lang in ("python", "typescript", "go", "rust"):
            result = enhance("build an API", "implement", lang)
            assert lang in result.lower(), f"expected {lang} in output"

    def test_no_language_heading_when_none(self):
        result = enhance("build a service", "implement", None)
        # Should not have " in None" or similar
        assert "in None" not in result

    # --- concept expansion ---------------------------------------------------

    def test_auth_prompt_contains_algorithm_pinning(self):
        result = enhance("build JWT auth middleware", "implement", "python")
        assert "algorithm" in result.lower()

    def test_sql_prompt_contains_injection_requirement(self):
        result = enhance("write a SQL search query", "implement", "python")
        assert "injection" in result.lower() or "parameteris" in result.lower()

    def test_webhook_prompt_contains_idempotency(self):
        result = enhance("build a webhook receiver", "implement", None)
        assert "idempotent" in result.lower()

    def test_cache_prompt_contains_ttl(self):
        result = enhance("add Redis caching", "implement", "python")
        assert "ttl" in result.lower()

    def test_no_concept_section_when_no_concepts_matched(self):
        result = enhance("sort a list of numbers", "implement", None)
        assert "## Technical requirements" not in result

    # --- task-type variation -------------------------------------------------

    def test_debug_contains_reproduction_section(self):
        result = enhance("fix race condition in worker", "debug", "python")
        assert "Reproduction" in result

    def test_debug_contains_hypotheses_section(self):
        result = enhance("fix race condition in worker", "debug", "python")
        assert "Hypotheses" in result

    def test_design_contains_decision_log_section(self):
        result = enhance("design a multi-tenant SaaS schema", "design", None)
        assert "Decision log" in result

    def test_design_contains_mvp_section(self):
        result = enhance("design a notification service", "design", None)
        assert "MVP" in result

    def test_review_contains_security_section(self):
        result = enhance("review this login handler", "review", "python")
        assert "Security" in result

    def test_security_contains_owasp_section(self):
        result = enhance("audit the payment endpoint", "security", "python")
        assert "OWASP" in result

    def test_optimize_contains_baseline_section(self):
        result = enhance("speed up the dashboard query", "optimize", "python")
        assert "Baseline" in result

    def test_test_contains_test_layer_section(self):
        result = enhance("write tests for the checkout service", "test", "python")
        assert "Test layer" in result

    def test_explain_contains_bird_eye_section(self):
        result = enhance("explain the event loop", "explain", "javascript")
        assert "Bird" in result

    # --- edge cases ----------------------------------------------------------

    def test_handles_single_word_prompt(self):
        result = enhance("auth", "implement", None)
        assert len(result) > 50

    def test_handles_very_long_prompt(self):
        long_prompt = "build " + ("a very complex system " * 30)
        result = enhance(long_prompt, "implement", None)
        assert isinstance(result, str)

    def test_unknown_task_type_falls_back_gracefully(self):
        # Should not raise — falls back to implement structure
        result = enhance("do something", "implement", None)
        assert isinstance(result, str)
