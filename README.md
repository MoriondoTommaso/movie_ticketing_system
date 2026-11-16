# Movie Ticketing System

Five-person database project: Python 3.13 CLI and MySQL 8.4, with atomic ticket
purchases, screening management, and SQL reports.

## Planning and collaboration

- [Specification](plan/SPEC.md)
- [Implementation plan](tasks/plan.md)
- [Team assignments and reviews](tasks/assignments.md)
- [Parallel work: start order and shared-file rules](tasks/parallel-work.md)
- [Git workflow and pull request guide](docs/git-workflow.md)
- [Task ledger](tasks/todo.md)
- [GitHub issues](tasks/github-issues.md)

The CLI is still a scaffold. The Python environment, database connection
lifecycle, and regression tests are implemented; T27 completes the handover guide.

## Continuous integration

[GitHub Actions CI](.github/workflows/ci.yml) runs on every push and pull request,
and can also be started manually from the Actions tab. It checks:

- Ruff lint and formatting.
- Dependency consistency and wheel packaging.
- The complete pytest suite on Python 3.13 with the pinned MySQL 8.4 services,
  including real database transaction, rollback, and test-isolation checks.

CI uses disposable databases and synthetic credentials from `.env.example`;
no GitHub secrets are required. Each run uploads pytest XML and MySQL diagnostics
as the `test-results` artifact (retained for 14 days).

To run the same checks locally, install Python 3.13 and Docker Compose, then:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip check
python -m ruff check .
python -m ruff format --check .
python -m pip wheel --no-deps --wheel-dir dist .
# First setup only; preserve an existing .env.
test -f .env || cp .env.example .env
docker compose --profile test up -d --wait --wait-timeout 180
python -m pytest -ra
docker compose --profile test down
```

Use distinct ports and a Compose project name in `.env` when sharing a machine.
Tests reset the configured test database; use only disposable synthetic test data.

To block merges on regressions, a repository administrator must enable a branch
ruleset for `main` requiring the **Python 3.13 / MySQL 8.4** status check after
the first CI run. The workflow alone does not enable branch protection.

Use short-lived branches and PRs linked to issues, with acceptance evidence and
the reviewer listed in the assignment plan. Keep issue and ledger status aligned.
Work in parallel lanes once each task's prerequisites are merged. Keep one active
task per person and reserve shared-file edits with the responsible integrator.
Use synthetic data; keep local credentials in ignored `.env` files. Intentional
`docs/` artifacts are tracked; the local assignment PDF is excluded.
