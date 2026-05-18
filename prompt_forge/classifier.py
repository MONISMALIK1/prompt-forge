"""
classifier.py — Detect what kind of development task is being described.

Task types:
  implement  – build something new
  debug      – fix a bug / diagnose an issue
  refactor   – improve existing code without changing behaviour
  review     – critique code for quality / security
  design     – architect a system, API, or data model
  test       – write or improve tests
  optimize   – improve performance or resource usage
  explain    – understand / document existing code
  security   – audit for vulnerabilities or harden code
"""

from __future__ import annotations
import re

# ── Keyword maps ──────────────────────────────────────────────────────────────

_TASK_KEYWORDS: dict[str, list[str]] = {
    "implement": [
        "build", "create", "implement", "write", "develop", "add", "make",
        "scaffold", "generate", "set up", "setup", "bootstrap", "integrate",
        "add feature", "new feature", "from scratch",
    ],
    "debug": [
        "fix", "bug", "error", "broken", "not working", "crash", "crashes",
        "crashing", "issue", "failing", "fails", "exception", "traceback",
        "stacktrace", "race condition", "deadlock", "memory leak", "doesn't work",
        "wrong output", "unexpected", "diagnose", "investigate", "root cause",
    ],
    "refactor": [
        "refactor", "clean up", "cleanup", "improve", "restructure",
        "simplify", "decouple", "extract", "consolidate", "rename",
        "reorganise", "reorganize", "modularise", "modularize",
    ],
    "review": [
        "review", "audit", "check", "evaluate", "assess", "critique",
        "feedback on", "look at", "is this good", "code quality",
    ],
    "design": [
        "design", "architect", "architecture", "schema", "data model",
        "api design", "system design", "plan", "blueprint", "how should i",
        "structure", "approach", "strategy", "pattern",
    ],
    "test": [
        "test", "tests", "unit test", "integration test", "e2e", "end-to-end",
        "spec", "coverage", "mock", "stub", "tdd", "bdd", "pytest", "jest",
        "playwright", "cypress", "assertion", "test suite",
    ],
    "optimize": [
        "optimize", "optimise", "slow", "performance", "latency", "speed up",
        "memory", "profil", "bottleneck", "n+1", "cache", "faster",
        "efficient", "throughput", "reduce cost",
    ],
    "explain": [
        "explain", "understand", "how does", "what does", "walk me through",
        "document", "comment", "what is", "describe", "breakdown",
    ],
    "security": [
        "security", "secure", "vulnerability", "vulnerabilities", "injection",
        "xss", "cross-site scripting", "csrf", "cross-site request",
        "authentication", "authorization", "auth", "permission",
        "sql injection", "input validation", "sanitize", "sanitise",
        "encrypt", "harden", "attack", "exploit", "owasp", "pentest",
        "privilege escalation", "insecure",
    ],
}

# Tie-breaker priority (more specific wins)
_PRIORITY = ["security", "debug", "optimize", "test", "review",
             "refactor", "design", "explain", "implement"]


_LEADING_VERB_MAP = [
    # (regex for leading verb phrase, task_type, bonus)
    # security-specific verbs / verb+concept combos must come before generic review
    (re.compile(r"^\s*(audit|pen.?test|find.*vuln|check.*security|check.*vuln|check.*xss|check.*inject)\b", re.I), "security", 5),
    (re.compile(r"^\s*(review|critique|audit\s+(?!.*inject|.*vuln)|check|evaluate|assess)\b", re.I), "review",    4),
    (re.compile(r"^\s*(refactor|clean\s+up|restructure|simplify)\b",                                 re.I), "refactor",  4),
    (re.compile(r"^\s*(debug|fix|diagnose|investigate)\b",                                           re.I), "debug",     4),
    (re.compile(r"^\s*(optimis?e|speed\s+up|profile)\b",                                             re.I), "optimize",  4),
    (re.compile(r"^\s*(explain|document|walk\s+me|describe)\b",                                      re.I), "explain",   4),
    # write/add/set up + test keyword → test
    (re.compile(r"^\s*(write|add|create|generate|set\s+up)\b.{0,60}\btest",                          re.I), "test",      5),
    # generic build verbs → implement (only if no stronger type fires)
    (re.compile(r"^\s*(build|create|implement|write|develop|add|make|scaffold|set\s+up)\b",          re.I), "implement", 3),
]


def detect_task(text: str) -> str:
    """Return the most likely task type for the given rough description."""
    lower = text.lower()
    scores: dict[str, int] = {t: 0 for t in _TASK_KEYWORDS}

    for task, kws in _TASK_KEYWORDS.items():
        for kw in kws:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                scores[task] += 1

    # Apply leading-verb boosts in priority order (first match wins per slot)
    for pattern, task, bonus in _LEADING_VERB_MAP:
        if pattern.search(text):
            scores[task] += bonus
            break  # only one verb bonus per prompt

    # Strong security signal: 3+ security keywords override verb bonuses
    if scores["security"] >= 3:
        scores["security"] += 4

    best_score = max(scores.values())
    if best_score == 0:
        return "implement"

    for task in _PRIORITY:
        if scores[task] == best_score:
            return task

    return max(scores, key=lambda t: scores[t])


def detect_language(text: str) -> str | None:
    """Try to extract a programming language or framework from the text."""
    lang_map = {
        "python": ["python", "fastapi", "django", "flask", "pydantic", "numpy", "pandas"],
        "typescript": ["typescript", "ts", "tsx"],
        "javascript": ["javascript", "js", "node", "express", "react", "vue", "angular", "next.js", "nextjs"],
        "rust": ["rust", "cargo", "tokio", "actix"],
        "go": ["golang", "go ", " go\b"],
        "java": ["java", "spring", "maven", "gradle"],
        "c++": ["c++", "cpp", "cmake"],
        "c#": ["c#", ".net", "dotnet", "asp.net"],
        "swift": ["swift", "swiftui", "ios", "xcode"],
        "kotlin": ["kotlin", "android"],
        "sql": ["sql", "postgres", "postgresql", "mysql", "sqlite", "mongodb"],
        "bash": ["bash", "shell", "sh ", "zsh"],
    }
    lower = text.lower()
    for lang, hints in lang_map.items():
        for h in hints:
            if re.search(r"\b" + re.escape(h.strip()) + r"\b", lower):
                return lang
    return None
