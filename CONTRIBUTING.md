# 🤝 CONTRIBUTING.md — CivicPulse Contribution Guide

Thank you for contributing to CivicPulse. This document outlines everything you need to know before opening a PR.

---

## Before You Start

1. Read `AGENTS.md` — it defines the core rules every contributor (human or AI) must follow
2. Read `ARCHITECTURE.md` — understand the system before modifying any component
3. Read `docs/privacy-framework.md` — data handling rules are non-negotiable

---

## Development Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-org/civicpulse.git
cd civicpulse

# 2. Copy env template
cp .env.example .env
# Fill in your local values (Mapbox token is enough to start)

# 3. Start local stack
docker-compose up --build

# 4. Verify all services are healthy
docker-compose ps

# 5. Run tests
pytest tests/ --cov=src --cov-report=term
```

---

## Branch Strategy

```
main         ← Production. Protected. Deploy on tag only.
staging      ← Pre-production. Auto-deploys on merge.
dev          ← Integration branch. All feature PRs target this.
feature/*    ← Feature branches. Branch from dev.
fix/*        ← Bug fix branches. Branch from dev (or main for hotfixes).
```

---

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(dispatch): add fatigue scoring to matcher
fix(ml): correct signal weight normalization
docs(agents): update CSS threshold documentation
test(ingestion): add unit tests for anonymizer
refactor(api): extract volunteer filtering to service layer
chore(deps): bump xgboost to 2.0.1
```

---

## Pull Request Rules

- All PRs must target `dev` (not `main` or `staging`)
- PR title must follow Conventional Commits format
- Every PR must include:
  - [ ] Tests for new functionality
  - [ ] Updated docstrings/comments
  - [ ] Updated relevant docs if behavior changes
  - [ ] Privacy impact statement (if touching ingestion or ML)

### PR Template

```markdown
## What does this PR do?
<!-- Brief description -->

## Related Issue
<!-- Closes #... -->

## Type of Change
- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation
- [ ] Chore

## Privacy Impact
- [ ] This PR touches data ingestion or ML pipelines
- [ ] Anonymization is preserved / not affected
- [ ] No PII is introduced

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally

## Screenshots (if UI change)
```

---

## Code Standards

### Python (Backend / ML)
- Style: Black + isort (enforced via pre-commit hook)
- Type hints: Required on all public functions
- Docstrings: Google-style
- Min test coverage: 80% per module

```python
# Good
def compute_css(signals: list[Signal], ward_id: str) -> float:
    """Compute Community Stress Score for a given ward.

    Args:
        signals: List of normalized signal records for the ward.
        ward_id: Unique identifier for the ward.

    Returns:
        CSS value between 0.0 and 100.0.
    """
    ...
```

### TypeScript/React (Frontend)
- Style: ESLint + Prettier
- Components: Functional only (no class components)
- State: useState / useReducer (no Redux unless absolutely necessary)
- Tests: React Testing Library

---

## Testing Requirements

| Layer | Requirement |
|---|---|
| ML models | Precision ≥ 0.75 on holdout set before merge |
| API endpoints | Every route has at least one happy-path + one error-path test |
| Ingestion | Every signal source connector has unit tests with mock data |
| Dispatch | Matching algorithm tested with synthetic volunteer pool |
| Privacy | PII scan runs automatically on all pipeline output fixtures |

Run full test suite:
```bash
pytest tests/ -v --cov=src --cov-fail-under=80
```

---

## Adding a New Signal Source

1. Create a new connector in `src/ingestion/connectors/{source_name}.py`
2. Implement the `BaseConnector` interface (see `src/ingestion/base.py`)
3. Normalize output to Unified Signal Schema (see `data/schemas/signal.json`)
4. Add anonymization step via `anonymizer.anonymize(signal)`
5. Add a mock in `src/ingestion/mocks/{source_name}_mock.py`
6. Register the connector in `src/ingestion/registry.py`
7. Add unit tests in `tests/unit/ingestion/test_{source_name}.py`
8. Document the source in `docs/signal-sources.md`

---

## Adding a New API Endpoint

1. Define request/response Pydantic models in `src/api/schemas/`
2. Implement route in `src/api/routes/`
3. Add auth dependency (`Depends(get_current_user)`)
4. Add rate limiting decorator if needed
5. Write integration test in `tests/integration/api/`
6. Update `docs/api-reference.md`

---

## Reporting Issues

Use GitHub Issues with the appropriate label:
- `bug` — something is broken
- `privacy` — data handling concern (treat as high priority)
- `ml` — model accuracy or fairness issue
- `enhancement` — new feature request
- `docs` — documentation gap

For security vulnerabilities: email security@civicpulse.org — do NOT open a public issue.

---

## Code of Conduct

CivicPulse is a social impact project. All contributors are expected to:
- Be respectful and constructive in all communications
- Prioritize community welfare in every technical decision
- Treat privacy and ethics violations as P0 issues, not afterthoughts
- Give credit generously and assume good intent

---

## Questions?

- Technical: Open a GitHub Discussion
- Privacy/Ethics: Email ethics@civicpulse.org
- Partnerships: Email partners@civicpulse.org
