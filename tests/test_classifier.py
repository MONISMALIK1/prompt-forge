"""Tests for prompt_forge.classifier — task-type detection and language detection."""

import pytest
from prompt_forge.classifier import detect_task, detect_language


# ── detect_task ───────────────────────────────────────────────────────────────

class TestDetectTask:

    # --- implement -----------------------------------------------------------

    def test_build_verb_routes_to_implement(self):
        assert detect_task("build a rate limiter in Go") == "implement"

    def test_create_verb_routes_to_implement(self):
        assert detect_task("create a REST API with Express") == "implement"

    def test_implement_verb_routes_to_implement(self):
        assert detect_task("implement a distributed cache using Redis") == "implement"

    def test_build_auth_does_not_route_to_security(self):
        """'build auth middleware' must resolve to implement, not security."""
        assert detect_task("build JWT auth middleware in FastAPI") == "implement"

    def test_add_feature_routes_to_implement(self):
        assert detect_task("add pagination to the user list endpoint") == "implement"

    # --- debug ---------------------------------------------------------------

    def test_fix_verb_routes_to_debug(self):
        assert detect_task("fix the race condition in my worker pool") == "debug"

    def test_bug_keyword_routes_to_debug(self):
        assert detect_task("there is a bug in the payment processing flow") == "debug"

    def test_memory_leak_routes_to_debug(self):
        assert detect_task("debug memory leak in Python async workers") == "debug"

    def test_crash_keyword_routes_to_debug(self):
        assert detect_task("the server crashes on large file uploads") == "debug"

    # --- refactor ------------------------------------------------------------

    def test_refactor_verb_routes_to_refactor(self):
        assert detect_task("refactor the payment service to reduce duplication") == "refactor"

    def test_clean_up_routes_to_refactor(self):
        assert detect_task("clean up the database layer") == "refactor"

    # --- review --------------------------------------------------------------

    def test_review_verb_routes_to_review(self):
        assert detect_task("review this React authentication hook") == "review"

    def test_review_does_not_route_to_security_via_auth(self):
        """'review … auth hook' must not be hijacked by the security classifier."""
        assert detect_task("review this React authentication hook") == "review"

    def test_review_migration_routes_to_review(self):
        assert detect_task("review the database migration script") == "review"

    # --- design --------------------------------------------------------------

    def test_design_verb_routes_to_design(self):
        assert detect_task("design a multi-tenant SaaS database schema") == "design"

    def test_architecture_keyword_routes_to_design(self):
        assert detect_task("what architecture should I use for the notification service") == "design"

    # --- test ----------------------------------------------------------------

    def test_write_unit_tests_routes_to_test(self):
        assert detect_task("write unit tests for the billing module") == "test"

    def test_add_test_coverage_routes_to_test(self):
        assert detect_task("add test coverage for the checkout flow") == "test"

    def test_e2e_keyword_routes_to_test(self):
        assert detect_task("set up e2e tests with Playwright") == "test"

    # --- optimize ------------------------------------------------------------

    def test_optimize_verb_routes_to_optimize(self):
        assert detect_task("optimize the slow SQL query in the user dashboard") == "optimize"

    def test_slow_performance_routes_to_optimize(self):
        assert detect_task("the homepage is very slow, need to speed it up") == "optimize"

    # --- explain -------------------------------------------------------------

    def test_explain_verb_routes_to_explain(self):
        assert detect_task("explain how the event loop works in Node.js") == "explain"

    def test_walk_me_through_routes_to_explain(self):
        assert detect_task("walk me through the authentication flow") == "explain"

    # --- security ------------------------------------------------------------

    def test_audit_routes_to_security(self):
        assert detect_task("audit this login endpoint for SQL injection vulnerabilities") == "security"

    def test_security_keyword_routes_to_security(self):
        assert detect_task("check the API for XSS and CSRF vulnerabilities") == "security"

    # --- fallback ------------------------------------------------------------

    def test_empty_string_falls_back_to_implement(self):
        assert detect_task("") == "implement"

    def test_gibberish_falls_back_to_implement(self):
        assert detect_task("asdfghjkl qwerty") == "implement"


# ── detect_language ───────────────────────────────────────────────────────────

class TestDetectLanguage:

    def test_detects_python(self):
        assert detect_language("build auth middleware in FastAPI") == "python"

    def test_detects_typescript(self):
        assert detect_language("review this TypeScript service") == "typescript"

    def test_detects_javascript_via_react(self):
        assert detect_language("review this React hook") == "javascript"

    def test_detects_rust(self):
        assert detect_language("implement a Rust async runtime") == "rust"

    def test_detects_go(self):
        assert detect_language("build a rate limiter in golang") == "go"

    def test_detects_sql(self):
        assert detect_language("optimize the slow SQL query") == "sql"

    def test_detects_java(self):
        assert detect_language("refactor the Spring Boot service") == "java"

    def test_returns_none_when_no_language(self):
        assert detect_language("fix the bug in the pipeline") is None

    def test_returns_none_for_empty_string(self):
        assert detect_language("") is None
