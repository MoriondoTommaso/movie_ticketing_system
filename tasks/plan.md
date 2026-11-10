# Implementation plan — Movie Ticketing System

## Authority and scope

The user explicitly approved `plan/SPEC.md` and `plan/ROADMAP.md` in this conversation after being asked to approve P1–P11 and the proposed defaults in SPEC §12. This records approval despite the source documents retaining their earlier draft headings. The current request explicitly selects `tasks/plan.md` and `tasks/todo.md`, superseding the earlier planning-output path restriction. This change creates planning documents only.

Deliver the mandatory Python CLI, MySQL database, five SQL queries, three reports, ER PDF, transaction evidence, and documentation (SC1–SC14). Optional Flask work is deferred until the mandatory delivery gate passes and the user separately authorizes it; it is not a TODO in this ledger.

Approved defaults include Python 3.13, MySQL 8.4/InnoDB, scrypt password hashes, credit/debit synthetic cards with billing addresses, normalized case-insensitive email, and original language among available languages. Exact dependency versions, the cinema timezone, card-format limits, ER details, operation names and return shapes are frozen in T01–T06. Actual student names and submission date remain administrative follow-ups. B requests instructor clarification in T01; confirmation of comment placement remains a T29 delivery condition. Approval of the proposed entry-point placement does not constitute instructor confirmation.

## Repository evidence (Verify tier)

- Graph project: `Users-tommasomoriondo-code_base-db_project`; ready, initial recorded generation `2026-10-28T16:37:14Z`; coverage rechecked after creating the ledger at generation `2026-11-10T11:08:13Z`, including both task files (metadata match, no recorded issue).
- `search_graph(label="Function", name_pattern=".*")` returned three results, `has_more=false`: the application `main` plus builtin `print` and `len`. Exact snippet and direct source confirm `main.py` is a six-line greeting scaffold. `trace_path` in both directions shows its module entry and `print`, with no pagination remaining.
- Direct reads confirm `pyproject.toml` declares Python >=3.13 and no dependencies, `README.md` is empty, `.python-version` is 3.13, and `.gitignore` excludes `.venv/` and all of `docs/`. There is no existing `tasks/` ledger in the filesystem; Git was clean before planning.
- Coverage checked `main.py`, configuration, README, both planning inputs, and root scope. The index recorded no issue for those exact paths; `.python-version` was untracked by the index and was read directly. Root exclusions were `.git`, `.venv`, and `docs`; this is best-effort coverage, not completeness proof. The excluded `docs/` directory was read directly and contains the eight-page assignment PDF, which was also read. Runtime/build state inside `.venv` was not inferred from the graph.
- Locally verified discovery commands: `python3.13 --version` → 3.13.13; `docker compose version` → v5.5.1; `git ls-files` confirms the scaffold and planning inputs. Docker daemon health, dependency installation, tests, and MySQL service startup have not been verified.

These are greenfield service seams prescribed by the approved specification, not existing service implementations. Keep the root `main.py` scaffold until an intentional compatibility decision in T08; do not silently remove it.

## Architecture and integration decisions

1. One local Python application, explicit parameterized SQL, and separate development/test MySQL services. No shared connection or implicit commits in transaction helpers. Test setup refuses development targets before any reset.
2. Freeze schema/fixture IDs, principal/error shapes, typed service results, clock/timezone rules, and connection ownership early. `src/auth.py` supplies authentication/role primitives; each service enforces its own boundary. Menus never establish authorization.
3. Pricing uses Decimal and the approved calendar-anniversary rules. Pure schedule interval rules live in a small `src/schedule_rules.py` helper to keep boundary verification separate from SQL; this is a planning-level file split within the approved screenings module.
4. Booking locks screening then payment, reads capacity under the lock, recomputes price, writes purchase and counter, and commits once. All failures roll back and release resources. Scheduling locks the theater before a current/locking overlap read; a stale REPEATABLE READ snapshot must not defeat serialization. Payment deactivation uses the same payment-row lock as purchase validation.
5. Revenue uses captured purchase amounts. Occupancy aggregates sold quantities at screening grain before summing offered seats. Preserve zero-sale entities and N/A for movies without screenings.
6. Share fixture lifecycle, not one person's entire test workload. Fixtures reconcile stored counters with purchases, control the clock, and use explicit synchronization and bounded waits for races. Parallel verifiers use separate developer-local Compose projects/test targets with distinct ports, credentials and storage, or serialize reset-bearing runs against a shared target under E's coordination. Never run two resetting test suites or the demo against the same target simultaneously.
7. Preserve `queries.sql` as exactly five executable parameterized statements at completion. Intermediate Q1/Q2 additions are completed by T24, whose result-parity tests prevent application/artifact drift.
8. Track intentional submission documentation under `docs/`; do not indiscriminately add ignored source files. T02 narrows ignore rules while continuing to ignore `.env` secrets and local/generated clutter. T01 may create ignored design documents; T02 makes these intentional artifacts visible to Git before the first integration checkpoint.

## Owners and review

**Current authority:** [Named assignments](assignments.md) supersede provisional
A–E staffing/reviews throughout this document. Letters below describe architectural
lanes only; use the named plan for integrators, checkpoints and instructor follow-up.

| Lane | Primary owner | Reviewer | Shared-file coordination |
|---|---|---|---|
| Data/runtime | A | B | A integrates schema, ER, Compose, configuration, dependency metadata |
| Identity/payments | B | E | B owns authentication and top-level dispatch |
| Screenings/pricing | C | D | C owns scheduling, pricing, administrator adapter |
| Booking/history | D | A | D owns booking and client adapter |
| Analytics/fixtures | E | C | E owns fixtures, queries, reports, assembled evidence |

Letters remain provisional. Feature owners submit their own tests and notes; shared-file owners integrate changes. B/C changes to `src/client.py` are coordinated with D, E changes to `src/admin.py` with C, and changes to `queries.sql` with E. These are collaboration lanes, not instructions to launch implementation subagents.

## Ordered bundles and dependency graph

The canonical ledger is `tasks/todo.md`; every task and checkpoint starts TODO. Sizes: XS = one bounded document/check; S = one small component or review; M = one feature slice or substantial environment-verification session. Typical implementation file counts are S = 1–2 and M = 3–5, but coordination/test effort also determines size. Split a task before implementation if it exceeds five substantive files or one focused session. Routine ledger status/evidence notes are bookkeeping, not additional feature scope. DONE means all acceptance criteria and listed verification have passed; implementation-only progress cannot be marked DONE. Cross-feature checks with later prerequisites belong to named checkpoints or later tasks, not deferred acceptance on an earlier task.

| Merge window | Tasks | Checkpoint |
|---|---|---|
| Contracts/runtime | T01 contracts, T02 environment, T03 connection/test lifecycle | C01 |
| Database foundation | T04 ER/schema, T05 pricing, T06 representative seeds | C02: foundation freeze |
| First client flow | T07 login, T08 role dispatch, T09 list/add methods | C03 |
| Screening discovery | T10 deactivate methods, T11 search, T12 interval rules | C04 |
| First purchase | T13 create screening, T14 schedule/capacity, T15 atomic purchase | C05 |
| Transaction proof | T16 rollback, T17 last-seat race, T18 history | C06 |
| Reporting | T19 movie revenue, T20 theater revenue, T21 occupancy | C07 |
| Remaining race/SQL proof | T22 schedule race, T23 payment race, T24 five-query artifact | C08 |
| Complete experience | T25 CLI journeys, T26 contention demo, T27 handover docs | C09 |
| Delivery | T28 clean install, T29 instructor/submission closure, T30 team rehearsal | C10 |

Dependency edges (checkpoint windows give the default integration order, not unnecessary global feature prerequisites):

```text
T01 -> T02 -> T03 -> T04
T01 + T02 -> T05, T12
T04 + T05 -> T06
T04 -> T07 -> T08
T06 + T08 -> T09 -> T10
T05 + T06 + T08 -> T11
T06 + T08 + T12 -> T13 -> T14
T05 + T06 + T09 + T10 + T11 -> T15 -> T16 -> T17
T15 -> T18
T06 + T08 -> T19 -> T20 -> T21
T13 -> T22
T10 + T15 -> T23
T11 + T18 + T21 -> T24
T10 + T14 + T17 + T18 + T21 + T22 + T23 + T24 -> T25
T17 -> T26
T24 + T25 + T26 -> T27 -> T28
T01 + T08 + T27 -> T29
T26 + T27 -> T30
T28 + T29 + T30 -> C10
```

The high-risk path is contracts/runtime/schema → payment validation/search lookup → atomic booking → rollback/last-seat proof → delivery. After contract agreement, C can implement T05/T12 while A handles runtime/schema; B can implement T07 after T04; E can develop seeds/reports while D develops booking. T22 and T23 can start immediately after their prerequisites rather than waiting for reporting. Serialize tasks that touch the same file unless the primary editor integrates them. All real-MySQL feature verification waits for the isolated database foundation; mocks cannot satisfy that gate.

Run a cross-lane checkpoint after every two or three completed tasks even when the team reorders ready tasks. C01–C10 are the default sequence; an out-of-order checkpoint must list the actual task IDs and run their focused commands plus the applicable broad checks. From C02 onward, use `python -m pytest -q` to include every delivered scope, including race tests delivered early. On failure, mark the checkpoint BLOCKED and stop dependent integration; name an owner to fix forward or revert the failing change, rerun affected checks plus the checkpoint suite, and record the reviewing student's release of the checkpoint. Human contract/schema changes require affected-owner agreement under SPEC §11.

## Verification command contract

All commands run from the repository root with Python 3.13's virtual environment active. The SPEC §9 commands below are the adopted project contract, **not existing passing test scripts**. T02 installs/configures pytest and Ruff; T03 creates the test lifecycle; each later task creates its explicitly named tests before its verification command is run. A missing test, missing executable, zero collected tests, or skipped required MySQL test is a failed/incomplete gate. There is no compilation/build step.

### Environment (made valid by T02; tests require T03 onward)

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pip check
```

On fresh setup only, copy `.env.example` to `.env`; preserve an existing `.env`. After configuring its synthetic local settings:

```sh
docker compose --profile test config --quiet
docker compose up -d --wait db
docker compose --profile test up -d --wait test-db
```

T02 pins compatible versions in reproducible installation metadata and uses a pinned MySQL 8.4 image. Test settings exclusively use `TEST_DB_*`. Different credentials, database names, storage, and published ports distinguish the services. A dedicated test account must not have privileges on development data. T03 verifies the guard before exercising any destructive fixture setup.

### Fresh development database (T04/T06 onward)

On an empty, already-created database only:

```sh
docker compose exec -T db sh -c 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < schema.sql
docker compose exec -T db sh -c 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < data.sql
python -m src.main
```

Do not rerun clean-load commands against existing development tables. T28 verifies them with an isolated fresh Compose project and nonconflicting configured ports, using the same project selection for all Compose commands and matching application environment. Normal `docker compose --profile test down` preserves volumes; resets are separately documented and explicitly test-targeted.

### Focused and checkpoint checks

The ledger names exact test files. Each completed code task also runs Ruff on its changed Python files. At checkpoints, use the following commands when their scopes exist; full suites are required at C09/C10:

```sh
python -m pytest tests/unit -q
python -m pytest tests/integration -q
python -m pytest tests/concurrency -q
python -m pytest -q
python -m ruff check src tests
python -m ruff format --check src tests
git diff --check
```

C01 requires integration tests; unit starts T05 and concurrency starts with the first delivered race task (T17/T22/T23). Avoid issuing commands against nonexistent scopes or interpreting that absence as a pass. Checkpoints run all currently delivered tests once; re-run broader checks only after changes or unresolved failures. Record command, environment versions, result, and associated acceptance IDs in `docs/test-evidence.md` once T27 assembles it; preserve earlier outputs in task review notes meanwhile.

## Coverage matrix

| SPEC criterion | Implementing / proving tasks |
|---|---|
| SC1 ER and assumptions | T01, T04, T28 |
| SC2 schema and coherent data | T02–T04, T06, T28 |
| SC3 five SQL statements | T11, T18–T21, T24 |
| SC4 authentication/authorization | T07–T10, T13–T15, T19–T21, T25 |
| SC5 search and prices | T05, T11 |
| SC6 all client paths | T08–T11, T15, T18, T25 |
| SC7 all admin paths | T08, T12–T14, T19–T22, T25 |
| SC8 atomic purchase/invariants | T15–T17, T23 |
| SC9 exact last-seat result | T17, T26 |
| SC10 reports | T19–T21, T24–T25 |
| SC11 negative/race evidence | T07, T09–T10, T13, T15–T17, T22–T23, T27 |
| SC12 reproducible README/contributions | T27–T29 |
| SC13 full demonstration/understanding | T26–T28, T30 |
| SC14 instructor comment | T01, T08, T29 |

## Risks and outstanding decisions

| Risk | Impact | Mitigation / task |
|---|---|---|
| Proposed commands mistaken for existing tooling or Docker unavailable | High: blocks MySQL proof | T02/T03 establish tooling and service health; record failures honestly |
| Shared configuration or schema drift | High: blocks several lanes | T01 contracts; C02 freeze; named file integrators |
| Parallel test resets interfere | High: invalid evidence/data loss in test target | Separate verifier targets or E-serialized runs |
| Ignored documentation missing from submission | High: incomplete delivery | Narrow `.gitignore` in T02; inventory in T28 |
| REPEATABLE READ snapshot or lock ordering breaks invariants | High: overselling/overlap | Current reads, bounded race tests T17/T22/T23 |
| Rollback test only proves an insert is undone | High: partial purchases | T16 injects after insert and after counter update; prove reacquisition |
| Demo dates become past dates | Medium: demo fails | Seed relative to a declared date, controllable clock in tests, fresh rehearsal T06/T28 |
| Three theaters cannot cover four capability combinations | Medium: incomplete fixtures | T06 uses representative three-theater demo data plus focused fourth-combination test fixtures; T05 exhaustively covers eight prices |
| Price/capacity multiplication in report joins | High: wrong reports | Hand-calculated multi-purchase fixtures T19–T21 |
| Instructor clarification pending | High: blocks SC14 closure | B requests in T01 and confirms in T29; technical checks proceed independently |
| Student/date details pending | Medium: coordination risk | T01 records unknowns; T29 closes contribution names and records known date honestly |

## Plan review

The requested `plan-critic` reviewed both task documents against the approved specification and roadmap. Its first pass identified inconsistent verification prerequisites and an oversized combined delivery task. Those findings were fixed by moving cross-feature checks to their integration gates, synchronizing dependencies, and splitting delivery into T28–T30. Checkpoint failure handling, parallel test-target isolation, and risk impacts were also clarified.

Final re-review: **APPROVE — no Blocking or Should-fix findings remaining**. Structural validation confirms 30 uniquely numbered XS/S/M tasks, 10 checkpoints, all TODO, acceptance/verification sections for every task, and no task listing more than five substantive files. Planning whitespace checks pass. Application tests and MySQL startup have not been run; they are implementation-time gates. Next action: `/build`.
