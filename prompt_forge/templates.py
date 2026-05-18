"""
templates.py — Senior-dev prompt templates, one per task type.

Each template is a callable that accepts a context dict and returns
the final prompt string.
"""

from __future__ import annotations
from string import Template


# ── Shared senior-dev footer ──────────────────────────────────────────────────

_SENIOR_FOOTER = """
─── Senior Dev Checklist ───────────────────────────────────────────────
Before you respond, think through each point silently:
  □  Edge cases — empty input, null/undefined, max size, concurrent access
  □  Error handling — specific exceptions, meaningful messages, no silent failures
  □  Security — input validation, injection risks, auth boundaries, secrets
  □  Performance — algorithmic complexity, N+1 queries, unnecessary allocations
  □  Testability — is the output easy to unit-test? are side effects isolated?
  □  Readability — clear naming, minimal nesting, single responsibility
  □  Backward compatibility — does this break existing callers or contracts?
Then produce your response.
────────────────────────────────────────────────────────────────────────""".strip()


# ── Templates ─────────────────────────────────────────────────────────────────

def _implement(ctx: dict) -> str:
    lang_hint = f" in **{ctx['language']}**" if ctx.get("language") else ""
    return f"""
You are a senior software engineer with 10+ years of experience.

## Task
Implement the following{lang_hint}:

> {ctx['task']}

## Requirements — think like a senior dev

**Functional**
- Implement the happy path cleanly and clearly.
- Handle all obvious edge cases (empty input, null values, boundary conditions,
  concurrent access if applicable).
- Return meaningful errors — never swallow exceptions silently.

**Non-functional**
- Aim for the simplest correct solution first; optimise only if there is a clear
  performance need.
- Keep functions/methods small and single-purpose.
- Use descriptive names — the code should read like prose.

**Security**
- Validate and sanitise all inputs before use.
- Avoid exposing internal implementation details in error messages.
- Flag any potential injection, auth, or privilege-escalation risk.

**Testing hooks**
- Structure the code so it can be unit-tested without mocking the world.
- Call out which parts you'd unit-test vs integration-test, and why.

**Output format**
1. Short explanation of your design choices (2–4 sentences).
2. Full implementation with inline comments on non-obvious decisions.
3. Example usage snippet.
4. Any caveats or follow-up work a reviewer should know about.

{_SENIOR_FOOTER}
""".strip()


def _debug(ctx: dict) -> str:
    lang_hint = f" ({ctx['language']})" if ctx.get("language") else ""
    return f"""
You are a senior software engineer doing a debugging session{lang_hint}.

## Problem
> {ctx['task']}

## Debugging approach — think like a senior dev

**Step 1 — Reproduce & Isolate**
- What is the smallest input / scenario that triggers the bug?
- Is the behaviour deterministic or intermittent?
- What changed recently that could have introduced this?

**Step 2 — Hypothesis**
- List the top 3 most likely root causes, ranked by probability.
- For each hypothesis, state what evidence would confirm or rule it out.

**Step 3 — Fix**
- Provide the minimal, surgical fix — do not refactor unrelated code.
- Explain *why* this fix works, not just *what* it does.
- Highlight any similar patterns elsewhere in the codebase that might
  have the same bug.

**Step 4 — Prevent recurrence**
- What test would have caught this bug before it reached production?
- Is there a linter rule, type annotation, or assertion that would
  prevent this class of bug?

**Output format**
1. Root cause diagnosis (2–3 sentences).
2. Fixed code (diff or full snippet).
3. Test case that proves the fix.
4. Prevention recommendation.

{_SENIOR_FOOTER}
""".strip()


def _refactor(ctx: dict) -> str:
    lang_hint = f" ({ctx['language']})" if ctx.get("language") else ""
    return f"""
You are a senior engineer performing a focused refactor{lang_hint}.

## Refactor target
> {ctx['task']}

## Constraints — think like a senior dev

**Non-negotiable rules**
- External behaviour must not change — this is a *refactor*, not a rewrite.
- Keep the diff as small as possible; resist scope creep.
- If you spot unrelated issues, note them in a "Future work" section —
  do NOT fix them now.

**Quality goals (pick what applies)**
- Reduce duplication — extract repeated logic into named abstractions.
- Improve naming — variables, functions, and classes should communicate intent.
- Simplify control flow — flatten nested conditionals, remove unnecessary flags.
- Improve separation of concerns — I/O, business logic, and presentation should
  be in different layers.
- Reduce coupling — dependencies should flow inward, not outward.

**Safety net**
- If tests exist, ensure they still pass after the refactor.
- If no tests exist, note which behaviour you'd cover before refactoring.

**Output format**
1. Summary of what changed and why (3–5 bullets).
2. Refactored code.
3. Before/after diff highlights for the most impactful changes.
4. Anything deliberately left out-of-scope.

{_SENIOR_FOOTER}
""".strip()


def _review(ctx: dict) -> str:
    lang_hint = f" ({ctx['language']})" if ctx.get("language") else ""
    return f"""
You are a principal engineer doing a thorough code review{lang_hint}.

## Code / PR to review
> {ctx['task']}

## Review rubric — think like a senior dev

Rate each area as  [+] Good  /  [~] Needs work  /  [!] Blocking issue:

| Area | Checklist |
|------|-----------|
| **Correctness** | Handles edge cases, no off-by-one, correct types |
| **Readability** | Clear names, low nesting, self-documenting |
| **Error handling** | All error paths explicit, no silent failures |
| **Security** | Input validation, no secret leakage, auth enforced |
| **Performance** | No obvious N+1, no unnecessary allocations, right data structures |
| **Testability** | Testable design, side effects isolated |
| **API / Interface** | Public surface minimal, backward-compatible |
| **Documentation** | Non-obvious code commented, public API documented |

**Tone guide**
- Be specific — "this can cause a race condition because…" not "this looks off".
- Suggest, don't mandate — offer the better pattern and explain why.
- Separate blocking issues from nice-to-haves clearly.

**Output format**
1. Overall verdict (Approve / Request changes / Needs discussion).
2. Blocking issues (if any).
3. Non-blocking suggestions grouped by area.
4. Positive callouts — what was done well.

{_SENIOR_FOOTER}
""".strip()


def _design(ctx: dict) -> str:
    lang_hint = f" using {ctx['language']}" if ctx.get("language") else ""
    return f"""
You are a staff engineer designing a system or component{lang_hint}.

## Design brief
> {ctx['task']}

## Design process — think like a senior dev

**1. Clarify requirements first**
Before proposing anything, state your assumptions about:
- Scale (users, requests/sec, data volume)
- Consistency vs availability trade-off (CAP theorem)
- Latency SLO (p99 acceptable latency)
- Operational constraints (team size, existing stack, budget)

**2. Enumerate approaches**
List 2–3 viable designs. For each:
- Key idea in one sentence
- Pros & cons
- When you'd choose it

**3. Recommended design**
Pick the best fit and detail it:
- Component diagram (ASCII or described)
- Data model / API contract
- Failure modes and how they're handled
- Scalability path (how does this hold up at 10× load?)

**4. Decision log**
Call out the top 3 decisions you made and the alternatives you rejected,
so future engineers understand *why* things are the way they are.

**5. MVP vs full design**
State what the minimal viable version looks like vs the full design —
most teams should ship the MVP first.

{_SENIOR_FOOTER}
""".strip()


def _test(ctx: dict) -> str:
    lang_hint = f" ({ctx['language']})" if ctx.get("language") else ""
    return f"""
You are a senior engineer writing a comprehensive test suite{lang_hint}.

## What to test
> {ctx['task']}

## Testing strategy — think like a senior dev

**Coverage pyramid**
- Unit tests: pure functions, isolated business logic — fast, no I/O.
- Integration tests: component boundaries, DB queries, API endpoints.
- E2E tests: critical user journeys only — kept minimal and stable.

**Test case categories to cover**
1. Happy path — typical valid input, expected output.
2. Edge cases — empty, null, boundary values, max/min.
3. Error paths — invalid input, network failure, permission denied.
4. Concurrent/race conditions — if the code has shared state.
5. Regression — any known past bugs should have a named test.

**Test quality rules**
- Each test should have one reason to fail (single assertion focus).
- Test names must describe *behaviour*, not implementation.
  Good : `test_transfer_fails_when_balance_insufficient`
  Avoid: `test_transfer_error`
- Avoid testing implementation details — test the public contract.
- No test should depend on the order of execution.

**Output format**
1. Testing strategy chosen and why.
2. Full test file with clear sections (arrange / act / assert pattern).
3. Any mocks/fixtures needed and why.
4. Coverage gaps you'd address in a follow-up.

{_SENIOR_FOOTER}
""".strip()


def _optimize(ctx: dict) -> str:
    lang_hint = f" ({ctx['language']})" if ctx.get("language") else ""
    return f"""
You are a senior performance engineer{lang_hint}.

## Optimization target
> {ctx['task']}

## Optimization process — think like a senior dev

**Rule 1 — Measure first, optimize second**
- What metric are we optimising? (latency p99, throughput, memory, CPU)
- What is the current baseline and what is the acceptable target?
- Do NOT guess — profile first. Describe what profiling approach you'd use.

**Rule 2 — Find the real bottleneck**
List the top 3 likely bottlenecks with reasoning:
- Algorithmic complexity (O(n²) hidden in a loop?)
- I/O bound (DB queries, network calls, disk reads?)
- Memory pressure (large allocations, GC pressure, cache misses?)
- Lock contention (threads waiting on mutexes?)

**Rule 3 — Optimise at the right layer**
Prefer in this order:
1. Algorithm / data structure change (biggest impact)
2. Caching (avoid repeated work)
3. Batching / async I/O (parallelise wait time)
4. Low-level micro-optimisation (last resort)

**Rule 4 — Preserve correctness**
- Every optimisation must leave the external behaviour unchanged.
- Add a benchmark or before/after measurement to prove the improvement.
- Document trade-offs: faster code that is harder to read needs a comment.

**Output format**
1. Profiling plan (what to measure and how).
2. Bottleneck diagnosis.
3. Optimised code with before/after complexity analysis.
4. Benchmark showing the improvement.

{_SENIOR_FOOTER}
""".strip()


def _explain(ctx: dict) -> str:
    lang_hint = f" ({ctx['language']})" if ctx.get("language") else ""
    return f"""
You are a senior engineer explaining code to a smart but unfamiliar reader{lang_hint}.

## What to explain
> {ctx['task']}

## Explanation style — think like a senior dev

**Levels of explanation**
Give all three levels:

1. **Bird's-eye** (1 paragraph) — What does this code *do* at a business level?
   What problem does it solve?

2. **Structural** — Walk through the main components/functions/classes.
   How do they interact? Draw a simple flow if helpful (ASCII is fine).

3. **Line-level** — For the 3–5 most non-obvious sections, explain:
   - *What* the code does
   - *Why* it does it this way (historical context, constraints, trade-offs)
   - What would break if this were changed naively

**Flag these explicitly**
- Footguns — subtle gotchas a future maintainer might trip over
- Dead code or commented-out blocks — why are they there?
- Implicit assumptions (global state, environment variables, execution order)
- Anything that looks wrong but is intentional

**Output format**
1. Bird's-eye summary.
2. Structural walkthrough with component diagram.
3. Annotated code with inline commentary on non-obvious parts.
4. Maintenance notes — what a new contributor must understand to safely modify this.

{_SENIOR_FOOTER}
""".strip()


def _security(ctx: dict) -> str:
    lang_hint = f" ({ctx['language']})" if ctx.get("language") else ""
    return f"""
You are a senior application security engineer doing a security review{lang_hint}.

## Target
> {ctx['task']}

## Security review checklist — think like a senior dev

**OWASP Top 10 scan**
Check each category and mark as  [+] Safe  /  [~] Needs review  /  [!] Vulnerable:

| # | Category | Finding |
|---|----------|---------|
| A01 | Broken Access Control | |
| A02 | Cryptographic Failures | |
| A03 | Injection (SQL, command, LDAP, XSS) | |
| A04 | Insecure Design | |
| A05 | Security Misconfiguration | |
| A06 | Vulnerable & Outdated Components | |
| A07 | ID & Authentication Failures | |
| A08 | Software & Data Integrity Failures | |
| A09 | Security Logging & Monitoring Failures | |
| A10 | Server-Side Request Forgery (SSRF) | |

**Additional checks**
- Secrets management — are credentials hardcoded or in env vars?
- Sensitive data exposure — are PII/secrets logged or returned in responses?
- Rate limiting — can this endpoint be brute-forced or abused?
- Dependency vulnerabilities — any known CVEs in libraries used?

**Output format**
1. Executive summary (2–3 sentences on overall risk level).
2. Critical / High findings with reproduction steps and fix.
3. Medium / Low findings.
4. Hardened version of the code (if applicable).
5. Recommended security tests to add to the CI pipeline.

{_SENIOR_FOOTER}
""".strip()


# ── Dispatch table ────────────────────────────────────────────────────────────

TEMPLATES: dict[str, callable] = {
    "implement": _implement,
    "debug":     _debug,
    "refactor":  _refactor,
    "review":    _review,
    "design":    _design,
    "test":      _test,
    "optimize":  _optimize,
    "explain":   _explain,
    "security":  _security,
}


def build_prompt(task_type: str, context: dict) -> str:
    """Generate a senior-dev prompt for the given task type and context."""
    fn = TEMPLATES.get(task_type, _implement)
    return fn(context)
