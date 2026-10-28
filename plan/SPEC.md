# Specification — Movie Ticketing System

**Status:** Draft for explicit approval; implementation is not authorized.
**Team:** Five students; provisional owners A–E, names to be assigned.
**Source:** Project A — Movie Ticketing System, groups of 3–5, supplied PDF text (`docs/Groups_3_5_Cinema.pdf`).
**Target:** 23 November 2026, tentative and unconfirmed. Phases are dependency-based, not time estimates.

## 1. Objective

Deliver an explainable MySQL database and Python application for one cinema: authentication, movie scheduling, ticket sales, payment-method management, reporting, and correct concurrent booking. The required interface is a CLI. A minimal web interface is an optional extension after the required deliverables pass verification.

Every student must be able to explain or modify the ER model, SQL, application code, and transaction logic. Parallel ownership must not become isolated knowledge ownership.

## 2. Confirmed decisions and proposals

### Confirmed in the interview

- MySQL runs through Docker Compose.
- Python CLI is mandatory; a simple Flask interface is optional and reuses application logic.
- Client and administrator accounts are preloaded; no registration feature is required.
- Roles are stored in MySQL and retrieved during authentication.
- Use `mysql-connector-python`, explicit SQL, and parameterized user input; no ORM.
- Payment methods support listing, adding, and deactivation. Historical purchases retain their payment-method references.
- All card details are synthetic; no real payment processing.
- Required analytics: revenue by movie, revenue by theater, and occupancy by movie.
- Use pytest and a separate MySQL test database, including two-connection concurrency tests.
- The module map below is approved. Organize work to maximize parallel progress across five students.

### Proposed assumptions — approval required

These are design proposals, not previously confirmed decisions. Approval of this specification accepts them unless explicitly amended.

| ID | Proposal |
|---|---|
| P1 | Retain Python 3.13, as declared in the existing project configuration. Use MySQL 8.4 LTS with InnoDB; select and pin exact compatible dependency/image versions at the foundation checkpoint. |
| P2 | Run Python on each developer's machine; Compose provides a development MySQL service and an isolated test MySQL service. Use a virtual environment, pip, and `.env` configuration. |
| P3 | Passwords are salted hashes, never plaintext. Use standard-library scrypt with recorded parameters; seed only documented fictional demo credentials. |
| P4 | One cinema, one agreed local timezone, minute-resolution scheduling, integer movie runtimes in minutes. No seat assignment, cancellation, refunds, external payment gateway, or movie/theater editing interface. |
| P5 | Screenings use half-open time intervals: back-to-back screenings are valid, with no cleaning interval. A screening may start at 10:00 and must finish by 23:59 on the same local date. |
| P6 | The age discount uses calendar years, not 730 days. Exactly two years old is not discounted. For a 29 February release, its non-leap-year anniversary is 28 February. |
| P7 | A theater's 3D capability and enhanced-sound flag directly determine surcharges, as the assignment states; there is no separate screening-format flag. Apply the 20% discount after adding all surcharges. |
| P8 | Store money as exact decimals, round the final unit price to two decimal places, and store the unit price and total at purchase time. Reject nonpositive/noninteger ticket quantities and purchases for screenings that have already started. |
| P9 | Clients may only manage their own payment methods and buy using their own active method. Deactivation is irreversible in the initial scope; adding a new method is permitted. Mask card numbers in normal displays. |
| P10 | All three analytics initially include all scheduled screenings; zero-sale movies/theaters remain visible. Occupancy is total sold tickets divided by total offered seats, not an unweighted average of screening percentages. A movie without screenings has occupancy N/A. |
| P11 | Prevent concurrent schedule insertion conflicts by locking the theater row before checking and inserting screenings. Keep transaction ownership in the relevant application service. |

Unresolved policy questions and the source's unusual comment requirement are listed in section 12. No proposed policy should be treated as settled before review.

## 3. Tech stack

| Area | Choice | Status |
|---|---|---|
| Application | Python 3.13 | Existing configuration; retain proposed |
| Database | MySQL 8.4 LTS / InnoDB | MySQL confirmed; version/engine proposed |
| Database runtime | Docker Compose | Confirmed |
| Driver | `mysql-connector-python` | Confirmed |
| Queries | Explicit SQL with bound parameters | Confirmed |
| Tests | pytest, real isolated MySQL, independent connections | Confirmed |
| Environment | `venv`, pip, `python-dotenv` | Proposed |
| Formatting/lint | Ruff, configured in `pyproject.toml` | Proposed |
| Optional web | Flask and server-rendered HTML, minimal CSS | Flask extension confirmed; rendering approach proposed |

Record exact dependency versions in reproducible installation metadata during foundation work. Flask is an optional dependency; CLI installation must not require it. No frontend build tool is needed.

## 4. Approved capability map and module specifications

These are logical modules, not independently deployed services. Their scoped specifications are consolidated here to keep one reviewable project contract.

| Stable module ID | Objective and boundary | Depends on | Acceptance |
|---|---|---|---|
| `database` | ER model, schema, constraints, connection/configuration contract, synthetic data | — | An empty database can be created and populated reproducibly; relationships and invariants are documented. |
| `identity` | Authenticate preloaded users and enforce database-backed roles; no registration | `database` | Invalid login fails; client credentials cannot perform administrator operations. |
| `screenings` | Movie catalog reads, screening search, pricing, creation, schedule and capacity views | `database` | All requested search fields are returned; invalid language/time/overlap is rejected. |
| `payments` | List, add, deactivate and validate a client's synthetic payment methods | `identity` | Ownership and active-state checks hold; deactivation preserves purchase history. |
| `booking` | Atomic multi-ticket purchase and authenticated client's purchase history | `identity`, `screenings`, `payments` | Booking, rollback, and last-seat contention meet section 7. |
| `analytics` | The three approved administrator reports | `database` | SQL results match manually computed fixture totals and occupancy. |
| `interfaces` | Required CLI and optional Flask adapters; role dispatch, input/output, error presentation | All application modules | Required menu paths work end to end and use the same underlying services. |

Administrator operations in `screenings` and `analytics` receive an authenticated principal and enforce the administrator role at the application-service boundary. The interfaces obtain that principal from `identity`; module dependencies do not imply that hiding a menu is sufficient authorization.

### Contracts to freeze before parallel implementation

| Provider | Contract consumers can rely on |
|---|---|
| `database` | Final table/column names, keys, types, connection factory, named environment settings, and who closes each connection. No shared global connection. Helpers do not silently commit caller-owned transactions. |
| `identity` | A verified principal carrying user ID and stored role, plus a consistent authentication/authorization failure result. Clients cannot supply a role to elevate themselves. |
| `screenings` | Search result fields listed in section 6; one authoritative pricing rule; screening lookup usable inside a caller-owned transaction. Read-only displayed availability is advisory. |
| `payments` | Payment-method ID, owner, type, masked display, active state; purchase validation can run using the booking transaction's connection. |
| `booking` | Input: authenticated client, screening ID, positive quantity, payment-method ID. Success: purchase ID, quantity, captured unit price and total. Failure: no purchase and no sold-count change. |
| `analytics` | Named columns, numeric/decimal types, zero-sale handling, and deterministic ordering for each report. |
| `interfaces` | Distinguish validation, authentication, authorization, capacity, and database failures. Translate them into understandable messages without duplicating business rules. |

Freeze exact operation names and return shapes at the first integration checkpoint. Contract-first work enables parallel development; database correctness must still be verified against real MySQL.

## 5. Data and ER design requirements

The PDF does not prescribe tables. The following is a proposed relational direction, to be validated by a jointly reviewed ER diagram rather than treated as a finished schema.

| Concept | Required information / proposed representation |
|---|---|
| User | Unique email, password hash, stored client/admin role; clients additionally require name and address. Proposed common user table plus client-profile table. |
| Payment method | Owner client, payment type, synthetic card number, billing address where relevant, active state. Purchases reference retained methods. |
| Theater | Unique ID, maximum occupancy, 3D and enhanced-sound flags. |
| Movie | Title, release date, runtime, original language, description. |
| Languages and genres | Language and genre tables, movie-language and movie-genre associations; every movie has at least one available language and one genre. Proposed: original language also appears among available languages. |
| Screening | Movie, theater, start date/time, chosen language, stored sold-ticket count. Chosen language must belong to that movie's available languages. |
| Purchase | Client, screening, positive ticket quantity, total amount, payment method; proposed captured unit price and purchase timestamp. |

ER deliverable: entities, attributes, identifiers, relationships, cardinalities, and optional/mandatory participation, plus explicit assumptions. Cover minimum child cardinalities that cannot be enforced by a simple foreign key.

`schema.sql` must run against an empty, already-created MySQL database and create all tables, primary/foreign keys, constraints, and useful indexes. Use database constraints for local invariants and relationships; use transactional application rules for cross-row capacity, schedule overlap, and ownership checks where appropriate. Document the enforcement location of each rule. Unsupported direct SQL writes are outside the application boundary.

Proposed constraints/indexes include unique email, positive capacity/runtime/quantity, nonnegative sold counts and amounts, relationship uniqueness, movie-language integrity, screening lookup by theater/start time, purchase lookup by client/time, and indexes supporting actual search/report queries. Do not claim a local `CHECK` alone enforces capacity against another table.

Synthetic data target: 6–8 movies, 2–3 theaters, 6–8 clients plus at least one administrator, multiple payment methods, 12–15 screenings, several purchases, multiple languages and genres. Include every price combination, discount boundaries, zero/partial/full occupancy, inactive and foreign-owned payment methods, and the capacity-10/sold-9 fixture. Seeded purchases and sold counters must reconcile.

## 6. Functional requirements

### Authentication and interfaces

- Login asks for email and password, validates credentials, and reads the role from MySQL.
- Client menu: search screenings; buy tickets; view previous purchases; manage payment methods; exit.
- Administrator menu: add screening; view schedule; view remaining capacity; view analytics; exit.
- Unauthorized operations fail even when called outside the menu path.
- Handle invalid input, failed login, invalid payment method, insufficient capacity, database failures, and failed transactions without leaving an open transaction.

### Screening search and creation

- Search supports combined title, genre, screening-language, date, and time criteria. Proposed semantics: title substring, exact genre/language/date, optional inclusive time range; combine supplied filters with AND.
- Each result shows movie, theater, date/time, language, current unit price, available seats, 3D support, and enhanced sound. Order by start time, then screening ID; avoid duplicates caused by genre joins.
- Administrator creation validates movie and theater existence, available language, full runtime within opening hours, and no theater overlap.
- Proposed overlap semantics: existing start is before new end AND existing end is after new start. Serialize conflicting inserts using the theater lock before validation.
- Schedule and capacity views display deterministic ordering and consistent available capacity.

### Pricing and purchases

- Base price is EUR 15; add EUR 5 for a 3D theater and EUR 3 for enhanced sound.
- Apply a 20% discount when release date is more than two years before screening date, using proposal P6.
- Undiscounted examples: EUR 15, 20, 18, 23; discounted examples: EUR 12, 16, 14.40, 18.40.
- One purchase contains one or more tickets for one screening and belongs to one client and one payment method.
- Recompute price during purchase from authoritative data; never trust a CLI/web-supplied amount. Purchase history displays captured amounts, not recalculated historical prices.

### Payment management

- Clients see only their own methods, including an active/inactive indication.
- Adding captures payment type, synthetic card number, and billing address where relevant. Supported types and validation details need approval.
- Deactivation does not delete purchase references. Inactive methods cannot fund subsequent purchases.
- Coordinate booking validation and deactivation with a payment-row lock: whichever transaction obtains the lock first establishes the valid ordering.

### Five SQL queries and three analytics

The proposed five statements in `queries.sql` are:

| Query | Purpose | Required SQL concepts |
|---|---|---|
| Q1 | Combined screening search, used by the application | Multiple joins, bound parameters, filtering, ordering |
| Q2 | Authenticated client's purchase history, used by the application | Multiple joins, client filtering, ordering |
| Q3 | Revenue by movie, with a minimum-tickets parameter defaulting to zero | Multiple joins, aggregation, GROUP BY, HAVING, ordering |
| Q4 | Revenue by theater | Multiple joins, aggregation, GROUP BY, ordering |
| Q5 | Occupancy by movie | Multiple joins, pre-aggregation/subquery, GROUP BY, safe denominator |

Reports show ticket totals and revenue where relevant. Q5 shows sold tickets, offered seats, and occupancy percentage. Aggregate purchase quantities per screening before summing capacities so multiple purchases never multiply the denominator. Define deterministic tie-breaking. Use stored purchase totals for revenue; use left joins and zero handling for the approved zero-sale policy.

Document parameter bindings and how to execute connector-style placeholders. `queries.sql` is the five-query submission artifact, not an unconditional seed script. Keep application versions aligned with it through review and result checks.

## 7. Transaction specification

### Booking sequence

The Python booking service owns a single MySQL transaction on one connection:

1. Verify the caller is an authenticated client and the requested quantity is a positive integer.
2. Begin the transaction and lock the selected screening with `SELECT ... FOR UPDATE`.
3. Read current sold count and capacity after obtaining the lock; validate availability and screening eligibility.
4. Lock and validate the selected payment method, including active state and ownership. Use a consistent lock order: screening, then payment method.
5. Calculate the authoritative unit price and total, then insert the purchase.
6. Increase the screening's sold-ticket count by the purchased quantity.
7. Commit only when every step succeeds.
8. On any validation or database failure after beginning, roll back before returning failure and close/release resources.

No user prompt or external payment call occurs while locks are held. Each concurrent client uses an independent connection. Catch lock timeouts/deadlocks, roll back, and present a retryable failure; automatic retries are not required initially.

Proposed isolation baseline: MySQL's default REPEATABLE READ, explicitly documented and tested. Capacity validation uses a locking/current read; do not reuse a pre-transaction search result as the authoritative capacity check.

### Why the screening lock is required

Without serialization, two buyers can both observe one available seat and each store a purchase. The screening row lock makes the second buyer wait until the first commits or rolls back. It then checks the updated count and rejects a sale when capacity is exhausted. The purchase insert and counter update are atomic in the same transaction.

### Required concurrency and rollback evidence

- Seed capacity 10, sold count 9, and valid existing purchase history totaling 9 tickets.
- Coordinate two independent connections attempting one ticket each; ensure the second attempts booking while the first holds the screening lock. Use synchronization events/barriers with bounded waits, not timing-only sleeps.
- Expect exactly one successful new purchase, one capacity failure, final sold count 10, and no purchase for the loser.
- Inject a failure after purchase insertion and before commit: purchase and counter changes must both roll back. Confirm another connection can subsequently book, proving the lock was released.
- Include a runnable demonstration using two application instances or independent connections and explain the lock behavior during presentation.

## 8. Proposed project structure and code style

This is a target structure, not a description of implemented files. Existing scaffolding must be inspected before moving or replacing it.

```text
project/
  SPEC.md, ROADMAP.md
  ER_diagram.pdf
  schema.sql, data.sql, queries.sql
  compose.yaml, .env.example
  pyproject.toml, .python-version
  README.md
  src/
    __init__.py
    main.py          — login/menu routing
    database.py      — environment and connection lifecycle
    auth.py          — credentials and role checks
    payments.py      — payment management
    screenings.py    — searches and scheduling
    pricing.py       — authoritative price calculation
    booking.py       — transaction and purchase history
    analytics.py     — report queries
    client.py        — client CLI adapter
    admin.py         — administrator CLI adapter
    web/             — optional Flask adapter and templates
  tests/
    conftest.py
    unit/
    integration/
    concurrency/
  docs/
    Groups_3_5_Cinema.pdf
    assumptions.md, er-model-source.*, test-evidence.md
    demo-script.md, contributions.md
```

Conventions: four-space Python indentation, snake_case functions/variables/modules, PascalCase classes, explicit service-boundary types, concise docstrings explaining transaction responsibilities, uppercase SQL keywords, and snake_case SQL identifiers. Use decimals rather than floats for currency. Formatting/linting uses Ruff. No implementation examples are included during this documentation-only stage.

Keep SQL and business rules out of menu/rendering code. Avoid a generic repository framework or unnecessary abstractions. Services accept the authenticated principal and return structured results; they do not prompt or print. Database helpers participating in an existing transaction use its connection and never commit it.

## 9. Proposed command contract

These are commands the implementation must make valid, **not commands verified against the current scaffold**. Run from the repository root. Compose service names are proposed as `db` and `test-db`, with the latter behind profile `test`. Both initialize an empty database and a dedicated project user through environment settings; the test service has separate credentials, storage, and host port.

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
docker compose up -d --wait db
docker compose exec -T db sh -c 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < schema.sql
docker compose exec -T db sh -c 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < data.sql
python -m src.main
```

Environment contract: development uses `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`; tests use the equivalent `TEST_DB_*` settings exclusively. Provide documented synthetic local defaults in the example file. The test fixture refuses the development database and initializes/resets only its dedicated test database. Compose healthchecks support `--wait`.

```sh
docker compose --profile test up -d --wait test-db
python -m pytest tests/unit -q
python -m pytest tests/integration -q
python -m pytest tests/concurrency -q
python -m pytest -q
python -m ruff check src tests
python -m ruff format --check src tests
docker compose --profile test down
```

There is no application compilation step. Schema loading and dependency installation are the setup checks. Normal shutdown must preserve development data; destructive reset commands must be separately documented and explicitly targeted.

Optional extension commands, to be supplied only if the web phase is approved:

```sh
python -m pip install -e '.[web]'
python -m flask --app src.web:create_app run
```

## 10. Testing strategy

Every workstream owns its feature tests. One member maintains shared fixtures and integration evidence, but is not the team's sole tester. Use deterministic fixtures and controllable dates for temporal rules; re-seed demonstration screenings relative to the demo date if past-screening purchases are rejected.

| Level | Required evidence |
|---|---|
| Unit | All surcharge combinations, exact two-year boundary and leap-day policy, decimal totals, invalid quantities, opening-hour and overlap boundary calculations. |
| MySQL integration | Clean schema/data load; constraints; unique emails; login/role enforcement; ownership and inactive methods; combined searches; valid/invalid scheduling; purchases/history; each analytic against hand-calculated expected results. |
| Transaction | Sold counter equals purchase quantities; insufficient-capacity failure; injected rollback after a write; resources and locks released after failure. |
| Concurrency | Coordinated last-seat contention on two independent connections; concurrent conflicting schedule creation; booking/deactivation ordering. |
| Manual CLI/demo | Every required menu path, invalid input recovery, fresh setup from README, representative queries, and live booking/concurrency/report demonstrations. |
| Optional web | Session authentication, role and ownership enforcement, CSRF protection for writes, and parity with existing booking/payment rules. |

No arbitrary coverage percentage is required. Each success criterion must have concrete automated or manual evidence. Mock-only database tests do not establish MySQL locking or rollback correctness.

## 11. Boundaries and success criteria

### Always

- Preserve the PDF's required deliverables and report explicit assumptions.
- Parameterize input values, enforce authorization in services, and preserve purchase history.
- Run relevant tests before merging; cross-review schema, SQL, and transactions.
- Coordinate shared contract/schema changes and keep this specification current.
- Record contributions and ensure all five students can explain the full project.

### Ask first

- Change the approved schema/contract after the foundation checkpoint.
- Add dependencies, alter pricing/time policies, or expand scope.
- Start the optional web phase or change required analytics.

### Never

- Commit actual secrets or real personal/payment data.
- Trust client-provided roles, price totals, ownership, or availability.
- Commit a purchase separately from its sold-count update.
- Remove failing tests simply to make a checkpoint pass.
- Treat this planning session as implementation approval: only `SPEC.md`, `ROADMAP.md`, and `docs/` may be written now.

### Acceptance checklist

- [ ] **SC1:** ER PDF and assumptions describe all required entities, relationships, cardinalities, and participation.
- [ ] **SC2:** `schema.sql` creates a clean MySQL database schema with keys, constraints, and useful indexes; `data.sql` supplies coherent representative fixtures.
- [ ] **SC3:** `queries.sql` contains five meaningful queries collectively meeting joins, filtering/ordering, GROUP BY, HAVING/subquery, non-trivial composition, and application parameterization requirements.
- [ ] **SC4:** Login retrieves stored roles; invalid credentials fail; clients cannot execute administrator functions.
- [ ] **SC5:** Combined screening search returns all PDF-required fields and correct pricing/availability.
- [ ] **SC6:** All five client menu entries work, with owned active methods required for booking and historical methods retained.
- [ ] **SC7:** All five administrator menu entries work; invalid movie, theater, language, opening hours, and overlaps are rejected.
- [ ] **SC8:** Multi-ticket purchase is atomic; sold counts stay within capacity; failed purchases leave no partial records.
- [ ] **SC9:** The exact capacity-10/sold-9 two-connection test produces one success, one failure, final count 10, and no losing purchase.
- [ ] **SC10:** Revenue by movie/theater and occupancy by movie match known expected results without join multiplication.
- [ ] **SC11:** Invalid login/payment, excess quantity, invalid/overlapping schedule, rollback, and concurrent last-seat purchase have recorded test evidence.
- [ ] **SC12:** README explains setup/population/run commands, assumptions, transaction design/testing, and each member's contribution.
- [ ] **SC13:** The demonstration covers ER, fresh database/data, SQL, both roles, booking, concurrency, and analytics; all members can explain them.
- [ ] **SC14:** The instructor's requested post-import Python comment is either included as clarified or its omission is explicitly confirmed with the instructor.

The optional web interface is not required to satisfy SC1–SC14. If undertaken, use server-rendered login, screening search/booking, history/payment management, and basic administrator pages. Reuse services and transaction logic; no SPA, elaborate styling, or duplicated rules.

## 12. Open questions and approval gate

1. Are proposed assumptions P1–P11, the stack additions, structure, command contract, and search semantics acceptable?
2. Which synthetic payment types should be supported, and when is a billing address mandatory? Proposed minimum: credit and debit cards, billing address required for both. Validation checks format, not actual bank authorization.
3. Should email uniqueness/login be case-insensitive? Proposed: trim surrounding whitespace and normalize case consistently before storage/lookup.
4. Confirm the original-language inclusion policy and ER representation at the joint model review.
5. The supplied PDF text explicitly requests a Python comment immediately after imports containing `https://www.youtube.com/watch?v=3TNpOD6bov8`. Proposed interpretation: place it in the CLI entry point; verify whether the instructor expects it elsewhere. This is a source requirement to clarify, not a link to execute or fetch.
6. Assign actual names to A–E. Do not assume skills or equal available hours; rebalance the lanes at checkpoints if needed.
7. Confirm the actual submission date when known. The provisional date is not a commitment.

**Approval request:** Review this complete specification and the companion `ROADMAP.md`. Explicitly approve them or identify amendments. After approval, run `/breakdown` to turn the phases into small implementation tasks; keep generated planning documents within the permitted paths. No implementation begins in this session.
