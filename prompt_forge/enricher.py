"""
enricher.py — Transform a vague prompt into what a senior engineer would write.

This is NOT a template filler. It reads the user's rough intent and rewrites
the prompt with the specificity, constraints, and requirements that a senior dev
would naturally include before handing a task to a colleague or an AI.
"""

from __future__ import annotations
import re


# ── Concept expansion ─────────────────────────────────────────────────────────
# When these terms appear in the prompt, inject precise technical requirements
# that a senior dev would always specify but juniors leave implicit.

_CONCEPT_EXPANSIONS: dict[str, list[str]] = {
    # Auth / identity
    "auth": [
        "Validate the token signature and algorithm (pin the algorithm — never accept 'none')",
        "Check expiry (`exp` claim) and return a distinct error for expired vs invalid tokens",
        "Attach the decoded identity (user_id, roles, email) to the request context",
        "Never expose internal signing details or stack traces in error responses",
    ],
    "jwt": [
        "Pin the expected algorithm (e.g. HS256 or RS256) — reject tokens signed with any other",
        "Validate `exp`, `iat`, and `iss` claims explicitly",
        "Return distinct HTTP status codes: 401 for expired, 400 for malformed, 401 for invalid signature",
    ],
    "oauth": [
        "Handle the full authorization code flow including PKCE",
        "Validate the `state` parameter to prevent CSRF",
        "Implement token refresh with rotation — revoke the old refresh token on use",
        "Store tokens server-side, never in localStorage",
    ],
    "password": [
        "Hash with bcrypt or argon2id — never MD5, SHA-1, or unsalted SHA-256",
        "Enforce a minimum length of 12 characters",
        "Rate-limit login attempts per IP and per account (separate counters)",
        "Never log or echo back the password at any point",
    ],
    # Database
    "database": [
        "Use a connection pool — do not open a new connection per request",
        "Wrap multi-step writes in a transaction; roll back the entire unit on any failure",
        "Use parameterised queries or an ORM — never string-format user input into SQL",
        "Add appropriate indexes for all columns used in WHERE/JOIN clauses",
    ],
    "sql": [
        "Use parameterised queries exclusively — zero string interpolation of user input",
        "Keep transactions as short as possible to reduce lock contention",
        "Explain the query plan (`EXPLAIN ANALYZE`) to verify index usage",
    ],
    "migration": [
        "Ensure the migration is idempotent and can be re-run safely",
        "Make it reversible — include a `down` migration",
        "Test on a copy of production data before merging",
        "Add the migration to CI so it runs automatically against a fresh schema",
    ],
    # API / HTTP
    "api": [
        "Version the endpoint (e.g. `/v1/`) from day one",
        "Return consistent error shapes: `{error: string, code: string, details?: object}`",
        "Validate and sanitise every input field — reject unknown fields",
        "Document the contract (request, response, error codes) in a comment or spec file",
    ],
    "rest": [
        "Use correct HTTP verbs and status codes (201 for creation, 204 for no-body success, etc.)",
        "Implement idempotency keys for POST operations that create resources",
        "Paginate list endpoints — never return unbounded result sets",
    ],
    "webhook": [
        "Verify the signature on every incoming payload before processing",
        "Respond 200 immediately and process asynchronously — never block on webhook handling",
        "Make the handler idempotent — duplicate deliveries must not cause duplicate side effects",
        "Implement exponential backoff on outbound delivery retries with a dead-letter mechanism",
    ],
    # Caching
    "cache": [
        "Define the cache key scheme explicitly — include all dimensions that affect the result",
        "Set a TTL on every key — no keys should live forever",
        "Handle cache miss, stale data, and cache stampede (use a lock or probabilistic refresh)",
        "Decide whether to use cache-aside, read-through, or write-through and state why",
    ],
    "redis": [
        "Use pipelining for batch operations to reduce round-trip latency",
        "Set `maxmemory-policy` appropriately for the use case (LRU vs LFU vs noeviction)",
        "Use TTL on every key; avoid using Redis as a permanent data store unless intended",
    ],
    # Async / queues
    "queue": [
        "Ensure consumers are idempotent — the same message may be delivered more than once",
        "Implement a dead-letter queue for messages that repeatedly fail processing",
        "Log the message ID on every step so failures can be traced end-to-end",
        "Test both the happy path and poison-pill messages that cause consumer panics",
    ],
    "async": [
        "Avoid fire-and-forget — always handle errors from async operations",
        "Set timeouts on all async I/O; never await indefinitely",
        "Propagate cancellation tokens / contexts through the entire call chain",
    ],
    "worker": [
        "Handle SIGTERM gracefully — finish the current job before shutting down",
        "Implement a heartbeat or health check so the scheduler can detect stuck workers",
        "Ensure job processing is idempotent so retries on failure are safe",
    ],
    # Infrastructure
    "docker": [
        "Use a multi-stage build to keep the final image minimal",
        "Run the process as a non-root user",
        "Pin base image versions — never use `latest`",
        "Add a health check instruction (`HEALTHCHECK`)",
    ],
    "kubernetes": [
        "Set resource requests AND limits for every container",
        "Define liveness and readiness probes",
        "Use a PodDisruptionBudget for services with an availability SLO",
        "Never store secrets in ConfigMaps — use Secrets or an external vault",
    ],
    # Testing
    "test": [
        "Cover the happy path, all documented error paths, and at least two edge cases",
        "Name tests after behaviour: `test_<unit>_<condition>_<expected_result>`",
        "Keep each test independent — no shared mutable state between tests",
        "Mock at the boundary (I/O, network) — do not mock business logic",
    ],
    # Frontend / React
    "react": [
        "Avoid unnecessary re-renders — memo expensive child components",
        "Keep side effects in `useEffect` with correct dependency arrays",
        "Handle loading, error, and empty states for every data-fetching hook",
        "Do not store derived state in `useState` — compute it from existing state/props",
    ],
    "component": [
        "Keep the component focused on one responsibility — split if it does two distinct things",
        "Accept a className or style prop so callers can adjust layout without forking",
        "Document all props with types and a brief description",
    ],
    # Performance
    "performance": [
        "Profile before optimising — identify the actual bottleneck first",
        "State the baseline metric and the target (e.g. p99 < 200 ms)",
        "Prefer algorithmic improvements over micro-optimisations",
        "Add a benchmark test so regressions are caught in CI",
    ],
    "memory": [
        "Identify whether the issue is a leak (growing indefinitely) or high steady-state usage",
        "Use a profiler to find the largest allocations — do not guess",
        "Check for references held in closures, caches, or global collections that prevent GC",
    ],
    # Security
    "encryption": [
        "Use AES-256-GCM for symmetric encryption — include a random IV per operation",
        "Never reuse IVs with the same key",
        "Authenticate the ciphertext (use AEAD) — detect tampering before decrypting",
        "Manage key rotation from day one — store keys outside the application code",
    ],
    "rate limit": [
        "Apply limits at the edge (load balancer / API gateway) as the first line of defence",
        "Use a sliding window algorithm for a smoother limit than fixed windows",
        "Return `Retry-After` header so clients can back off gracefully",
        "Separate burst limit from sustained limit",
    ],
    # Distributed systems
    "microservice": [
        "Define the service boundary clearly — what does this service own exclusively?",
        "Design for failure: circuit breaker, retry with backoff, timeout on every outbound call",
        "Use correlation IDs for distributed tracing across service boundaries",
        "Version your API contracts and maintain backward compatibility within a major version",
    ],
    "distributed": [
        "Identify the consistency model required (strong, eventual, causal)",
        "Design for partial failure — what happens if one node is unreachable?",
        "Use idempotent operations wherever possible so retries are safe",
    ],
}

# ── Task-type specific required sections ─────────────────────────────────────

_TASK_STRUCTURE: dict[str, dict] = {
    "implement": {
        "role": "senior software engineer",
        "core_label": "Implement",
        "req_sections": [
            ("Functional requirements",
             "Define the exact behaviour: inputs, outputs, and all documented side effects. "
             "List every state the function/class/service must handle correctly."),
            ("Error handling",
             "For every failure mode, specify the exact exception type or HTTP status code to return. "
             "Do not use catch-all handlers — name each error explicitly."),
            ("Edge cases",
             "Cover: empty / null / zero input, maximum size, concurrent access, "
             "partial failure in multi-step operations, and any domain-specific boundary values."),
            ("Non-functional requirements",
             "State thread-safety expectations, whether the component must be stateless, "
             "any memory or latency constraints, and backward-compatibility requirements."),
            ("Testability",
             "Accept dependencies (secrets, clocks, HTTP clients) via parameters or dependency injection, "
             "not from global state, so tests can run without patching."),
        ],
        "deliverables": [
            "Full implementation with type annotations and inline comments on every non-obvious decision",
            "Unit tests covering all documented error paths and the two most critical edge cases",
            "A short design note (3–5 sentences) explaining the key trade-off made",
        ],
    },
    "debug": {
        "role": "senior engineer conducting a debugging session",
        "core_label": "Debug",
        "req_sections": [
            ("Reproduction",
             "Provide the smallest self-contained example that reliably triggers the bug. "
             "State whether the failure is deterministic or intermittent."),
            ("Hypotheses",
             "List the top 3 root-cause candidates ranked by probability. "
             "For each, state what evidence would confirm or definitively rule it out."),
            ("Fix",
             "Apply the minimal surgical change. Do not refactor unrelated code in the same diff. "
             "Explain why the fix works, not just what it changes."),
            ("Regression guard",
             "Write a test that fails before the fix and passes after. "
             "Identify whether the same bug pattern exists elsewhere in the codebase."),
        ],
        "deliverables": [
            "Root cause diagnosis in 2–3 sentences",
            "Fix as a clean diff or annotated snippet",
            "Regression test that proves the fix",
            "One concrete recommendation to prevent this class of bug in future",
        ],
    },
    "refactor": {
        "role": "senior engineer performing a focused refactor",
        "core_label": "Refactor",
        "req_sections": [
            ("Constraints",
             "External behaviour must not change — this is a refactor, not a rewrite. "
             "Keep the diff as small as possible. Do not fix unrelated issues in the same PR."),
            ("Goals",
             "Improve one or more of: naming clarity, duplication, control-flow nesting, "
             "coupling between modules, or separation of concerns. State the specific goal upfront."),
            ("Out of scope",
             "List issues you noticed but are deliberately leaving for a follow-up, "
             "so reviewers understand the intentional narrowness of this change."),
        ],
        "deliverables": [
            "Refactored code",
            "Before/after diff highlighting the three most impactful changes",
            "A Future Work section listing issues intentionally deferred",
        ],
    },
    "review": {
        "role": "principal engineer conducting a code review",
        "core_label": "Review",
        "req_sections": [
            ("Correctness",
             "Check for logic errors, off-by-one mistakes, type mismatches, and unhandled edge cases. "
             "Reference specific lines when flagging issues."),
            ("Security",
             "Verify input validation, injection risks (SQL, command, template), "
             "authentication enforcement, and that no secrets are logged or returned in responses."),
            ("Performance",
             "Flag N+1 query patterns, unnecessary allocations, synchronous I/O on hot paths, "
             "and data structures that are wrong for the access pattern."),
            ("Readability and maintainability",
             "Identify naming that obscures intent, nesting deeper than two levels, "
             "functions with more than one responsibility, and missing documentation on public APIs."),
            ("Testability",
             "Note whether the code can be unit-tested without mocking internals, "
             "and whether all documented behaviour is covered by existing tests."),
        ],
        "deliverables": [
            "Overall verdict: Approve / Request changes / Needs discussion",
            "Blocking issues listed with file and line reference",
            "Non-blocking suggestions grouped by category",
            "Two to three positive callouts — what was done well and why it matters",
        ],
    },
    "design": {
        "role": "staff engineer designing a system or component",
        "core_label": "Design",
        "req_sections": [
            ("Assumptions",
             "State your assumptions about scale (RPS, data volume, user count), "
             "consistency requirements, p99 latency SLO, team size, and existing stack constraints. "
             "Any reader should be able to evaluate the design knowing only what you state here."),
            ("Options considered",
             "Describe 2–3 viable approaches. For each: one-sentence summary, key trade-offs, "
             "and the specific condition under which you would choose it."),
            ("Recommended design",
             "Detail the chosen approach: component responsibilities, data model, "
             "API contract, failure modes and how they are handled, "
             "and how the design scales to 10x current load."),
            ("Decision log",
             "Call out the three most significant design choices and the alternatives you rejected, "
             "with the reasoning. This is the most valuable part for future maintainers."),
            ("MVP scope",
             "Define the smallest version that is safe to ship and delivers real value. "
             "Separate it clearly from the full design."),
        ],
        "deliverables": [
            "ASCII component diagram with responsibility labels",
            "API or data model contract with field types and constraints",
            "Decision log with alternatives rejected",
            "Risk register: top 3 risks with probability, impact, and mitigation",
        ],
    },
    "test": {
        "role": "senior engineer writing a production-grade test suite",
        "core_label": "Test",
        "req_sections": [
            ("Test layer",
             "Decide unit / integration / E2E coverage and justify the split. "
             "Unit tests should have no I/O. Integration tests should use real dependencies "
             "or high-fidelity fakes. E2E tests should cover critical user journeys only."),
            ("Test cases",
             "Cover: happy path, empty/null/zero input, boundary values, "
             "each documented error path, concurrency if applicable, "
             "and a named regression test for any known past bugs."),
            ("Test quality",
             "One assertion focus per test. Names follow `test_<unit>_<condition>_<expected>`. "
             "No shared mutable state between tests. Test the public contract, not implementation details."),
        ],
        "deliverables": [
            "Complete test file using arrange / act / assert structure with section comments",
            "All fixtures and mocks with an explanation of why each is needed",
            "A coverage gap analysis listing what is not tested and the reason",
        ],
    },
    "optimize": {
        "role": "senior performance engineer",
        "core_label": "Optimise",
        "req_sections": [
            ("Baseline and target",
             "State the current measured value (p99 latency, throughput, memory RSS) "
             "and the acceptable target. Do not start optimising without a baseline."),
            ("Bottleneck identification",
             "Rank the top 3 likely bottlenecks: algorithm complexity, I/O wait, "
             "memory pressure/GC, or lock contention. For each, state the tool you would use to confirm it."),
            ("Optimisation strategy",
             "Apply improvements in this order: algorithm/data-structure change first, "
             "then caching, then batching/async I/O, then micro-optimisations last. "
             "Stop when the target is met."),
            ("Correctness preservation",
             "Every change must leave observable behaviour identical. "
             "Add a benchmark test so future regressions are caught automatically."),
        ],
        "deliverables": [
            "Profiling plan with specific tool and command",
            "Optimised implementation with before/after Big-O or empirical comparison",
            "Benchmark output proving the improvement",
            "A comment in the code explaining why the optimised form is correct",
        ],
    },
    "explain": {
        "role": "senior engineer writing documentation for a new contributor",
        "core_label": "Explain",
        "req_sections": [
            ("Bird's-eye view",
             "One paragraph describing what this code does at a business or product level. "
             "A non-technical reader should understand the purpose."),
            ("Structural walkthrough",
             "Walk through the main components or functions in the order a new reader would encounter them. "
             "An ASCII flow diagram is preferred over prose for anything with branching."),
            ("Non-obvious sections",
             "For the 3–5 most surprising or complex lines/blocks, explain "
             "what they do, why they are written this way, and what would break if changed naively."),
            ("Maintenance guide",
             "List implicit assumptions, footguns, global state dependencies, "
             "and anything a contributor must know before making any change."),
        ],
        "deliverables": [
            "Bird's-eye summary (one paragraph)",
            "Structural walkthrough with ASCII flow if applicable",
            "Annotated version of the most complex section",
            "Maintenance notes: footguns, assumptions, safe change boundaries",
        ],
    },
    "security": {
        "role": "senior application security engineer",
        "core_label": "Security audit",
        "req_sections": [
            ("Threat model",
             "Identify the attacker profile (external user, authenticated user, insider, "
             "supply-chain) and what they would gain from a successful attack."),
            ("Attack surface",
             "Map all entry points: HTTP endpoints, CLI arguments, environment variables, "
             "file reads, third-party callbacks, and inter-service calls."),
            ("OWASP Top 10 check",
             "For each relevant category — injection, broken authentication, "
             "sensitive data exposure, insecure design, security misconfiguration — "
             "state whether it applies and what the finding is."),
            ("Hardening",
             "List specific code changes in priority order (critical first). "
             "Each finding must include: description, reproduction steps, and the exact fix."),
        ],
        "deliverables": [
            "Executive summary: overall risk level (Critical / High / Medium / Low) with one-sentence rationale",
            "Findings table: severity, description, reproduction, fix",
            "Hardened version of the most critical section",
            "Three automated security checks to add to the CI pipeline",
        ],
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_concept_expansions(text: str) -> list[str]:
    """Return specific requirements for every technical concept found in text."""
    lower = text.lower()
    found: list[str] = []
    for concept, points in _CONCEPT_EXPANSIONS.items():
        if concept in lower:
            found.extend(points)
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for p in found:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _extract_core(prompt: str) -> str:
    """Clean up the prompt text for use as the task statement."""
    # Strip leading question words if present
    cleaned = re.sub(r"^\s*(can you|please|could you|i need|i want|help me|write me)\s+",
                     "", prompt.strip(), flags=re.IGNORECASE)
    # Capitalise first letter
    return cleaned[0].upper() + cleaned[1:] if cleaned else prompt.strip()


# ── Main enhance function ─────────────────────────────────────────────────────

def enhance(prompt: str, task_type: str, language: str | None) -> str:
    """
    Rewrite `prompt` as a senior engineer would write it.

    Returns a polished, ready-to-paste prompt — not a meta-template.
    """
    struct = _TASK_STRUCTURE.get(task_type, _TASK_STRUCTURE["implement"])
    concept_reqs = _find_concept_expansions(prompt)
    core = _extract_core(prompt)
    lang_hint = f" in {language}" if language else ""

    lines: list[str] = []

    # ── Role ──────────────────────────────────────────────────────────────────
    lines.append(f"You are a {struct['role']}.")
    lines.append("")

    # ── Task statement ────────────────────────────────────────────────────────
    lines.append(f"## {struct['core_label']}{lang_hint}")
    lines.append("")
    lines.append(core)
    lines.append("")

    # ── Concept-specific requirements (derived from what is in the prompt) ────
    if concept_reqs:
        lines.append("## Technical requirements")
        lines.append("")
        for req in concept_reqs:
            lines.append(f"- {req}")
        lines.append("")

    # ── Task-type standard sections ───────────────────────────────────────────
    lines.append("## Scope and constraints")
    lines.append("")
    for section, description in struct["req_sections"]:
        lines.append(f"**{section}**")
        lines.append(f"{description}")
        lines.append("")

    # ── Senior dev non-negotiables ────────────────────────────────────────────
    lines.append("## Non-negotiables")
    lines.append("")
    lines.append("- Handle all failure paths explicitly — no silent failures or bare except/catch.")
    lines.append("- Validate and sanitise every external input before use.")
    if task_type not in ("explain", "review"):
        lines.append("- Structure the code so it can be unit-tested without mocking internals.")
    lines.append("- Use descriptive names — the code must be readable without comments for the happy path.")
    if language in ("python", "typescript", "go", "rust", "java", "c#", "swift", "kotlin"):
        lines.append(f"- Use {language} type annotations / types throughout.")
    lines.append("")

    # ── Deliverables ──────────────────────────────────────────────────────────
    lines.append("## Deliver")
    lines.append("")
    for i, d in enumerate(struct["deliverables"], 1):
        lines.append(f"{i}. {d}")
    lines.append("")

    # ── Closing instruction ───────────────────────────────────────────────────
    lines.append("Before writing any code, state your assumptions and flag any ambiguity "
                 "in the requirements above.")

    return "\n".join(lines)
