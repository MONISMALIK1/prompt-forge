# 🧠 prompt-forge

> Turn a rough task description into a **senior-engineer-quality prompt** in one command.

Stop writing vague prompts like _"write a function to sort users"_.  
Let `prompt-forge` expand it into something a principal engineer would write — with edge cases, error handling, security checks, testability requirements, and trade-off thinking baked in.

---

## Install

```bash
pip install prompt-forge
```

---

## Quick start

```bash
# Auto-detects task type and language
pf "build a JWT auth middleware in FastAPI"

# Override task type explicitly
pf "fix the memory leak in my connection pool" --type debug

# Copy generated prompt straight to clipboard
pf "review this React authentication hook" --copy

# Raw output (no colour/headers) — pipe it anywhere
pf "design a multi-tenant SaaS DB schema" --raw | pbcopy

# Interactive wizard — guided step-by-step
pf --interactive

# See all task types
pf --list-types
```

---

## Task types

| # | Type | Emoji | When to use |
|---|------|-------|-------------|
| 1 | `implement` | 🔨 | Build something new |
| 2 | `debug` | 🐛 | Diagnose and fix a bug |
| 3 | `refactor` | ♻️ | Improve code without changing behaviour |
| 4 | `review` | 👁️ | Critique code for quality and correctness |
| 5 | `design` | 🏗️ | Architect a system, API, or data model |
| 6 | `test` | 🧪 | Write comprehensive tests |
| 7 | `optimize` | ⚡ | Improve performance or memory usage |
| 8 | `explain` | 📖 | Understand and document existing code |
| 9 | `security` | 🔒 | Audit for vulnerabilities and harden code |

Task type is **auto-detected** from your description — you only need `--type` to override.

---

## What makes these prompts "senior dev" quality?

Every generated prompt instructs the AI to think through:

```
□  Edge cases — empty input, null/undefined, max size, concurrent access
□  Error handling — specific exceptions, meaningful messages, no silent failures
□  Security — input validation, injection risks, auth boundaries, secrets
□  Performance — algorithmic complexity, N+1 queries, unnecessary allocations
□  Testability — is the output easy to unit-test? are side effects isolated?
□  Readability — clear naming, minimal nesting, single responsibility
□  Backward compatibility — does this break existing callers or contracts?
```

Plus task-specific structure:
- **debug** → Reproduce → Hypothesis (ranked) → Fix → Prevention
- **design** → Assumptions → 3 approaches → Recommended → Decision log → MVP vs full
- **review** → OWASP-style rubric across 8 quality areas
- **optimize** → Measure first → Bottleneck → Fix by layer → Benchmark
- **security** → Full OWASP Top 10 scan + secrets + rate limiting

---

## Examples

### Before prompt-forge
```
"write an auth middleware"
```

### After prompt-forge
```
You are a senior software engineer with 10+ years of experience.

## Task
Implement the following in python:
> build a JWT auth middleware in FastAPI that validates tokens,
  checks expiry, and attaches user context to the request

## Requirements — think like a senior dev

**Functional**
- Handle all obvious edge cases (empty token, expired token, malformed JWT,
  wrong algorithm, missing claims)...

**Security**
- Validate and sanitise all inputs before use.
- Avoid exposing internal implementation details in error messages...

**Output format**
1. Short explanation of your design choices
2. Full implementation with inline comments
3. Example usage snippet
4. Caveats or follow-up work a reviewer should know about
```

---

## Options

```
pf [TASK] [OPTIONS]

Arguments:
  TASK          Rough description of what you want to do

Options:
  -t, --type    Task type (implement|debug|refactor|review|design|
                           test|optimize|explain|security)
  -l, --lang    Language/framework override (python, typescript, rust…)
  -c, --copy    Copy output to clipboard (macOS/Linux)
  --raw         Plain text output — no colour or headers
  -i, --interactive  Launch the step-by-step wizard
  --list-types  Show all task types
  -h, --help    Show help
  --version     Show version
```

---

## Related projects

- [llm-router](https://github.com/MONISMALIK1/llm-router) — route prompts to the cheapest AI that can handle them
- [model-advisor-extension](https://github.com/MONISMALIK1/model-advisor-extension) — Chrome extension for live model recommendation
- [dev-guard-vscode](https://github.com/MONISMALIK1/dev-guard-vscode) — VS Code extension for prompt injection scanning

---

## License

MIT
