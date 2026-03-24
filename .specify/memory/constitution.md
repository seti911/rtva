# rtva Constitution

## Core Principles

### I. Library-First
Every feature starts as a standalone library. Libraries must be self-contained, independently testable, and documented. Clear purpose required - no organizational-only libraries.

### II. CLI Interface
Every library exposes functionality via CLI. Text in/out protocol: stdin/args → stdout, errors → stderr. Support JSON + human-readable formats.

### III. Test-First (NON-NEGIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced.

### IV. Integration Testing
Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas.

### V. Observability
Text I/O ensures debuggability. Structured logging required for all components.

### VI. Versioning & Breaking Changes
MAJOR.MINOR.BUILD format. Breaking changes require migration plan and deprecation timeline.

### VII. Simplicity
Start simple, YAGNI principles. Avoid premature optimization.

## Security Requirements
- All external inputs must be validated and sanitized
- Secrets must never be committed to version control
- Use environment variables for sensitive configuration
- Follow OWASP guidelines for web-facing components

## Performance Standards
- Response times must meet defined SLAs
- Resource usage must be monitored and logged
- Performance tests required for critical paths
- Memory and CPU limits defined for all services

## Development Workflow
- Code review required for all changes
- Testing gates: Unit tests → Integration tests → E2E tests
- Deployment approval process with sign-offs
- CI/CD pipeline must pass before merge

## Governance
Constitution supersedes all other practices. Amendments require documentation, approval, and migration plan. All PRs/reviews must verify compliance. Complexity must be justified.

**Version**: 1.0.0 | **Ratified**: 2026-03-24 | **Last Amended**: 2026-03-24
