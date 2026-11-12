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

Implementation has not started: `main.py` is a greeting scaffold. Database and
test commands in the plan are future acceptance gates, not working application
instructions. T02 establishes the environment; T27 completes the handover guide.

Use short-lived branches and PRs linked to issues, with acceptance evidence and
the reviewer listed in the assignment plan. Keep issue and ledger status aligned.
Work in parallel lanes once each task's prerequisites are merged. Keep one active
task per person and reserve shared-file edits with the responsible integrator.
Use synthetic data; keep local credentials in ignored `.env` files. Intentional
`docs/` artifacts are tracked; the local assignment PDF is excluded.
