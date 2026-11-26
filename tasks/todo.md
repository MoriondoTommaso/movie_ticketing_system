# Implementation ledger — Movie Ticketing System

**Execution order:** follow [parallel readiness and handoffs](parallel-work.md),
not task-number order. Each owner can start a task once its prerequisites are
verified and merged. Keep one active task per person and reserve shared-file edits.
Task and checkpoint acceptance criteria remain binding.

**Ownership authority:** [Named assignments](assignments.md) supersede provisional
A–E owner/reviewer/coordination references below. Bianca handles T29 submission
administration; Eleonora coordinates isolated verification runs.

Source: approved `plan/SPEC.md` and `plan/ROADMAP.md`; execution conventions and command prerequisites: `tasks/plan.md`.

GitHub tracking: [issue index](github-issues.md) maps every task/checkpoint to its published issue. Keep issue and ledger completion states aligned.

T01 and T02 are DONE; other tasks/checkpoints retain their listed states. Dependencies below are task IDs; checkpoints additionally verify the delivered prefix in the default order. Each task includes implementation plus meaningful feature verification, with at most five substantive files. Reviewers follow the plan's ownership table. Each feature owner provides review evidence and contribution notes as work lands.

## T01 — Freeze shared design contracts
- [x] **DONE · M · Owner Tommaso + all · Reviewer Eleonora · Depends: none · SC1, SC12**

**Files:** `docs/contracts.md`, `docs/assumptions.md`, `docs/fixtures.md`, `docs/contributions.md`.

**Acceptance:**
- [ ] Draft contracts using the completed 14 November design interview (SPEC §12). Record approved policies, Europe/Rome timezone, synthetic card-format limits, email normalization, table/column/type/key proposals, cardinalities, and each invariant's database/service enforcement location. Record named owners and confirmed 23 November 2026 submission date.
- [ ] Freeze operation names, arguments/results/errors, authenticated-principal trust boundary, connection lifecycle, transaction-compatible payment/screening helpers, clock injection, no-prompt service boundary, and screening→payment lock order with all consumers.
- [ ] Specify fixture IDs, hand-calculable report cases, role/ownership cases, capacity-10/sold-9 history, repeatable demo dates, and the field/parameter contracts for Q1–Q5; all five lanes review.

**Verification:** `git diff --check`; manual joint walkthrough of SPEC §§4–7 and SC1–SC13 against the contract/fixture documents, recording reviewers and unresolved items. No implementation proceeds on an unresolved behavior contract.

**T01 progress — 14 November 2026:** Draft T01-r1 in the four listed documents.
Policy/design interview complete; exact schema/API/error/fixture proposals await
all five reviewers in `docs/contributions.md`. No student signoffs fabricated.
Documentation-only: TDD/build/lint/types not applicable; tooling is a T02 task.
Verification: `git diff --check` passed; Python 3.13 document/oracle check passed
(four documents, 12 screenings, eight purchases, per-screening reconciliation,
all eight movie report totals, global 49 tickets / EUR840.20 / 220 seats).
Manual diff checkpoint: scoped documentation only; runtime checks are not claimed.
`/checkpoint` is unavailable in this session; independent approval is not claimed.
Draft commit: `043cfb1`. Draft PR: #41 (`task/T01-shared-design-contracts`).
External contract approval is still pending; do not merge yet.
T01 remains incomplete and T02 blocked on joint approval.

**Approval update — 14 November 2026:** After being explicitly asked whether to
replace the joint-review gate with their approval, the user replied "everything
is approved". This supersedes the pending-review notes above, accepts T01-r1 and
closes T01 using user approval, not claimed individual student signoffs.

## T02 — Establish reproducible Python and MySQL environments
- [x] **DONE · M · Owner Eleonora · Reviewer Tommaso · Depends: T01 · SC2, SC12**

**Readiness update — 14 November 2026:** T01 PR #41 merged as `8cabd99`;
explicit user approval above closes its remaining review gate. T02 is ready.
Packaging slice: inline TOML contract check failed for missing pinned connector,
then passed after metadata/package initialization. Editable `.[dev]` installation
passed on Python 3.13.13. Existing `.venv` lacked pip; bootstrapped with ensurepip
without replacing the environment. Packaging commit: `4b1d91c`.

**Files:** `pyproject.toml`, `compose.yaml`, `.env.example`, `.gitignore`, `src/__init__.py`.

**Acceptance:**
- [x] Editable Python 3.13 installation works with pinned compatible connector/dotenv and dev pytest/Ruff metadata; Flask is not required. Configure package discovery and Ruff consistently with SPEC §8.
- [x] Pinned MySQL 8.4/InnoDB development and profile-test services have healthchecks, independent storage/credentials/names/ports, and environment settings matching SPEC §9; startup initializes the empty databases and scoped users.
- [x] Intentional design/submission documents become trackable without bulk-adding ignored files; `.env` remains ignored and `.env.example` contains only fictional local credentials. Normal shutdown retains volumes.

**Verification:** Plan environment commands, `python -m pytest --version`, `python -m ruff --version`, `git check-ignore .env`, and `git status --short --untracked-files=all`. Inspect `docker compose --profile test config` for isolation and confirm services become healthy. A configured but unreachable Docker daemon is an incomplete gate.

**T02 evidence — 14 November 2026 (SC2, SC12):**
- Python 3.13.13; Docker server 29.7.2; Compose v5.5.1.
  Connector 26.10.0, dotenv 1.2.4, pytest 9.2.0, Ruff 0.17.5,
  setuptools 84.2.1; pytest transitive dependencies pinned in dev metadata.
- RED: inline TOML packaging assertion failed for absent pinned connector;
  GREEN after metadata/package slice. RED: Compose config reported no file;
  GREEN after adding compose.yaml. No application behavior or feature tests added.
- PASS: `.venv/bin/python -m pip install -e '.[dev]'`, `pip check`,
  `pytest --version`, `ruff --version`, `ruff check src`,
  `ruff format --check src`, and `git diff --check`.
  These use `.venv/bin/python -m` for the Python tools.
- PASS: `docker compose --profile test config --quiet`; inline configuration
  assertions verify digest pin, example-env parity, distinct credentials/names/
  ports/networks/volumes, test profile, local bindings and SELECT 1 healthchecks.
- Live verification used project `db-project-t02-20261114`, `--env-file .env.example`,
  and shell overrides `DB_PORT=23306 TEST_DB_PORT=23307` for every Compose call:
  `up -d --wait --wait-timeout 180 db`, then
  `--profile test up -d --wait --wait-timeout 180 test-db`; both healthy.
  Connector smoke assertions: 8.4.13, InnoDB, REPEATABLE-READ, empty schemas,
  distinct server UUIDs, grants limited to own database, opposite database
  USE denied with error1044. No schema/data writes or development resets.
  The first grant-format assertion was corrected to expect MySQL's escaped
  underscore in SHOW GRANTS; permission checks were not relaxed.
- PASS: `pip wheel --no-deps` into an approved temporary directory, fresh lean
  venv installs that wheel, `pip check`, and imports src/mysql.connector/dotenv
  outside the checkout; Flask and pytest absent from the lean installation.
- PASS: `git check-ignore .env`; `git check-ignore --no-index` confirms .env.example
  and intentional docs are not ignored. Existing .gitignore already meets T02;
  left unchanged. No .env overwritten or source PDF bulk-added.
- PASS: isolated `--profile test down` then `docker volume inspect` confirms
  both project volumes retained. No `down -v` or destructive cleanup.
- Feature pytest suites start in T03; none exist yet, so no zero-test run is
  reported as passing. No type checker is configured/required by this task.
  No next task started.
- Runtime commit: `8411533`. PR: #42 (`task/T02-runtime`).
  Manual PR-diff checkpoint: five scoped files, no implementation blockers found;
  credentials are explicitly fictional, localhost-only exposure, independent
  test storage/network/account, no schema changes or automatic destructive resets.
  `/checkpoint` remains unavailable; this is not an independent review.
  `gh pr checks 42` reports no configured checks. Reviewer approval and merge
  remain pending; T02 stays IN REVIEW and does not unlock merged-prerequisite work.

**Merge update — 14 November 2026:** User confirmed merging PR #42; GitHub
confirms merge commit `aa44bce15758cf6be4d25790f88fde7fa9744407`.
This supersedes the pending-review/merge notes above. T02 is DONE; its dependent
tasks may start when their other prerequisites are met. No next task started here.

## T03 — Make connections and isolated database tests usable
- [x] **DONE · M · Owner Tommaso, Eleonora fixture review · Reviewer Eleonora · Depends: T02 · SC2, SC8**

**Files:** `src/database.py`, `tests/conftest.py`, `tests/integration/test_database.py`.

**Acceptance:**
- [x] Connection factory uses explicit dev/test settings, separate connections, documented closing responsibility, and no hidden commit for caller-owned work; actual isolation is checked as REPEATABLE READ.
- [x] Test reset validates the complete configured target before destructive operations, refuses development identity/unsafe settings, and uses an account unable to modify development data. Missing MySQL fails required integration runs rather than silently skipping them.
- [x] Unseeded connection fixtures work now; later schema/seed fixtures have explicit opt-in lifecycle and reset only the test database. Verify connection independence, transaction rollback, resource cleanup and target refusal with a disposable probe table.

**Verification:** `python -m pytest tests/integration/test_database.py -q`; Ruff on these three files. Guard tests must demonstrate no destructive statement was issued for a rejected target; use fake settings/call capture for that negative case, not a destructive experiment on development data.

**T03 evidence — 14 November 2026 (SC2, SC8):**
- T02 merged and DONE; settings slice commit `4fd4fc3`. RED: missing database
  module; GREEN: 12 offline configuration cases. Subsequent RED runs identified
  missing reset/connection functions and fixtures; all now implemented.
- Scope: database settings/factory/closing context, opt-in test lifecycle,
  focused tests and this ledger. No schema, seed, authentication or menu work.
- Complete test settings never fall back to development. Reset requires a local
  loopback target, distinct published port/name/user/password, a test-prefixed
  or test-suffixed schema name and a non-root user. It freezes those settings,
  checks connected database/user and database-only grants, then drops only that
  test schema's base tables. Rejected settings make zero connections; rejected
  server identity/grants make no destructive statements. Guard negatives use
  fakes, never destructive experiments against development.
- `db_factory`/`db_connection` do not reset or seed; `empty_database` is explicit
  destructive opt-in for later schema/seed fixtures. Fixture/context cleanup
  rolls back pending work and closes connections; no implicit commit.
- Live target: Compose project `db-project-t03-20261114`, `--env-file .env.example`,
  shell overrides `DB_PORT=23316 TEST_DB_PORT=23317`; both services healthy after
  `--profile test up -d --wait --wait-timeout 180 db test-db`.
  Pytest subprocess environment = process env plus dotenv_values(.env.example)
  plus those two port overrides; no .env overwritten.
- PASS: `python -m pytest tests/integration/test_database.py -q` and
  `python -m pytest -q`: **43 passed, zero skipped**, real MySQL 8.4.13.
  Includes independent connection IDs, actual REPEATABLE-READ, visibility before
  commit, rollback, success/error cleanup, cleanup after failed rollback/drop,
  explicit guarded reset and test-user development access denied (1044).
- Availability proof: stopped only isolated test-db, ran the independent-
  connection test and observed one DatabaseError failure (not skip/fallback);
  restarted test-db and reran the complete suite green before commit.
- PASS: `python -m pip check`, `docker compose --profile test config --quiet`,
  `python -m ruff check src tests`, `python -m ruff format --check src tests`,
  `git diff --check`; tools run via `.venv/bin/python`.
- PASS: `pip wheel --no-deps` in an approved temporary directory; wheel contains
  src/database.py and excludes test fixtures. No type checker is configured.
  C01 command evidence is available; its review/release is not claimed here.
  PR/checkpoint review pending. No subsequent implementation task started.
- Lifecycle/guard commit: `c03612f`; PR #44 (`task/T03-database-lifecycle`),
  requested reviewer Eleonora. PR body closes issue #3 automatically upon merge.
  Manual PR-diff checkpoint: four scoped files; no implementation blockers found.
  `/checkpoint` is unavailable; no independent approval claimed.
  `gh pr checks 44` reports no configured checks. Review/merge remain pending;
  T03 remains IN REVIEW until that gate passes.
- Isolated verification project shut down without `-v`; both dev/test volumes
  confirmed retained with `docker volume inspect`. No active verification
  containers or development-table changes left behind.

**Merge update — 16 November 2026:** User confirmed T03 completed; GitHub
confirms PR #44 merged on 14 November. This supersedes the pending merge notes.
T03 is DONE. C01 verifies the integrated T01–T03 prefix, not later features.

## C01 — Runtime checkpoint
- [x] **DONE · Owner A + all · Depends: T01–T03**

**Acceptance/verification:** Review contracts; run `python -m pip check`, `docker compose --profile test config --quiet`, `python -m pytest -q`, both plan Ruff commands and `git diff --check`. Confirm independent healthy services and tracked design documents. Record pins and results.

**C01 evidence — 16 November 2026 (T01–T03 runtime prefix):**
- Base: `88676e4` (`origin/main`); branch `task/C01-runtime-checkpoint`.
  T01 user approval and T02 merge recorded above; T03 merged in #44.
  CI follow-up #45 is also merged. Only this ledger changes for C01.
- Verification-only task: no behavior changed, so no artificial RED test.
  `test-driven-development` loaded; `incremental-implementation` unavailable.
- Reviewed `docs/contracts.md` connection/transaction ownership against
  `src/database.py` and T03 fixture/test evidence: explicit independent settings,
  caller-owned transactions, no implicit commit, guarded opt-in test reset.
  Future schema/service contracts remain future tasks, not C01 runtime claims.
  Draft headings in T01 documents are superseded by the recorded user approval;
  proposed documentation cleanup is separate, not implemented here.
- PASS: `.venv/bin/python -m pip check`;
  `docker compose --env-file .env.example --profile test config --quiet`;
  `.venv/bin/python -m pytest -q`: **43 passed, zero skipped**;
  `.venv/bin/python -m ruff check src tests`;
  `.venv/bin/python -m ruff format --check src tests` (four files);
  `git diff --check`.
  The full suite includes all currently delivered integration tests; absent
  unit/concurrency scopes were not reported as passing.
- PASS: `pip wheel --no-deps` into approved temporary storage.
  No application compilation or configured type-checker gate exists for C01.
- Pins/runtime: Python 3.13.13, connector 26.10.0, dotenv 1.2.4,
  pytest 9.2.0, Ruff 0.17.5, Docker 29.7.2, Compose v5.5.1;
  build backend setuptools==84.2.1 in isolated build metadata.
  A diagnostic querying setuptools in the runtime venv failed because it is
  build-isolated, not a runtime dependency; wheel build passed. Corrected the
  version diagnostic to inspect runtime dependencies only; no package changes.
- Live project `db-project-c01-20261116`, `.env.example` plus exported
  `DB_PORT=23406 TEST_DB_PORT=23407`; existing `.env` untouched.
  Both services healthy with distinct server UUIDs, databases, accounts, ports,
  networks and volumes; MySQL 8.4.13 / InnoDB / REPEATABLE-READ on each.
  SHOW GRANTS limited each account to its own schema (plus global USAGE).
  Image digest: `sha256:a81d043930e51745522bd5c430961cf8286f0a23f0a9a2a6e0108f7ea71b0902`.
  Shutdown used `down` without `-v`; retained volumes, no development resets.
- PASS: `git ls-files --error-unmatch` for contracts, assumptions, fixtures,
  contributions and SPEC. Intentional design documents are tracked.
- Release pending: `/checkpoint` is unavailable in this session. Manual scoped
  diff review can be recorded, but is not the requested independent checkpoint
  approval or reviewing student's release. Do not merge until that gate passes.
  No next task started.
- Evidence commit: `f561ae0`; PR #46 (`task/C01-runtime-checkpoint`), refs #4.
  Manual diff review: ledger-only C01 evidence and direct T03 merge reconciliation;
  no implementation blockers found. Required checkpoint approval remains pending.

**Release update — 16 November 2026:** This supersedes the pending-release notes
above. Parallel read-only reviewer, security-auditor and test-engineer reviews
returned APPROVE/GO/ADEQUATE with no blockers. Both CI runs passed at `b948d98`.
Historical diff verification by subagents was limited and relied partly on
parent-supplied evidence; this limitation was disclosed in the consolidated GO.
The user then explicitly approved release ("ok go"); no individual student
signoff is inferred. C01 is DONE; PR #46 may merge after CI on this ledger update.
Optional follow-ups, not C01 blockers: reconcile stale contract approval wording;
preserve the original failure when rollback also fails; add grant-option refusal
and committed-work preservation regression tests. No next task started.

## T04 — Deliver ER model and enforceable relational schema
- [ ] **IN REVIEW · M · Owner Tommaso · Reviewer Eleonora · Depends: T03 · SC1, SC2**

**Files:** `schema.sql`, `docs/er-model-source.drawio`, `ER_diagram.pdf`, `tests/integration/test_schema.py`.

**Acceptance:**
- [ ] ER source/PDF captures all SPEC §5 attributes, identifiers, relationships, cardinalities and mandatory participation, including user/client distinction and movie languages/genres; all five review its correspondence to T01.
- [x] Clean schema load creates InnoDB tables, keys, relationship uniqueness, local positive/nonnegative checks and useful search/history indexes; unsupported cross-row rules are assigned to services, not falsely claimed as CHECK guarantees.
- [x] Real MySQL tests reject duplicate emails, invalid local numeric values, missing foreign keys and invalid movie-language associations; retained purchase references prevent destructive payment deletion. Document minimum-child rules that require seed/service validation.

**Verification:** Plan's clean `schema.sql` load command on the empty dev database; `python -m pytest tests/integration/test_schema.py -q`; manually open `ER_diagram.pdf` and compare every entity and constraint to the approved contract.

**T04 progress — 16 November 2026:** Branch `task/T04-relational-schema` from
merged C01 `1c72a42`. Scope is the four task files plus this ledger.
TDD slice 1: 46-line schema test failed with missing schema.sql against real
MySQL, then passed after creating the 11 mandatory-attribute InnoDB entities,
primary/foreign keys and enforcement-boundary comments. Focused test: 1 passed;
Ruff lint/format and whitespace checks passed. Constraints/indexes and ER
deliverables follow in scoped slices; no later task started.
Isolated verifier: `db-project-t04-20261116`, `.env.example` plus exported
`DB_PORT=23506 TEST_DB_PORT=23507`; existing `.env` preserved.
Foundation commit: `206e083`. Slice 2 RED: 25 missing CHECK/UNIQUE enforcement
failures (three existing structure/association tests passed). GREEN: 28 tests
passed after role/type, ASCII card format, boolean/numeric/amount constraints and
unique email/language/genre constraints. SQL error codes distinguish intended
constraint refusal from unrelated failures. Ruff lint/format and diff checks pass.
Constraint commit: `6d642be`. Slice 3 RED: required lookup/history/reverse indexes
missing (44 other cases passed). GREEN after explicit indexes: 45 passed.
Coverage includes every FK path, existing-but-unavailable screening language,
payment deletion refused while deactivation retains history, minimum valid
counts, zero amounts, default active state, both card-length bounds and duplicate
synthetic card numbers. Auto-created FK indexes remain where no explicit index
has the needed leading columns. No cross-row enforcement is claimed.

**T04 verification and review handoff — 16 November 2026:**
- Reference/index slice commit: `598579f`. Final test refinement isolates
  nonpositive quantity with zero price/total (so the amount equation cannot mask
  a missing quantity CHECK), and verifies exact Decimal 12.34 * 3 = 37.02.
- ER source: editable grouped entities and explicit routed FK edges in
  `docs/er-model-source.drawio` (open in diagrams.net, export all pages as PDF).
  `ER_diagram.pdf` has two vector pages: entities/attributes, then participation,
  local constraints, indexes and service/seed enforcement. Source and PDF were
  generated from the same layout using temporary tooling; no runtime dependency
  added. Opened/read the PDF and visually inspected both rendered pages.
- Live-schema/source comparison passed: all 11 entities, 45 attributes and
  12 FK relationships correspond exactly; every FK uses RESTRICT on update/delete,
  email uses utf8mb4_bin. Composite movie-language membership, client/admin
  profile distinction, mandatory participation and business minimum-child rules
  are explicit. Seed/services own cross-row rules as approved in T01.
- PASS: focused `python -m pytest tests/integration/test_schema.py -q`:
  **45 passed**; full `python -m pytest -q`: **88 passed, zero skipped**.
  Tools use `.venv/bin/python`, Python 3.13.13 / MySQL 8.4.13.
- PASS: guarded emptiness check of the isolated development schema, then plan's
  `docker compose exec -T db ... < schema.sql` clean-load command (MYSQL_PWD
  instead of a command-line password). No existing development schema overwritten.
- PASS: `python -m pip check`; `python -m pip wheel --no-deps` into temporary
  storage; `python -m ruff check src tests`;
  `python -m ruff format --check src tests` (five files); `git diff --check`.
  No configured type checker; no application compilation step.
- Verification services shut down without `-v`; both task-scoped volumes
  confirmed retained. No schema/data artifacts for T06 or later tasks added.
- Pending acceptance: all five teammates' ER/T01 correspondence review and
  PR checkpoint approval. `/checkpoint` and `incremental-implementation` are
  unavailable in this session; TDD skill already loaded. Manual diff review
  does not substitute for the required approvals. Do not merge until released.
- ER/evidence commit: `e6e496b`. Whole-branch whitespace review detected that
  the initial ASCII-encoded PDF was treated as text by Git. Re-exported using
  binary Flate streams; `pdfinfo` validates two pages, extracted text is identical,
  and base-to-tree whitespace checks now pass. No schema/test behavior changed.
- Artifact export commit: `daed6cc`. PR #47 (`task/T04-relational-schema`), refs
  issue #5; Eleonora requested as reviewer. Manual PR diff: five scoped files,
  no implementation blockers found. T04 remains IN REVIEW pending the explicit
  ER/team and checkpoint approvals; no next task started.

## T05 — Implement the authoritative ticket price
- [ ] **IN REVIEW · S · Owner C · Reviewer D · Depends: T01, T02 · SC5, SC8**

**Files:** `src/pricing.py`, `tests/unit/test_pricing.py`.

**Acceptance:**
- [x] Decimal pricing produces EUR 15/20/18/23 and discounted 12/16/14.40/18.40, applying discount after all theater surcharges and final two-decimal rounding.
- [x] Calendar-year boundary tests cover exactly two years, day before/after, and Feb 29 → Feb 28 anniversary; no dependence on wall-clock test execution date.
- [x] One typed service contract is usable by search and booking without display logic or duplicated formulas.

**Verification:** `python -m pytest tests/unit/test_pricing.py -q` and focused Ruff.

**T05 progress — 17 November 2026:** T01/T02 DONE; branch
`task/T05-authoritative-pricing` from `origin/main` (`7ea976a`).
Only the two task files and this ledger are in scope. TDD skill loaded;
`incremental-implementation` unavailable. Frozen API: `calculate_unit_price`
with release/screening dates and both capability flags, returning Decimal.

**T05 verification — 17 November 2026 (SC5, SC8):**
- RED 1: missing `src.pricing`; GREEN: four undiscounted capability cases.
  RED 2: seven expected discount failures, ten passing cases; GREEN: 17 passed.
  Tests check all eight prices and two-decimal exponent, exact/day-before/
  day-after anniversary, Feb 29 → Feb 28, and a 730-day non-anniversary case.
- PASS: `.venv/bin/python -m pytest tests/unit/test_pricing.py -q`: **17 passed**;
  full `python -m pytest -q`: **105 passed, zero skipped**.
  Full-suite subprocess used process environment plus `.env.example` and
  DB_PORT=23606 / TEST_DB_PORT=23607. Initial environment-wrapper construction
  failed with duplicate keyword arguments before pytest; corrected wrapper only.
- Live verification: isolated Compose project `db-project-t05-20261117`,
  `--env-file .env.example --profile test`, both db/test-db healthy;
  existing `.env` preserved and no normal development database reset.
- PASS: Ruff check and format check on `src tests`, `pip check`, wheel build
  (`pip wheel --no-deps` into approved temporary storage), Compose config,
  and `git diff --check`. No configured type checker or compilation gate.
- Manual scoped diff review: pricing follows the frozen typed API, uses exact
  Decimal arithmetic and explicit dates, with no I/O or duplicated display formula.
  `/checkpoint` is not available as a session tool; independent checkpoint
  approval remains pending. Do not merge before that gate and green CI.
  No next task started.
- Implementation commit: `cc4c767`; PR #48 (`task/T05-authoritative-pricing`).
  Verification services stopped with `down` without `-v`; volumes retained.
  T05 remains IN REVIEW pending checkpoint approval and CI.

## T06 — Populate coherent, reproducible movie data
- [ ] **IN REVIEW · M · Owner E · Reviewer C · Depends: T04, T05 · SC2, SC10**

**Files:** `data.sql`, `tests/integration/test_seed.py`, `docs/fixtures.md`, `tests/conftest.py`.

**Acceptance:**
- [x] Seed 6–8 movies, 2–3 theaters, 6–8 clients plus admin, multiple synthetic methods/languages/genres, 12–15 screenings and purchases. Seed documented salted scrypt credentials with recorded parameters compatible with T01, not plaintext database passwords.
- [x] Original/available languages and genres meet minimum cardinalities; schedules respect rules; purchase totals/counters reconcile, including zero/partial/full and capacity-10/sold-9 cases, foreign and inactive methods. With only 2–3 demo theaters, supply a fourth capability combination in focused test fixtures to cover all eight prices.
- [x] Fixtures control dates and offer a repeatable relative-date demo seed policy; expose known report expectations including multiple purchases per screening, different capacities, and movies without screenings.

**Verification:** Plan's clean `data.sql` load after schema; `python -m pytest tests/integration/test_seed.py -q`; manually reconcile fixture quantities and captured totals with the fixture document.

**T06 progress — 17 November 2026:** Branch `task/T06-reproducible-seed`
from `ef43e5f`. GitHub confirms T04 #47 and T05 #48 merged; T05 approved
with successful CI, superseding its pending merge note above. TDD first:
42-line seed tests fail because the opt-in seeded fixture is missing.
Frozen T01 oracle: 12 screenings, eight purchases, anchor D=2026-11-23.
TDD instructions retained; incremental-implementation skill unavailable.
Fixture implementation exposed missing data.sql on real MySQL (RED), then
two tests passed with shipped seed inventory, distinct salted scrypt hashes and
49 tickets / EUR840.20 captured totals. Focused Ruff passes. Isolated verifier:
`db-project-t06-20261117`, `.env.example`, ports 23706/23707; `.env` preserved.

**T06 verification — 17 November 2026 (SC2, SC10):**
- Seed/lifecycle slice: `cb38f98`. Second RED: missing opt-in fourth-theater
  fixture; GREEN after adding it. Focused suite: **6 passed**, including
  independent-connection visibility, all eight prices and unchanged three-theater
  report totals. Uses the approved eight-purchase oracle (SPEC §5 says several
  purchases; 12–15 is the screening count), rather than changing T01 fixture IDs.
- Full suite: **111 passed, zero skipped**, Python 3.13 / MySQL 8.4.13.
  Pytest ran via `.venv/bin/python`, process env plus `.env.example` plus the
  two port overrides above. Missing MySQL remains a failure, not a skip.
- PASS: `ruff check src tests`, `ruff format --check src tests` (eight files),
  `pip check`, `pip wheel --no-deps` into approved temporary storage,
  Compose `--profile test config --quiet`, and `git diff --check`.
  No configured type checker or compilation gate.
- PASS: confirmed isolated dev schema empty (zero tables), then imported
  `schema.sql` and `data.sql` through Compose exec/mysql without `--force`.
  Independent SQL output: eight purchases / 49 tickets / EUR840.20 / 220 seats.
  Hand reconciliation: movie revenues 215+540+24+43.20+18=840.20;
  theater revenues 159+80+601.20=840.20; movie seat totals
  30+40+30+40+50+10+20=220. Each sold counter matches purchase quantities.
- Fixed anchor and complete date-rebase mapping documented in `docs/fixtures.md`;
  no runtime clock dependency, existing history rewrite or dev reset.
- Manual scoped diff review: five task/ledger files, exact frozen IDs, salted
  credentials, explicit opt-in resets and transaction commit; no blockers found.
  Graph coverage is best-effort; SQL parse gaps were verified directly in source
  and by actual imports. `/checkpoint` remains unavailable, so independent
  checkpoint approval is pending. No merge or next task before that gate.
- Verification/documentation commit: `51a72f5`; PR #49
  (`task/T06-reproducible-seed`). Isolated services stopped using `down` without
  `-v`, retaining volumes. T06 remains IN REVIEW pending checkpoint and CI.

## C02 — Foundation freeze
- [x] **DONE · GO · Owner A + all · Depends: C01, T04–T06**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; verify clean schema/data loads and ER review. All lanes sign the first schema/service/fixture contract revision; changes thereafter require affected-owner review. Confirm exact dependency/image versions and timezone.

**Release decision:** The user approved freezing the schema, service and fixture
contracts at `e869f32`, including the final three-page ER from #50. When asked
whether to waive the five-lane signoff requirement for C02, the user replied
“ok go”. This is user approval, not five individual signatures. Future contract
changes still require affected-owner review.

**Evidence:** [CI at the frozen revision](https://github.com/MoriondoTommaso/movie_ticketing_system/actions/runs/44482552846)
passed all 111 tests and Ruff lint/format. `git diff --check 1c72a42 e869f32`
passed. The clean MySQL 8.4.13 import reconciled 49 tickets, EUR840.20 and 220
offered seats. Review confirmed the dependency and image pins, Europe/Rome
timezone, and final ER-to-schema correspondence. The three checkpoint reviews
found no blocking technical defect. Release tracked in #8.

## T07 — Authenticate preloaded users and enforce stored roles
- [ ] **IN REVIEW · S · Owner B · Reviewer E · Depends: T04 · SC4, SC11**

**Files:** `src/auth.py`, `tests/integration/test_auth.py`, `src/database.py` (user-approved shared auth contracts only).

**Acceptance:**
- [x] Authentication trims/normalizes email, verifies the approved scrypt hash format, and returns a verified principal with the database role; invalid credentials fail consistently and inputs are bound parameters.
- [x] Direct role checks deny missing/invalid principals, clients calling administrator operations, and inappropriate admin-as-client requests according to the frozen contract; no interface-supplied role is accepted as authority.
- [x] Tests cover normalization/uniqueness, invalid password/email, malformed stored hashes and connection failure cleanup; service APIs neither prompt nor print secrets.

**Verification:** `python -m pytest tests/integration/test_auth.py -q` with task-local accounts inserted into the isolated schema fixture; do not require T06's demo seed. C03 checks the shipped demo credentials separately.

**T07 blocker — 19 November 2026:** Branch `task/T07-authentication` from
`origin/main` (`e869f32`); T04 PR #47 is merged. Graph lookup (generation
2026-11-19T07:55:26Z), path coverage and direct source inspection confirm
`src/database.py` provides only CinemaError, ValidationError and DatabaseError;
AuthenticationError, AuthorizationError and verify_principal are absent.
The frozen contract (§§2–3) places those shared auth errors and the borrowed-
connection principal verifier in database.py, outside T07's two allowed files.
Implementing replacements in auth.py would change the shared contract.
Await explicit permission to include src/database.py in T07, or a separately
approved prerequisite task providing these contracts. No implementation or
tests changed; no RED commit. TDD skill already loaded; requested
incremental-implementation remains unavailable. No next task started.

**T07 resolution:** User approved adding `src/database.py` to T07. RED:
focused tests failed to collect because `src.auth` did not exist. GREEN: nine
initial cases, then 16 focused cases total. The shared verifier checks stored
role and client profile on a borrowed connection without owning its transaction.
Login verifies bounded scrypt hashes and releases its owned connection on
success, refusal, and driver failure. Tests use task-local accounts, not demo seed.
Full suite: **127 passed**. Ruff lint/format, `pip check`, wheel build and
`git diff --check` passed. No configured type checker. Isolated Compose project
`db-project-t07`, `.env.example`, ports 23806/23807. Checkpoint and CI pending.
Implementation: `67a6b8f`; PR #52. Isolated services stopped without `-v`.
Checkpoint correctness, security, and test reviews launched on the PR diff.
Correctness and security found no blockers. Test review found a missing positive
database-backed client check; added it and reran focused (16 passed), full
(127 passed), Ruff lint/format, and whitespace checks. No runtime code changed.
Checkpoint GO after the coverage fix; revert the PR if an integration regression
appears. Merge still requires green CI on the final head and repository approval.

## T08 — Open authenticated CLI sessions with role dispatch
- [x] **DONE · M · Owner B, D/C adapter coordination · Reviewer E · Depends: T07 · SC4, SC6, SC7**

**Files:** `src/main.py`, `src/client.py`, `src/admin.py`, `tests/unit/test_cli_auth.py`.

**Acceptance:**
- [x] `python -m src.main` asks for email/password, routes using the authenticated principal, and supports exit/EOF; invalid login/input/database errors return understandable outcomes without tracebacks or open resources.
- [x] Establish thin client/admin adapter entry points for incremental feature handlers; unavailable functions are not presented as working. Preserve the root greeting scaffold and document the canonical module entry point in the later README.

**Verification:** `python -m pytest tests/unit/test_cli_auth.py -q` covering client/admin dispatch, invalid credentials, exit and EOF using service fakes; real auth is verified by T07. Seeded live CLI login is a C03 integration obligation, not a prerequisite for completing T08.

**T08 evidence:** T07 merged as `7f2a141` (#52). RED: missing `src.main`
at collection. GREEN: 12 focused tests, including module exit, both stored
roles, retries, EOF and refusal of an echoed password prompt. Full suite:
162 passed on isolated MySQL (Compose `db-project-t08`, ports 23906/23907).
Ruff lint/format, `pip check`, wheel build and diff whitespace passed; no
configured type checker. Root greeting untouched. Only Exit is available in
the role adapters until downstream features land. Implementation: `047828c`;
PR #54. The isolated Compose services were stopped without deleting volumes.
Checkpoint GO: correctness, security, and test reviews found no blockers.
Optional follow-ups: assert the exact Exit-only choices for both menus and
assert that a rejected login followed by exit never calls a role adapter.
Seeded live login remains C03 work. If an integration regression appears,
revert PR #54 and rerun the focused and full checks.

## T09 — Let clients list and add their payment methods
- [x] **DONE · M · Owner B, D integrates adapter · Reviewer E · Depends: T06, T08 · SC6, SC11**

**Files:** `src/payments.py`, `src/client.py`, `tests/unit/test_payment_validation.py`, `tests/integration/test_payments.py`, `src/database.py` (approved retryable error subclass only).

**Acceptance:**
- [x] CLI management lists only the authenticated client's methods, masks numbers and shows active state; add accepts approved synthetic credit/debit fields and required billing address.
- [x] Service-boundary tests reject malformed fields, unauthenticated/inappropriate principals and foreign-owner access; supplied SQL-like text cannot change query structure.
- [x] Provide transaction-compatible payment lookup/validation on the caller's connection, with no implicit commit, so booking can lock and revalidate ownership/activity.

**Verification:** `python -m pytest tests/unit/test_payment_validation.py tests/integration/test_payments.py -q`; manual `python -m src.main` → client → payment management → add/list and invalid-input recovery.

**T09 blocker:** T06 and T08 are merged. The frozen contract (§§2, 4)
requires `lock_valid_method` to lock the payment row with `FOR UPDATE` and
defines `database.RetryableDatabaseError` for lock timeouts and deadlocks.
Graph lookup and source inspection found `DatabaseError` but no shared
retryable subclass. `src/database.py` is outside T09's allowed files.
Await approval to add just that class there or to defer typed lock-error
classification to a separate task. No implementation or test changes.

**Resolution and verification:** User approved the shared error subclass. RED:
missing payment module, then a failing CLI flow with no payment menu. GREEN:
22 focused and 184 full-suite tests passed on isolated MySQL. The caller-held
row lock blocked a second connection with a bounded timeout; retry succeeded
after caller rollback. Ruff lint/format, dependency check and wheel build
passed. No configured type checker. Interactive `python -m src.main` verified
masked list, invalid-number recovery, add, relist and exit against isolated
seeded MySQL, ports 24006/24007. Checkpoint and CI required before merge.
Implementation: `7ea9023`; PR #55. Checkpoint GO: correctness, security, and
test reviews found no merge blockers. The final diff confirms that the retryable
error subclass is the only `src/database.py` change.
Proposed follow-ups: hide synthetic number entry; test rollback/close after a
failed write and preserve the original error on cleanup failure; assert relisting
separately from add confirmation. If an integration regression appears, revert
PR #55 and rerun focused and full checks.

## C03 — First client flow checkpoint
- [ ] **TODO · Owner B + all · Depends: C02, T07–T09**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; use `python -m src.main` to verify T06's documented client/admin credentials, invalid credentials, exit/EOF, role dispatch → add/list owned method and client rejection at an admin service boundary/role guard.

## T10 — Deactivate methods without losing purchase references
- [ ] **IN REVIEW · M · Owner B, D integrates adapter · Reviewer E · Depends: T09 · SC6, SC8**

**Files:** `src/payments.py`, `src/client.py`, `tests/integration/test_payments.py`.

**Acceptance:**
- [x] Owner can deactivate through CLI; state change is irreversible within the initial scope and preserves existing purchase references. Repeated deactivation has a documented consistent outcome.
- [x] The service locks the payment row while checking ownership and changing state; inactive or foreign methods fail purchase validation on a caller-owned transaction.
- [x] Validation/database failures roll back and release connections/locks; history references and method visibility remain intact.

**Verification:** `python -m pytest tests/integration/test_payments.py -q`; manual deactivation path via `python -m src.main`, checking an existing seeded purchase reference still exists.

**T10 evidence:** T09 merged at `9524f76`. RED: six failures for missing
service/CLI deactivation; GREEN: 21 focused and 191 full-suite tests on
isolated MySQL. Repeated deactivation of an owned inactive method succeeds
without changing it. Tests verify an actual lock timeout and release,
rollback of a written state change after an injected pre-commit failure,
and retained history. The seeded CLI relisted method 201 as inactive;
SQL independently confirmed purchases 303 and 308 still reference it.
Ruff lint/format, pip check, wheel build and whitespace passed; no configured
type checker. Implementation: `c282971`; PR #56. Checkpoint GO: correctness,
security, and test reviews found no blockers. Non-blocking test follow-ups:
exercise deactivation directly with unauthorized principals and verify the
lock on an already-inactive method. Isolated Compose services stopped without
deleting volumes. T10 remains IN REVIEW until the user merges after green CI.

## T11 — Search screenings from the client menu
- [ ] **IN REVIEW · M · Owner C, D adapter / E query integration · Reviewer D · Depends: T05, T06, T08 · SC3, SC5, SC6**

**Files:** `src/screenings.py`, `src/client.py`, `tests/integration/test_search.py`, `queries.sql`, `src/database.py` (approved clock and not-found definitions only).

**Acceptance:**
- [x] Combined title-substring, exact genre/language/date and inclusive optional time-range filters use AND and bound parameters; invalid ranges are rejected and genre joins cannot duplicate screenings.
- [x] Results ordered by start then ID contain movie/theater/date/time/language, authoritative unit price, advisory available seats and both capability flags; display and empty-result behavior work in CLI.
- [x] Add Q1 to the query artifact and supply transaction-compatible authoritative screening lookup for booking without committing its connection.

**Verification:** `python -m pytest tests/integration/test_search.py -q`; manual combined search and no-results path using `python -m src.main`; inspect representative bound-parameter execution against MySQL.

**T11 blocker:** T05, T06 and T08 are merged. The frozen contract (§§2–4)
places `default_clock` and `NotFoundError` in `src/database.py`. Graph and
source checks confirm both are missing. Search needs the shared clock for
future-only results; `lock_screening` needs the shared error for a missing
screening. `src/database.py` is outside T11's allowed files. Await approval to
add only those two shared definitions. No implementation or tests changed.

**Resolution and verification:** User approved both shared definitions. RED:
missing `NotFoundError`, then missing Q1 and CLI search. GREEN: 11 focused and
202 full-suite tests on isolated MySQL (ports 24306/24307). Bound Q1 results
matched the service, which uses the authoritative Python price calculation.
The locking lookup read past a stale snapshot and held the screening lock
until caller rollback. Seeded `python -m src.main` combined filter, empty
result, and exit passed. Ruff lint/format, dependency and wheel build checks,
and whitespace passed. No configured type checker. User owns the merge.
Implementation: `1bd120d`; PR #57. Correctness, security, and test checkpoint
reviews launched. Isolated Compose services stopped without deleting volumes.

**Checkpoint fixes:** The correctness review requested catalog choices and
independent filter assertions. Added authenticated genre/language reads and
displayed their ID/name choices before prompting. Added near-miss rows for each
filter and checked expected IDs independently through the service and bound Q1.
RED: CLI test failed on the missing choices. GREEN: 13 focused and 204 full-suite
tests, plus Ruff, dependency, wheel and whitespace checks. Follow-up commit:
`e0c98aa`. Checkpoint GO: correctness, security, and test re-reviews found no
blockers. Optional follow-ups: Q1 parity at the exact start cutoff and leap-day
pricing boundary, and direct search role-denial tests. T11 remains IN REVIEW
until the user merges after green CI.

## T12 — Specify valid screening intervals in executable rules
- [ ] **IN REVIEW · S · Owner Eleonora · Reviewer Tommaso · Depends: T01, T02 · SC7**

**Files:** `src/schedule_rules.py`, `tests/unit/test_schedule_rules.py`.

**Acceptance:**
- [x] Minute-resolution runtime fits the same local date between 10:00 and 23:59 inclusive at boundaries; reject before-open, too-late and date-crossing intervals.
- [x] Half-open overlap rejects intersecting intervals and permits exact back-to-back screenings; cover equal starts, contained intervals, adjacent dates and exact close.
- [x] Pure rules use the frozen timezone/clock convention and explicit types, shared with scheduling rather than copied into the menu.

**Verification:** `python -m pytest tests/unit/test_schedule_rules.py -q` and focused Ruff.

**T12 evidence — 18 November 2026:**
- Tests first: RED (missing `src.schedule_rules`), GREEN 16 interval cases;
  RED (missing `overlaps`), GREEN 23 cases.
- PASS: `python -m pytest tests/unit/test_schedule_rules.py -q` → 23 passed;
  `python -m pytest tests/unit -q` → 40 passed.
- PASS: `ruff check src tests`, `ruff format --check src tests`, `git diff --check`.
- The "start in the future" rule is not in T12: these functions have no clock,
  so T13 checks it after locking the theater row.

## C04 — Discovery/payment checkpoint
- [ ] **TODO · Owner C + all · Depends: C03, T10–T12**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; demonstrate price/filter results, invalid ranges, and irreversible method deactivation with preserved references.

## T13 — Create a valid screening from the administrator menu
- [ ] **IN REVIEW · M · Owner C · Reviewer D · Depends: T06, T08, T12 · SC7, SC11**

**Files:** `src/screenings.py`, `src/admin.py`, `tests/integration/test_scheduling.py`, `tests/unit/test_cli_auth.py` (approved obsolete menu assertion update only).

**Acceptance:**
- [x] Authorized administrator can select existing movie/theater, allowed language and valid interval; missing entities, invalid language/time and overlaps fail with no inserted row.
- [x] Transaction acquires theater lock before checking/inserting; overlap uses a current/locking read so a preexisting snapshot cannot hide a just-committed competitor. Failure rolls back and closes resources.
- [x] Direct service calls by clients fail; CLI validates input and presents service errors without SQL or business logic in the adapter.

**Verification:** `python -m pytest tests/integration/test_scheduling.py -q`; manual valid, back-to-back and rejected overlap creation via `python -m src.main`.

**T13 blocker:** T06, T08, and T12 are merged. The T08 CLI test
`test_menu_recovers_without_advertising_unimplemented_features` in
`tests/unit/test_cli_auth.py` explicitly requires “Add screening” to be absent
and uses choice `1` as invalid. T13 makes that feature available; preserving
the old expectation would require hiding or renaming a delivered feature.
Await approval to update just this out-of-scope regression test to use an
invalid choice and check that a still-unimplemented action is not advertised.
No implementation or test changes.

**Resolution:** User approved the T08 assertion update. RED: 11 failures for
the missing service and menu. GREEN: 25 focused scheduling/CLI tests and 217
full-suite tests on isolated MySQL. Tests check stale-snapshot rejection,
theater lock before clock access, and connection closure on timeout. The seeded
CLI accepted two back-to-back creations and declined an overlapping request.
Ruff lint/format, dependency and wheel checks, and whitespace passed. No
configured type checker. The T12 overflow edge is translated at the scheduling
service boundary; no changes to T12. Only the user merges.
Implementation: `bb7f80b`; PR #58. Checkpoint reviews launched. Isolated
Compose services stopped without deleting volumes.

**Checkpoint follow-up:** The T08 regression now asserts the actual menu
prompts, not stdout alone. Scheduling tests cover malformed CLI input followed
by successful creation, persisted selected IDs, and an existing language not
offered for the selected movie. No service changes. Reverification at `f6d7ef5`:
26 focused and 218 full-suite passes on MySQL. Checkpoint GO: correctness,
security, and test reviews found no blockers after the follow-up. Optional
tests: mixed-runtime overlap and injected failure after insert. The synchronized
two-writer race remains T22. T13 stays IN REVIEW until the user merges.

## T14 — Show schedule and remaining capacity to administrators
- [ ] **IN REVIEW · M · Owner C · Reviewer D · Depends: T13 · SC7**

**Files:** `src/screenings.py`, `src/admin.py`, `tests/integration/test_schedule_views.py`, `tests/unit/test_cli_auth.py` (approved menu expectation only).

**Acceptance:**
- [x] Both required menu paths show deterministic schedule ordering and capacity minus sold count, with full/partial/empty cases and relevant movie/theater/time identifiers.
- [x] Views enforce administrator authorization at service entry and handle empty results/database errors through the common error contract.
- [x] Tests demonstrate capacity against known sold/capacity fixtures and newly created screenings; displayed capacity is explicitly advisory for booking. Cross-feature search comparison is owned by C05.

**Verification:** `python -m pytest tests/integration/test_schedule_views.py -q`; manual both admin views via `python -m src.main`.

**T14 blocker:** T13 merged as `d28b51d` (#58), with both CI checks green.
The existing T08 regression in `tests/unit/test_cli_auth.py` asserts the
exact Add-screening-and-Exit menu before and after invalid input. T14 must
add two visible actions, so the full suite requires updating that assertion.
The test is outside T14's allowed files, and the previous exception covered
T13 only. Await approval to update the expected menu while preserving the
invalid-input recovery and exact-menu checks. No implementation changed.

**Resolution:** User approved updating the exact expected menu. RED: six
failures for missing view services. GREEN: 19 focused and 225 full-suite tests
on isolated MySQL. Checks include historical rows, deterministic ordering,
authorization, optional date filter, and seat counts for seeded and newly
created screenings. Both menu paths verified via seeded `python -m src.main`.
Ruff, dependencies, wheel, and whitespace passed. No configured type checker.
Implementation: `cd7a401`; PR #59. Checkpoint GO: correctness, security, and
test reviews found no blockers. Optional follow-ups: assert complete rendered
rows, exercise CLI recovery after malformed dates and database failures, and
inject query/cleanup failures. Isolated Compose services stopped without
deleting volumes. T14 stays IN REVIEW until the user merges after green CI.

## T15 — Buy multiple tickets atomically through the CLI
- [ ] **IN REVIEW · M · Owner D · Reviewer A · Depends: T05, T06, T09, T10, T11 · SC6, SC8, SC11**

**Files:** `src/booking.py`, `src/client.py`, `tests/integration/test_booking.py`, `tests/unit/test_booking_validation.py`, `src/database.py` (approved `CapacityError` only).

**Acceptance:**
- [x] Authenticated client submits screening/quantity/method; reject zero, negative, noninteger (including boolean) quantities and already-started screenings using the controlled cinema clock. No prompt occurs inside a transaction.
- [x] One transaction locks screening then payment, reads current capacity, revalidates owner/active method, computes Decimal price internally, inserts captured unit/total and increases sold count, committing only both together.
- [x] Real MySQL cases verify multi-ticket success and persisted totals/counter, missing IDs, foreign/inactive methods and insufficient capacity with no partial state; CLI displays structured purchase confirmation or understandable failure.

**Verification:** `python -m pytest tests/unit/test_booking_validation.py tests/integration/test_booking.py -q`; manual `python -m src.main` purchase and persisted confirmation, using independent SQL reads in the integration tests to verify counter/amounts. The admin capacity comparison belongs to C05. No interface amount/role/availability may override database facts.

**T15 blocker:** T05, T06, and T09–T11 are merged. The frozen exception
contract (§2) locates `CapacityError` in `src/database.py`, but the graph
and direct source inspection confirm it is missing. Booking needs it to
distinguish insufficient capacity from other request failures; defining it in
`src/booking.py` would change the shared contract. `src/database.py` is outside
T15's allowed files. Await approval to add only the missing exception subclass.
No implementation or test changes.

**Resolution:** User approved adding `CapacityError`. RED: focused tests could
not import the missing booking module. GREEN: 13 focused tests and 238
full-suite tests passed on isolated MySQL. Seeded CLI purchase 309 confirmed
two tickets at EUR14.40 each / EUR28.80 total, with independent SQL confirming
the captured amounts and sold count rising from 3 to 5. Ruff lint/format,
dependencies, wheel build, and whitespace passed; no configured type checker.
Write-failure injection and coordinated last-seat race remain T16/T17.
Implementation: `5c65cc0`; PR #60. Checkpoint GO: correctness, security, and
test reviews found no blockers. The exact diff confirms `CapacityError` is the
only database module change. Optional follow-ups: cover rejection of a naive
clock and assert the complete CLI receipt in the automated test. The integrated
schedule/search/admin capacity comparison remains C05. Isolated Compose stopped
without deleting volumes. T15 stays IN REVIEW until the user merges after CI.

## C05 — First-purchase checkpoint
- [ ] **TODO · Owner D + all · Depends: C04, T13–T15**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; cross-review the exact transaction lock/write/commit sequence and demonstrate schedule creation → search → multi-ticket purchase → changed capacity. Explicitly compare T11 search availability with T14 admin views before/after the T15 purchase. Do not claim concurrency proof until the relevant race tests pass.

## T16 — Prove rollback and lock release after failed writes
- [ ] **IN REVIEW · S · Owner D · Reviewer A · Depends: T15 · SC8, SC11**

**Files:** `src/booking.py`, `tests/integration/test_booking_failures.py`.

**Acceptance:**
- [x] Inject failures after purchase insertion and separately after counter update but before commit; both leave purchase rows and sold counts unchanged, observed from a separate connection.
- [x] Another connection can successfully book after each failure with bounded waits, proving transaction/lock cleanup; all cursors/connections are released on validation and database errors.
- [x] Controlled real lock timeout plus injected connector deadlock/commit-error paths demonstrate rollback and a retryable error classification where applicable, without automatic retries or duplicate writes. Do not assert a known rollback after an indeterminate lost commit acknowledgement; distinguish that database failure.

**Verification:** `python -m pytest tests/integration/test_booking_failures.py -q`; review injection seams for deterministic tests and absence of user-facing failure switches.

**T16 evidence:** T15 merged at `65d07c2`. RED: lost commit acknowledgement
was reported as a generic database failure. GREEN: 7 focused and 245 full-suite
tests on isolated MySQL (ports 24906/24907). Post-write rollback verified by
independent read and bounded retry; real payment-row timeout, injected deadlock,
validation cleanup, and committed-but-unacknowledged outcome covered. Fault
injection is test-only via the existing connection factory. No auto-retry.
Ruff lint/format, pip check, wheel build and whitespace passed. No configured
type checker. Checkpoint pending; only the user merges.
Implementation: `8a9dcf6`; PR #61. Checkpoint reviews launched; isolated
Compose services stopped without deleting volumes.

**Review follow-up:** RED: a cursor-close failure masked an injected write
deadlock. The write cursor now preserves the primary error and still rolls
back on a close-only failure. Tests also cover rollback failure after a lost
commit acknowledgement and receipt delivery after an acknowledged commit
followed by a close failure. GREEN: 10 focused and 248 full-suite tests;
Ruff, pip and whitespace checks passed. Follow-up: `9a366ed`. Checkpoint GO:
correctness, security and test re-reviews found no blockers. Optional test
hardening: assert that the double-fault cursor-close hook ran. T16 remains
IN REVIEW until the user merges after green CI.

**CI follow-up:** Linux CI reported four cursor-close spy failures. Tests now
observe context-manager exit and explicit close at the caller boundary rather
than relying on the connector to invoke a monkeypatched instance method.
Cleanup assertions remain in place; no runtime changes. Full local suite:
248 passed; Ruff lint/format passed. Final CI pending.

**Second CI follow-up:** The cursor wrapper still intercepted connector-internal
cursor calls when patching the real connection. Pass a test-only connection
proxy instead, so assertions apply only to cursors requested by the service.
No production changes. Local MySQL: 10 focused and 248 full-suite passes;
Ruff lint/format passed.

## T17 — Prove the exact last-seat contention outcome
- [ ] **IN REVIEW · S · Owner D · Reviewer A · Depends: T16 · SC9, SC11**

**Files:** `tests/concurrency/test_last_seat.py`, `src/booking.py` (only if a narrow synchronization seam is required).

**Acceptance:**
- [ ] Start with capacity 10, sold 9 and valid purchase quantities totaling 9; two independent connections attempt one ticket through the real booking service.
- [ ] Bounded events/barriers coordinate the second lock attempt while the first holds the screening lock; no timing-only sleeps, unbounded joins or shared global connections. Fail and clean up workers on timeout.
- [ ] Assert exactly one success, one capacity failure, final sold 10, one new purchase and no losing purchase; check purchase/counter reconciliation and no leaked transaction from a fresh connection.

**Verification:** `python -m pytest tests/concurrency/test_last_seat.py -q`; reviewer inspects synchronization evidence to confirm actual overlap rather than two serial purchases.

**T17 evidence:** T16 merged at `2326662`. RED: first worker did not pause
while holding the screening lock. GREEN: the existing clock callback pauses
the first worker after the lock, and the observer sees the second session's
locking SQL on MySQL before releasing the first. No production seam added.
Independent SQL confirms sold 10, purchase quantities 5+4+1, and no loser
purchase; a fresh session reacquires the screening and payment locks.
Focused: 1 passed; full suite: 249 passed on isolated MySQL. Ruff lint/format,
pip check, wheel build and whitespace passed. Checkpoint pending; user merges.
Implementation: `aa0c87d`; PR #62. Three checkpoint reviews launched.

**Review follow-up:** Bound worker and observer connector I/O at connection
creation. If a worker misses its join deadline, a separate test-only connection
terminates its session and the harness rejoins it, failing the test even when
cleanup succeeds. Fixture cleanup does not close an active worker's connection.
Confirmed same-account termination needs no new grants. Focused 1 and full 249
passed again, plus Ruff and whitespace. No runtime changes. Follow-up:
`394f487`. Checkpoint GO: correctness re-review cleared the timeout blocker;
the security and test reviews raised no other blockers. Optional: exercise
the forced-cleanup path end to end. User owns the merge after green CI.

## T18 — Show the client's captured purchase history
- [ ] **IN REVIEW · M · Owner D, E query integration · Reviewer A · Depends: T15 · SC3, SC6**

**Files:** `src/booking.py`, `src/client.py`, `tests/integration/test_history.py`, `queries.sql`.

**Acceptance:**
- [x] History CLI shows only the authenticated client's purchases, quantity, captured unit/total and screening details with deterministic time/ID ordering and an empty state.
- [x] Captured amounts remain unchanged if current price inputs change in a controlled test; a deactivated method retains historical references and masked display.
- [x] Q2 uses bound client filtering and multiple joins; unauthenticated/foreign-principal misuse and SQL-like input cannot expose another client's records.

**Verification:** `python -m pytest tests/integration/test_history.py -q`; manual buy → history → method deactivate → history via `python -m src.main`.

**T18 evidence:** T15 merged at `65d07c2`. RED: seven cases failed on missing
history service/Q2. GREEN: seven focused and 256 full-suite tests on isolated
MySQL. Live CLI buy → masked history → deactivate → unchanged history passed.
The Q2 artifact was executed with bound parameters and compared to the service.
Implementation: `3221072`; PR #63. Three checkpoint reviews launched.
Review follow-up: ordering now exercises conflicting timestamp/ID order and
tied timestamps; CLI assertions check exact owned IDs and a complete masked
receipt line. No runtime changes. Reverified 7 focused and 256 full tests,
plus Ruff lint/format. CI before user merge; no auto-merge.

## C06 — Transaction checkpoint
- [ ] **TODO · Owner D + all · Depends: C05, T16–T18**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; inspect rollback/last-seat evidence and explain why a search result is not an authoritative capacity check. Review failure cleanup and captured history together.

## T19 — Report revenue by movie
- [ ] **IN REVIEW · M · Owner E, C adapter integration · Reviewer C · Depends: T06, T08 · SC7, SC10**

**Files:** `src/analytics.py`, `src/admin.py`, `tests/integration/test_movie_revenue.py`, `tests/unit/test_cli_auth.py` (approved prompt update).

**Acceptance:**
- [x] Admin service/CLI returns movie ticket totals and captured revenue with deterministic tie-breaking and zero-sale movies included at the default threshold.
- [x] Bound minimum-tickets parameter defaults to zero and uses HAVING; invalid thresholds and client/nonprincipal direct calls fail.
- [x] Hand-calculated fixtures cover multiple screenings/purchases, zero sales and a nonzero threshold; totals cannot multiply through joins.

**Verification:** `python -m pytest tests/integration/test_movie_revenue.py -q`; manual administrator analytics path via `python -m src.main`.

**T19 evidence:** T06 and T08 are merged. RED: `src.analytics` missing.
The user approved updating the exact menu expectation in `test_cli_auth.py`;
all existing assertions were retained. GREEN: 22 focused and 266 full-suite
tests on isolated MySQL. Live administrator CLI, Ruff lint/format, dependency
check, wheel build, and whitespace passed. Implementation: `f4da3fb`.
Checkpoint and CI before user merge.

## T20 — Report revenue by theater
- [ ] **IN REVIEW · M · Owner E, C adapter integration · Reviewer C · Depends: T19 · SC7, SC10**

**Files:** `src/analytics.py`, `src/admin.py`, `tests/integration/test_theater_revenue.py`, `tests/unit/test_cli_auth.py` (approved prompt update).

**Acceptance:**
- [x] Admin service/CLI returns theater ticket totals and captured revenue, including zero-sale theaters with deterministic ordering and exact Decimal amounts.
- [x] Multiple screenings and purchases match hand-calculated totals without double counting; role and database-error behavior follow the existing report contract.
- [x] A committed additional purchase inserted by the controlled report fixture changes the totals exactly once; captured totals, not current pricing inputs, drive revenue. Live booking-service reconciliation is separately required at C07 and T25.

**Verification:** `python -m pytest tests/integration/test_theater_revenue.py -q`; manual report via `python -m src.main`. This task can fully pass without T15; C07 and T25 own the subsequent cross-service check.

**T20 evidence:** T19 merged at `93389f6`. RED on MySQL: missing
`revenue_by_theater`. The user approved updating the exact admin prompt test;
its assertions remain intact. GREEN: 18 focused tests and 272 full-suite tests
on isolated MySQL. Live admin CLI, Ruff lint/format, dependency check, wheel
build, and whitespace passed. Implementation: `0640ccd`. Checkpoint and CI
before user merge.

**PR #65 checkpoint:** Correctness and security reviews found no blockers.
The test review identified an ordering gap. The committed-purchase fixture
now makes revenue and ticket rankings disagree and leaves the screening
counter unchanged to verify the report counts purchases. No runtime changes.
Reverified: 18 focused and 272 full MySQL tests, Ruff, and whitespace.

## T21 — Report weighted occupancy by movie
- [ ] **IN REVIEW · M · Owner E, C adapter integration · Reviewer C · Depends: T20 · SC7, SC10**

**Files:** `src/analytics.py`, `src/admin.py`, `tests/integration/test_occupancy.py`, `tests/unit/test_cli_auth.py` (approved prompt update).

**Acceptance:**
- [x] Return sold tickets, offered seats and percentage across all scheduled screenings, pre-aggregating purchases per screening so capacities are counted once.
- [x] Distinct-capacity/multi-purchase fixtures prove weighted occupancy rather than average percentages; zero-sale screenings yield zero and movies with no screenings yield N/A.
- [x] Admin-only CLI formats results consistently and ordering is deterministic; no division-by-zero or float-money substitutions.

**T21 evidence:** T20 merged at `f1f67f8`. Approved exact menu prompt update
retains the existing assertions. RED: five cases failed on missing
`occupancy_by_movie`. GREEN: 17 focused and 277 full-suite MySQL tests.
Live admin CLI, Ruff lint/format, dependency check, wheel build and whitespace
passed. Implementation: `e028268`. Checkpoint and CI before user merge.

**PR #66 checkpoint:** Correctness and security found no blockers. Test
follow-up distinguishes ID ordering from title ordering and checks integer
counts. Five focused MySQL tests, Ruff, and whitespace passed; no runtime
changes. Equal-capacity fixture and CLI error-path coverage are optional.

**Verification:** `python -m pytest tests/integration/test_occupancy.py -q`; manually compare displayed results to the fixture arithmetic via `python -m src.main`.

## C07 — Analytics checkpoint
- [ ] **TODO · Owner E + all · Depends: C06, T19–T21**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; make a purchase and independently reconcile all three reports, capacity and history. Resolve any arithmetic discrepancy before expanding the query artifact.

## T22 — Prove concurrent schedule creation cannot overlap
- [ ] **IN REVIEW · S · Owner C · Reviewer D · Depends: T13 · SC7, SC11**

**Files:** `tests/concurrency/test_schedule_race.py`, `src/screenings.py` (only necessary race fixes/seams).

**Acceptance:**
- [x] Independent transactions contend for one theater with overlapping proposed intervals; synchronization proves overlap in execution and exactly one screening is stored.
- [x] Back-to-back intervals both succeed, and different theaters do not cause false overlap rejection; tests expose stale-snapshot behavior under REPEATABLE READ.
- [x] Bounded waits and cleanup prevent hangs; a failed contender releases its resources and a later valid creation succeeds.

**Verification:** `python -m pytest tests/concurrency/test_schedule_race.py -q`; review theater-lock acquisition and current-read ordering against SPEC P11.

**T22 evidence:** T13 is merged (`d28b51d`). RED negative control: removing
the overlap current read in memory let both overlapping requests succeed.
GREEN with unchanged production code: 3 focused and 280 full MySQL tests.
Ruff lint/format, dependency check, wheel build, and whitespace passed.
Implementation: `2e6622f`. Checkpoint and CI before user merge.

## T23 — Prove booking/payment deactivation ordering
- [ ] **TODO · M · Owner B + D · Reviewer E · Depends: T10, T15 · SC6, SC8, SC11**

**Files:** `tests/concurrency/test_payment_race.py`, `src/payments.py`, `src/booking.py` (only necessary race fixes/seams).

**Acceptance:**
- [ ] With independent connections and bounded synchronization, booking obtaining the payment lock first commits before deactivation; the purchase reference survives.
- [ ] Deactivation obtaining the payment lock first causes the waiting booking to reject the inactive method, leaving no purchase/counter change.
- [ ] Lock order remains screening→payment for booking; foreign ownership remains rejected and both orderings clean up workers/transactions on failure.

**Verification:** `python -m pytest tests/concurrency/test_payment_race.py -q` plus the affected payment/booking integration files after any service fix.

## T24 — Complete and execute the five-query submission artifact
- [ ] **TODO · M · Owner E · Reviewer C · Depends: T11, T18, T21 · SC3, SC10**

**Files:** `queries.sql`, `tests/integration/test_queries.py`, `docs/queries.md`.

**Acceptance:**
- [ ] Exactly Q1–Q5 implement search, client history, movie revenue with HAVING, theater revenue, and occupancy with screening-grain subquery/pre-aggregation; document required SQL concepts and deterministic ordering.
- [ ] Document connector-style parameter names/order, types and execution procedure; execute the artifact's actual statements using bound values, not by unconditional shell import or unrelated copies.
- [ ] Tests compare artifact results against application services and independent expected fixture values, including filters, nonzero threshold, zero sales, no screenings and multiple purchases per screening.

**Verification:** `python -m pytest tests/integration/test_queries.py -q`; reviewer checks the five-query coverage matrix against SPEC §6 and assignment PDF Step 4.

## C08 — Shared-invariant/query checkpoint
- [ ] **TODO · Owner A + all · Depends: C07, T22–T24**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; inspect evidence for both payment lock orderings, conflicting schedule creation and all five SQL statements. Any service/schema changes trigger affected-owner contract review.

## T25 — Verify every required CLI journey end to end
- [ ] **TODO · M · Owner B/C/D coordinated · Reviewer E · Depends: T10, T14, T17, T18, T21–T24 · SC4–SC8, SC10–SC11**

**Files:** `tests/integration/test_cli_flows.py`, `src/main.py`, `src/client.py`, `src/admin.py` (adapters only).

**Acceptance:**
- [ ] Script real service/MySQL-backed CLI journeys for all five client and all five administrator entries; menu choices dispatch correctly and exit/input recovery are usable.
- [ ] Verify invalid login/payment/quantity/schedule, insufficient capacity, role/ownership denial and database failures produce clear distinct messages without leaked transactions or business logic duplicated in menus.
- [ ] One purchase changes history, search availability, admin capacity and all relevant reports consistently; failed purchases change none. Include booking after deactivation rejection and retained history.

**Verification:** `python -m pytest tests/integration/test_cli_flows.py -q`; manual `python -m src.main` walkthrough for both roles with malformed input, EOF and recovery. Split newly discovered service defects into bounded follow-ups rather than expanding this adapter task.

## T26 — Provide a repeatable two-connection demonstration
- [ ] **TODO · M · Owner D · Reviewer A · Depends: T17 · SC9, SC13**

**Files:** `src/demo_concurrency.py`, `docs/demo-script.md`, `tests/integration/test_demo.py`.

**Acceptance:**
- [ ] `python -m src.demo_concurrency` uses the isolated test target and existing real booking path to demonstrate capacity 10/sold 9, two independent connections, one success/one capacity failure and final 10 with reconciled history.
- [ ] Demo refuses a development target before reset, uses bounded synchronization, returns failure if the invariant is violated, and cleans up its workers/resources; it does not implement a separate purchase algorithm.
- [ ] Script explains lock acquisition/current reads/rollback and provides the full ER → setup/data → SQL → client/admin → booking → contention → analytics presentation order.

**Verification:** `python -m pytest tests/integration/test_demo.py -q`; `python -m src.demo_concurrency`; manual reviewer walkthrough of the output and explanation. The demo module/command is introduced by this task, not assumed to exist earlier.

## T27 — Assemble reproducible handover documentation
- [ ] **TODO · M · Owner E + all contributions · Reviewer C · Depends: T24–T26 · SC11–SC13**

**Files:** `README.md`, `docs/test-evidence.md`, `docs/contributions.md`, `docs/demo-script.md`.

**Acceptance:**
- [ ] README gives clean setup/schema/data/run/test instructions, local synthetic credentials, assumptions links, transaction/isolation explanation, parameterized query execution, normal shutdown and separately targeted reset guidance. Document fresh-project isolation and matching ports/environment for rehearsal.
- [ ] Evidence maps SC1–SC13 to actual commands/manual observations and reviewed artifacts, recording versions/results rather than predicted passes; each owner supplies their work and cross-review contribution.
- [ ] Demo script has repeatable date/fixture preparation and each student is assigned an explanation outside their primary lane.

**Verification:** Run `python -m pytest -q`, plan Ruff commands and `git diff --check`; execute the documented query/demo commands, manually compare every README command with actual metadata/service names and record results. Fresh installation itself is verified in T28.

## C09 — Mandatory functionality complete
- [ ] **TODO · Owner E + all · Depends: C08, T25–T27**

**Acceptance/verification:** Review complete test output recorded by T27 (repeat only after changes), all ten menu paths, query parity, three reports and all race/rollback evidence. Every implemented SC must link to evidence; remaining fresh-install, clarification and rehearsal work is isolated to T28–T30. No optional web work begins.

## T28 — Verify a fresh installation and artifact inventory
- [ ] **TODO · M · Owner A · Reviewer B · Depends: T27, C09 · SC1–SC3, SC11–SC13**

**Files:** `docs/test-evidence.md` (delivery/rehearsal record only).

**Acceptance:**
- [ ] From a fresh virtual environment and isolated fresh Compose project/volumes with nonconflicting configured ports, follow README exactly: install pinned dependencies, start services, load schema/data, run CLI/full suite/demo. Preserve the normal development environment. Record ER/source/SQL/docs inventory and ensure intentional artifacts are tracked and included.
- [ ] Record actual command results and versions with no required test skipped; distinguish fresh-install evidence from the earlier incremental suite results.
- [ ] Any defect becomes a new bounded TODO with focused retest; do not hide implementation repairs inside this verification-only task.

**Verification:** README fresh setup and schema/data commands; `python -m pip check`; `python -m pytest -q`; both plan Ruff commands; `python -m src.main`; `python -m src.demo_concurrency`; `git diff --check`; `git ls-files` plus final artifact inventory/manual PDF opening.

## T29 — Close submission administration
- [ ] **TODO · S · Owner B + E · Reviewer A · Depends: T01, T08, T27 · SC12**

**Files:** `docs/test-evidence.md`, `docs/contributions.md`.

**Acceptance:**
- [ ] Ensure submission documents use named ownership from `assignments.md`, reviewed contributions and the confirmed 23 November 2026 submission date.
- [ ] Each student confirms their contribution record.

**Verification:** `git diff --check`; manual review of submission details and the contribution record with all five students.

## T30 — Rehearse the full-team presentation
- [ ] **TODO · S · Owner all, E coordinates · Reviewer A · Depends: T26, T27 · SC13**

**Files:** `docs/demo-script.md`, `docs/test-evidence.md`.

**Acceptance:**
- [ ] All five students run the presentation sequence covering ER, fresh setup/data explanation, representative SQL, both roles, booking, concurrency and all three analytics.
- [ ] Each student explains a module outside their primary lane and can explain the ER model, a nontrivial query and why screening locks/atomic writes prevent overselling; record participants and unresolved explanation gaps.
- [ ] Demonstration failures or knowledge gaps receive named follow-ups and a repeat of the affected segment before this task passes; full implementation repairs remain separate tasks.

**Verification:** Execute `docs/demo-script.md`, `python -m src.main`, and `python -m src.demo_concurrency` on a prepared isolated demonstration target; record manual review of every segment and all five participants. Coordinate with E so the demo cannot reset T28's active test target.

## C10 — Mandatory delivery gate
- [ ] **TODO · Owner all · Depends: C09, T28–T30**

**Acceptance/verification:** Review T28's actual clean-install evidence, T29's submission closure, T30's five-person rehearsal and complete SC1–SC13 mapping; check no unresolved mandatory TODO/failed test remains. Preserve a known-good mandatory delivery. Optional Flask work requires separate explicit approval and its own task breakdown.
