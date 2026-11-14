# Implementation ledger — Movie Ticketing System

**Execution order:** follow [parallel readiness and handoffs](parallel-work.md),
not task-number order. Each owner can start a task once its prerequisites are
verified and merged. Keep one active task per person and reserve shared-file edits.
Task and checkpoint acceptance criteria remain binding.

**Ownership authority:** [Named assignments](assignments.md) supersede provisional
A–E owner/reviewer/coordination references below. Bianca handles the T01/T29
instructor request; Eleonora coordinates isolated verification runs.

Source: approved `plan/SPEC.md` and `plan/ROADMAP.md`; execution conventions and command prerequisites: `tasks/plan.md`.

GitHub tracking: [issue index](github-issues.md) maps every task/checkpoint to its published issue. Keep issue and ledger completion states aligned.

Every task/checkpoint is TODO. Acceptance checkboxes are not claims of completion. Dependencies below are task IDs; checkpoints additionally verify the delivered prefix in the default order. Each task includes implementation plus meaningful feature verification, with at most five substantive files. Reviewers follow the plan's ownership table. Each feature owner provides review evidence and contribution notes as work lands.

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
- [ ] **IN REVIEW · M · Owner Eleonora · Reviewer Tommaso · Depends: T01 · SC2, SC12**

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

## T03 — Make connections and isolated database tests usable
- [ ] **TODO · M · Owner A, E fixture review · Reviewer B · Depends: T02 · SC2, SC8**

**Files:** `src/database.py`, `tests/conftest.py`, `tests/integration/test_database.py`.

**Acceptance:**
- [ ] Connection factory uses explicit dev/test settings, separate connections, documented closing responsibility, and no hidden commit for caller-owned work; actual isolation is checked as REPEATABLE READ.
- [ ] Test reset validates the complete configured target before destructive operations, refuses development identity/unsafe settings, and uses an account unable to modify development data. Missing MySQL fails required integration runs rather than silently skipping them.
- [ ] Unseeded connection fixtures work now; later schema/seed fixtures have explicit opt-in lifecycle and reset only the test database. Verify connection independence, transaction rollback, resource cleanup and target refusal with a disposable probe table.

**Verification:** `python -m pytest tests/integration/test_database.py -q`; Ruff on these three files. Guard tests must demonstrate no destructive statement was issued for a rejected target; use fake settings/call capture for that negative case, not a destructive experiment on development data.

## C01 — Runtime checkpoint
- [ ] **TODO · Owner A + all · Depends: T01–T03**

**Acceptance/verification:** Review contracts; run `python -m pip check`, `docker compose --profile test config --quiet`, `python -m pytest -q`, both plan Ruff commands and `git diff --check`. Confirm independent healthy services and tracked design documents. Record pins and results.

## T04 — Deliver ER model and enforceable relational schema
- [ ] **TODO · M · Owner A · Reviewer B · Depends: T03 · SC1, SC2**

**Files:** `schema.sql`, `docs/er-model-source.drawio`, `ER_diagram.pdf`, `tests/integration/test_schema.py`.

**Acceptance:**
- [ ] ER source/PDF captures all SPEC §5 attributes, identifiers, relationships, cardinalities and mandatory participation, including user/client distinction and movie languages/genres; all five review its correspondence to T01.
- [ ] Clean schema load creates InnoDB tables, keys, relationship uniqueness, local positive/nonnegative checks and useful search/history indexes; unsupported cross-row rules are assigned to services, not falsely claimed as CHECK guarantees.
- [ ] Real MySQL tests reject duplicate emails, invalid local numeric values, missing foreign keys and invalid movie-language associations; retained purchase references prevent destructive payment deletion. Document minimum-child rules that require seed/service validation.

**Verification:** Plan's clean `schema.sql` load command on the empty dev database; `python -m pytest tests/integration/test_schema.py -q`; manually open `ER_diagram.pdf` and compare every entity and constraint to the approved contract.

## T05 — Implement the authoritative ticket price
- [ ] **TODO · S · Owner C · Reviewer D · Depends: T01, T02 · SC5, SC8**

**Files:** `src/pricing.py`, `tests/unit/test_pricing.py`.

**Acceptance:**
- [ ] Decimal pricing produces EUR 15/20/18/23 and discounted 12/16/14.40/18.40, applying discount after all theater surcharges and final two-decimal rounding.
- [ ] Calendar-year boundary tests cover exactly two years, day before/after, and Feb 29 → Feb 28 anniversary; no dependence on wall-clock test execution date.
- [ ] One typed service contract is usable by search and booking without display logic or duplicated formulas.

**Verification:** `python -m pytest tests/unit/test_pricing.py -q` and focused Ruff.

## T06 — Populate coherent, reproducible movie data
- [ ] **TODO · M · Owner E · Reviewer C · Depends: T04, T05 · SC2, SC10**

**Files:** `data.sql`, `tests/integration/test_seed.py`, `docs/fixtures.md`, `tests/conftest.py`.

**Acceptance:**
- [ ] Seed 6–8 movies, 2–3 theaters, 6–8 clients plus admin, multiple synthetic methods/languages/genres, 12–15 screenings and purchases. Seed documented salted scrypt credentials with recorded parameters compatible with T01, not plaintext database passwords.
- [ ] Original/available languages and genres meet minimum cardinalities; schedules respect rules; purchase totals/counters reconcile, including zero/partial/full and capacity-10/sold-9 cases, foreign and inactive methods. With only 2–3 demo theaters, supply a fourth capability combination in focused test fixtures to cover all eight prices.
- [ ] Fixtures control dates and offer a repeatable relative-date demo seed policy; expose known report expectations including multiple purchases per screening, different capacities, and movies without screenings.

**Verification:** Plan's clean `data.sql` load after schema; `python -m pytest tests/integration/test_seed.py -q`; manually reconcile fixture quantities and captured totals with the fixture document.

## C02 — Foundation freeze
- [ ] **TODO · Owner A + all · Depends: C01, T04–T06**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; verify clean schema/data loads and ER review. All lanes sign the first schema/service/fixture contract revision; changes thereafter require affected-owner review. Confirm exact dependency/image versions and timezone.

## T07 — Authenticate preloaded users and enforce stored roles
- [ ] **TODO · S · Owner B · Reviewer E · Depends: T04 · SC4, SC11**

**Files:** `src/auth.py`, `tests/integration/test_auth.py`.

**Acceptance:**
- [ ] Authentication trims/normalizes email, verifies the approved scrypt hash format, and returns a verified principal with the database role; invalid credentials fail consistently and inputs are bound parameters.
- [ ] Direct role checks deny missing/invalid principals, clients calling administrator operations, and inappropriate admin-as-client requests according to the frozen contract; no interface-supplied role is accepted as authority.
- [ ] Tests cover normalization/uniqueness, invalid password/email, malformed stored hashes and connection failure cleanup; service APIs neither prompt nor print secrets.

**Verification:** `python -m pytest tests/integration/test_auth.py -q` with task-local accounts inserted into the isolated schema fixture; do not require T06's demo seed. C03 checks the shipped demo credentials separately.

## T08 — Open authenticated CLI sessions with role dispatch
- [ ] **TODO · M · Owner B, D/C adapter coordination · Reviewer E · Depends: T07 · SC4, SC6, SC7, SC14**

**Files:** `src/main.py`, `src/client.py`, `src/admin.py`, `tests/unit/test_cli_auth.py`.

**Acceptance:**
- [ ] `python -m src.main` asks for email/password, routes using the authenticated principal, and supports exit/EOF; invalid login/input/database errors return understandable outcomes without tracebacks or open resources.
- [ ] Establish thin client/admin adapter entry points for incremental feature handlers; unavailable functions are not presented as working. Preserve the root greeting scaffold and document the canonical module entry point in the later README.
- [ ] Place the SPEC §12 URL as a Python comment immediately after imports in `src/main.py`, without fetching/executing it; retain instructor-placement clarification as a final delivery follow-up.

**Verification:** `python -m pytest tests/unit/test_cli_auth.py -q` covering client/admin dispatch, invalid credentials, exit and EOF using service fakes; real auth is verified by T07. Seeded live CLI login is a C03 integration obligation, not a prerequisite for completing T08.

## T09 — Let clients list and add their payment methods
- [ ] **TODO · M · Owner B, D integrates adapter · Reviewer E · Depends: T06, T08 · SC6, SC11**

**Files:** `src/payments.py`, `src/client.py`, `tests/unit/test_payment_validation.py`, `tests/integration/test_payments.py`.

**Acceptance:**
- [ ] CLI management lists only the authenticated client's methods, masks numbers and shows active state; add accepts approved synthetic credit/debit fields and required billing address.
- [ ] Service-boundary tests reject malformed fields, unauthenticated/inappropriate principals and foreign-owner access; supplied SQL-like text cannot change query structure.
- [ ] Provide transaction-compatible payment lookup/validation on the caller's connection, with no implicit commit, so booking can lock and revalidate ownership/activity.

**Verification:** `python -m pytest tests/unit/test_payment_validation.py tests/integration/test_payments.py -q`; manual `python -m src.main` → client → payment management → add/list and invalid-input recovery.

## C03 — First client flow checkpoint
- [ ] **TODO · Owner B + all · Depends: C02, T07–T09**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; use `python -m src.main` to verify T06's documented client/admin credentials, invalid credentials, exit/EOF, role dispatch → add/list owned method and client rejection at an admin service boundary/role guard.

## T10 — Deactivate methods without losing purchase references
- [ ] **TODO · M · Owner B, D integrates adapter · Reviewer E · Depends: T09 · SC6, SC8**

**Files:** `src/payments.py`, `src/client.py`, `tests/integration/test_payments.py`.

**Acceptance:**
- [ ] Owner can deactivate through CLI; state change is irreversible within the initial scope and preserves existing purchase references. Repeated deactivation has a documented consistent outcome.
- [ ] The service locks the payment row while checking ownership and changing state; inactive or foreign methods fail purchase validation on a caller-owned transaction.
- [ ] Validation/database failures roll back and release connections/locks; history references and method visibility remain intact.

**Verification:** `python -m pytest tests/integration/test_payments.py -q`; manual deactivation path via `python -m src.main`, checking an existing seeded purchase reference still exists.

## T11 — Search screenings from the client menu
- [ ] **TODO · M · Owner C, D adapter / E query integration · Reviewer D · Depends: T05, T06, T08 · SC3, SC5, SC6**

**Files:** `src/screenings.py`, `src/client.py`, `tests/integration/test_search.py`, `queries.sql`.

**Acceptance:**
- [ ] Combined title-substring, exact genre/language/date and inclusive optional time-range filters use AND and bound parameters; invalid ranges are rejected and genre joins cannot duplicate screenings.
- [ ] Results ordered by start then ID contain movie/theater/date/time/language, authoritative unit price, advisory available seats and both capability flags; display and empty-result behavior work in CLI.
- [ ] Add Q1 to the query artifact and supply transaction-compatible authoritative screening lookup for booking without committing its connection.

**Verification:** `python -m pytest tests/integration/test_search.py -q`; manual combined search and no-results path using `python -m src.main`; inspect representative bound-parameter execution against MySQL.

## T12 — Specify valid screening intervals in executable rules
- [ ] **TODO · S · Owner C · Reviewer D · Depends: T01, T02 · SC7**

**Files:** `src/schedule_rules.py`, `tests/unit/test_schedule_rules.py`.

**Acceptance:**
- [ ] Minute-resolution runtime fits the same local date between 10:00 and 23:59 inclusive at boundaries; reject before-open, too-late and date-crossing intervals.
- [ ] Half-open overlap rejects intersecting intervals and permits exact back-to-back screenings; cover equal starts, contained intervals, adjacent dates and exact close.
- [ ] Pure rules use the frozen timezone/clock convention and explicit types, shared with scheduling rather than copied into the menu.

**Verification:** `python -m pytest tests/unit/test_schedule_rules.py -q` and focused Ruff.

## C04 — Discovery/payment checkpoint
- [ ] **TODO · Owner C + all · Depends: C03, T10–T12**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; demonstrate price/filter results, invalid ranges, and irreversible method deactivation with preserved references.

## T13 — Create a valid screening from the administrator menu
- [ ] **TODO · M · Owner C · Reviewer D · Depends: T06, T08, T12 · SC7, SC11**

**Files:** `src/screenings.py`, `src/admin.py`, `tests/integration/test_scheduling.py`.

**Acceptance:**
- [ ] Authorized administrator can select existing movie/theater, allowed language and valid interval; missing entities, invalid language/time and overlaps fail with no inserted row.
- [ ] Transaction acquires theater lock before checking/inserting; overlap uses a current/locking read so a preexisting snapshot cannot hide a just-committed competitor. Failure rolls back and closes resources.
- [ ] Direct service calls by clients fail; CLI validates input and presents service errors without SQL or business logic in the adapter.

**Verification:** `python -m pytest tests/integration/test_scheduling.py -q`; manual valid, back-to-back and rejected overlap creation via `python -m src.main`.

## T14 — Show schedule and remaining capacity to administrators
- [ ] **TODO · M · Owner C · Reviewer D · Depends: T13 · SC7**

**Files:** `src/screenings.py`, `src/admin.py`, `tests/integration/test_schedule_views.py`.

**Acceptance:**
- [ ] Both required menu paths show deterministic schedule ordering and capacity minus sold count, with full/partial/empty cases and relevant movie/theater/time identifiers.
- [ ] Views enforce administrator authorization at service entry and handle empty results/database errors through the common error contract.
- [ ] Tests demonstrate capacity against known sold/capacity fixtures and newly created screenings; displayed capacity is explicitly advisory for booking. Cross-feature search comparison is owned by C05.

**Verification:** `python -m pytest tests/integration/test_schedule_views.py -q`; manual both admin views via `python -m src.main`.

## T15 — Buy multiple tickets atomically through the CLI
- [ ] **TODO · M · Owner D · Reviewer A · Depends: T05, T06, T09, T10, T11 · SC6, SC8, SC11**

**Files:** `src/booking.py`, `src/client.py`, `tests/integration/test_booking.py`, `tests/unit/test_booking_validation.py`.

**Acceptance:**
- [ ] Authenticated client submits screening/quantity/method; reject zero, negative, noninteger (including boolean) quantities and already-started screenings using the controlled cinema clock. No prompt occurs inside a transaction.
- [ ] One transaction locks screening then payment, reads current capacity, revalidates owner/active method, computes Decimal price internally, inserts captured unit/total and increases sold count, committing only both together.
- [ ] Real MySQL cases verify multi-ticket success and persisted totals/counter, missing IDs, foreign/inactive methods and insufficient capacity with no partial state; CLI displays structured purchase confirmation or understandable failure.

**Verification:** `python -m pytest tests/unit/test_booking_validation.py tests/integration/test_booking.py -q`; manual `python -m src.main` purchase and persisted confirmation, using independent SQL reads in the integration tests to verify counter/amounts. The admin capacity comparison belongs to C05. No interface amount/role/availability may override database facts.

## C05 — First-purchase checkpoint
- [ ] **TODO · Owner D + all · Depends: C04, T13–T15**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; cross-review the exact transaction lock/write/commit sequence and demonstrate schedule creation → search → multi-ticket purchase → changed capacity. Explicitly compare T11 search availability with T14 admin views before/after the T15 purchase. Do not claim concurrency proof until the relevant race tests pass.

## T16 — Prove rollback and lock release after failed writes
- [ ] **TODO · S · Owner D · Reviewer A · Depends: T15 · SC8, SC11**

**Files:** `src/booking.py`, `tests/integration/test_booking_failures.py`.

**Acceptance:**
- [ ] Inject failures after purchase insertion and separately after counter update but before commit; both leave purchase rows and sold counts unchanged, observed from a separate connection.
- [ ] Another connection can successfully book after each failure with bounded waits, proving transaction/lock cleanup; all cursors/connections are released on validation and database errors.
- [ ] Controlled real lock timeout plus injected connector deadlock/commit-error paths demonstrate rollback and a retryable error classification where applicable, without automatic retries or duplicate writes. Do not assert a known rollback after an indeterminate lost commit acknowledgement; distinguish that database failure.

**Verification:** `python -m pytest tests/integration/test_booking_failures.py -q`; review injection seams for deterministic tests and absence of user-facing failure switches.

## T17 — Prove the exact last-seat contention outcome
- [ ] **TODO · S · Owner D · Reviewer A · Depends: T16 · SC9, SC11**

**Files:** `tests/concurrency/test_last_seat.py`, `src/booking.py` (only if a narrow synchronization seam is required).

**Acceptance:**
- [ ] Start with capacity 10, sold 9 and valid purchase quantities totaling 9; two independent connections attempt one ticket through the real booking service.
- [ ] Bounded events/barriers coordinate the second lock attempt while the first holds the screening lock; no timing-only sleeps, unbounded joins or shared global connections. Fail and clean up workers on timeout.
- [ ] Assert exactly one success, one capacity failure, final sold 10, one new purchase and no losing purchase; check purchase/counter reconciliation and no leaked transaction from a fresh connection.

**Verification:** `python -m pytest tests/concurrency/test_last_seat.py -q`; reviewer inspects synchronization evidence to confirm actual overlap rather than two serial purchases.

## T18 — Show the client's captured purchase history
- [ ] **TODO · M · Owner D, E query integration · Reviewer A · Depends: T15 · SC3, SC6**

**Files:** `src/booking.py`, `src/client.py`, `tests/integration/test_history.py`, `queries.sql`.

**Acceptance:**
- [ ] History CLI shows only the authenticated client's purchases, quantity, captured unit/total and screening details with deterministic time/ID ordering and an empty state.
- [ ] Captured amounts remain unchanged if current price inputs change in a controlled test; a deactivated method retains historical references and masked display.
- [ ] Q2 uses bound client filtering and multiple joins; unauthenticated/foreign-principal misuse and SQL-like input cannot expose another client's records.

**Verification:** `python -m pytest tests/integration/test_history.py -q`; manual buy → history → method deactivate → history via `python -m src.main`.

## C06 — Transaction checkpoint
- [ ] **TODO · Owner D + all · Depends: C05, T16–T18**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; inspect rollback/last-seat evidence and explain why a search result is not an authoritative capacity check. Review failure cleanup and captured history together.

## T19 — Report revenue by movie
- [ ] **TODO · M · Owner E, C adapter integration · Reviewer C · Depends: T06, T08 · SC7, SC10**

**Files:** `src/analytics.py`, `src/admin.py`, `tests/integration/test_movie_revenue.py`.

**Acceptance:**
- [ ] Admin service/CLI returns movie ticket totals and captured revenue with deterministic tie-breaking and zero-sale movies included at the default threshold.
- [ ] Bound minimum-tickets parameter defaults to zero and uses HAVING; invalid thresholds and client/nonprincipal direct calls fail.
- [ ] Hand-calculated fixtures cover multiple screenings/purchases, zero sales and a nonzero threshold; totals cannot multiply through joins.

**Verification:** `python -m pytest tests/integration/test_movie_revenue.py -q`; manual administrator analytics path via `python -m src.main`.

## T20 — Report revenue by theater
- [ ] **TODO · M · Owner E, C adapter integration · Reviewer C · Depends: T19 · SC7, SC10**

**Files:** `src/analytics.py`, `src/admin.py`, `tests/integration/test_theater_revenue.py`.

**Acceptance:**
- [ ] Admin service/CLI returns theater ticket totals and captured revenue, including zero-sale theaters with deterministic ordering and exact Decimal amounts.
- [ ] Multiple screenings and purchases match hand-calculated totals without double counting; role and database-error behavior follow the existing report contract.
- [ ] A committed additional purchase inserted by the controlled report fixture changes the totals exactly once; captured totals, not current pricing inputs, drive revenue. Live booking-service reconciliation is separately required at C07 and T25.

**Verification:** `python -m pytest tests/integration/test_theater_revenue.py -q`; manual report via `python -m src.main`. This task can fully pass without T15; C07 and T25 own the subsequent cross-service check.

## T21 — Report weighted occupancy by movie
- [ ] **TODO · M · Owner E, C adapter integration · Reviewer C · Depends: T20 · SC7, SC10**

**Files:** `src/analytics.py`, `src/admin.py`, `tests/integration/test_occupancy.py`.

**Acceptance:**
- [ ] Return sold tickets, offered seats and percentage across all scheduled screenings, pre-aggregating purchases per screening so capacities are counted once.
- [ ] Distinct-capacity/multi-purchase fixtures prove weighted occupancy rather than average percentages; zero-sale screenings yield zero and movies with no screenings yield N/A.
- [ ] Admin-only CLI formats results consistently and ordering is deterministic; no division-by-zero or float-money substitutions.

**Verification:** `python -m pytest tests/integration/test_occupancy.py -q`; manually compare displayed results to the fixture arithmetic via `python -m src.main`.

## C07 — Analytics checkpoint
- [ ] **TODO · Owner E + all · Depends: C06, T19–T21**

**Acceptance/verification:** `python -m pytest -q`, plan Ruff commands, `git diff --check`; make a purchase and independently reconcile all three reports, capacity and history. Resolve any arithmetic discrepancy before expanding the query artifact.

## T22 — Prove concurrent schedule creation cannot overlap
- [ ] **TODO · S · Owner C · Reviewer D · Depends: T13 · SC7, SC11**

**Files:** `tests/concurrency/test_schedule_race.py`, `src/screenings.py` (only necessary race fixes/seams).

**Acceptance:**
- [ ] Independent transactions contend for one theater with overlapping proposed intervals; synchronization proves overlap in execution and exactly one screening is stored.
- [ ] Back-to-back intervals both succeed, and different theaters do not cause false overlap rejection; tests expose stale-snapshot behavior under REPEATABLE READ.
- [ ] Bounded waits and cleanup prevent hangs; a failed contender releases its resources and a later valid creation succeeds.

**Verification:** `python -m pytest tests/concurrency/test_schedule_race.py -q`; review theater-lock acquisition and current-read ordering against SPEC P11.

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
- [ ] Evidence maps SC1–SC14 to actual commands/manual observations and reviewed artifacts, recording versions/results rather than predicted passes; each owner supplies their work and cross-review contribution.
- [ ] Demo script has repeatable date/fixture preparation and each student is assigned an explanation outside their primary lane; instructor comment clarification remains visible until resolved in T29.

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

## T29 — Close instructor clarification and submission administration
- [ ] **TODO · S · Owner B + E · Reviewer A · Depends: T01, T08, T27 · SC12, SC14**

**Files:** `docs/test-evidence.md`, `docs/contributions.md`.

**Acceptance:**
- [ ] Record the instructor response to B's T01 request confirming the post-import comment placement (or explicitly confirmed omission). If placement changes require code edits, add a bounded follow-up task and verify it before this task passes; do not treat a pending response as approval.
- [ ] Replace provisional ownership with actual student names and reviewed contributions, and record the actual submission date if known. An unknown date stays explicitly unknown rather than becoming an invented software requirement.
- [ ] Each student confirms their contribution record; the SC14 entry links to the confirmed outcome and matching delivered artifact.

**Verification:** `git diff --check`; manual review of instructor confirmation against `src/main.py` and the contribution record with all five students. Technical tasks T28/T30 can proceed while clarification is pending; C10 cannot.

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

**Acceptance/verification:** Review T28's actual clean-install evidence, T29's instructor/submission closure, T30's five-person rehearsal and complete SC1–SC14 mapping; check no unresolved mandatory TODO/failed test remains. Preserve a known-good mandatory delivery. Optional Flask work requires separate explicit approval and its own task breakdown.
