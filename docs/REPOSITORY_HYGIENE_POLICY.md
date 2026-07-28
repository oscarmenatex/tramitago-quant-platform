# Repository Hygiene & Traceability Policy

## Purpose

This policy, authorized by IT-000-001, restores objective traceability for source, tests, documentation,
scripts and configuration.  These areas are versioned repository assets; they
must not be hidden by `.gitignore` or exist outside Git's index.

## Mandatory repository checks

Run the following before merging any change:

```powershell
python scripts/check_repository_hygiene.py
pytest
```

The hygiene check fails when a file in `src/`, `tests/`, `docs/`, `scripts/` or
`config/` is untracked or ignored.  It also rejects ignore rules for those
directories and validates references to `DOC-*`, `IT-*` and `ADR-*` documents.
Only generated/local artefacts may be ignored (for example caches, virtual
environments, coverage output, local data and secret `.env` files).

The CI workflow executes the same check for every push and pull request.

## Commit policy

Every functional commit uses the format:

```text
<type>(<domain>): <summary> [IT-XXX-YYY] [DOC-XXX] [ADR-XXX]
```

`IT` is mandatory.  `DOC` and `ADR` are mandatory whenever the change affects
an implementation contract or architectural decision.  The commit body records
the reason, affected domain, changed tests and any justified test deletion.
Test deletion must cite the authorizing IT and preserve the rationale in that
IT's evidence section.

Examples:

```text
feat(data): register dataset [IT-024-001] [DOC-024] [ADR-009]
test(research): replace obsolete availability case [IT-024-003] [DOC-023]
```

## Branch policy

`main` contains reviewed, releasable history and is protected: direct pushes
are prohibited and pull requests require the hygiene check and test suite.
`develop` is the integration branch, subject to the same checks.  Work starts
from `develop` in `feature/<IT>-<short-name>` branches.  Urgent corrections
start from `main` in `hotfix/<IT>-<short-name>` branches and are merged back to
both `main` and `develop`.

Each pull request identifies the IT, linked DOC/ADR, affected domain, changed
tests and documentation.  Squash or merge commits must retain these references
in their final commit message.

## Audit procedure

Use `git log -- <path>` to identify the change history of a file and `git show
<commit> -- <path>` to inspect its exact delta.  Use `git diff <baseline>...HEAD
-- src tests docs scripts config` to compare an audit scope objectively.
Coverage comparisons must use the same committed test command and baseline.
