# Roadmap — Five-Person Movie Ticketing System

**Status:** Draft for explicit approval alongside `SPEC.md`.
**Planning target:** 23 November 2026, tentative; no effort or calendar commitments assumed.
**Approach:** Short shared design checkpoint, then five parallel feature workstreams with incremental integration. Detailed implementation tasks are deferred to `/breakdown` after approval.

## 1. Parallelization strategy

The database contract is a shared dependency; completion of every database task is not a prerequisite for all other work. Agree on the ER model, table/column names, operation contracts, fixture IDs, error conventions, and transaction ownership early. Students can then prepare their feature SQL, pure logic, CLI adapters, and tests concurrently while the foundational schema/runtime is completed.

Each feature owner delivers a vertical slice: application behavior, relevant CLI interaction, SQL, and tests. Nobody waits until the end to integrate; nobody owns testing or documentation alone.

### Proposed five workstreams

| Owner | Primary responsibility | During initial design/runtime work | First integrated result |
|---|---|---|---|
| A — Data and integration | ER/schema, Compose, connection/configuration contract; shared schema integrator | Draft ER/schema and isolated MySQL environments; coordinate contract decisions | Empty-database setup and working connection factory |
| B — Identity and payments | Login, role checks, payment management, menu entry point | Specify principal/error contract, seeded accounts and payment cases; develop credential/validation checks | Login → role menu → list/add/deactivate own payment method |
| C — Screenings and pricing | Search, pricing, scheduling validation, administrator CLI adapter | Draft search SQL, price boundary tests, interval rules, screening contract | Client search plus administrator creates and views a valid screening |
| D — Booking and concurrency | Purchase transaction, history, client CLI adapter, concurrency demonstration | Design lock sequence/failure cases, purchase result contract, contention harness | Client books tickets and sees persisted purchase history |
| E — Analytics and fixture coordination | Three reports, shared seed/test fixtures, query catalog, evidence coordination | Define expected report totals, prepare synthetic data plan and fixture lifecycle | Administrator sees three numerically verified reports |

Owner letters are placeholders, not assignments based on assumed skill. B and C supply callable CLI handlers to D's client adapter where needed; D owns `client.py` routing. E supplies report handlers to C's `admin.py`. B owns the top-level dispatch in `main.py`.

### File ownership to reduce merge conflicts

| Primary editor | Expected files |
|---|---|
| A | `schema.sql`, `compose.yaml`, `src/database.py`, `.env.example`, ER source/PDF, shared `pyproject.toml` integration |
| B | `src/auth.py`, `src/payments.py`, `src/main.py`, matching feature tests |
| C | `src/screenings.py`, `src/pricing.py`, `src/admin.py`, matching feature tests |
| D | `src/booking.py`, `src/client.py`, booking/history/concurrency tests |
| E | `src/analytics.py`, `data.sql`, `queries.sql`, `tests/conftest.py`, analytic tests, shared README/evidence assembly |

Ownership means primary editor/integrator, not exclusive knowledge. Other members contribute changes through review. All five write their own test evidence and contribution notes; E assembles rather than authors everyone's documentation. A's integration role does not require A to approve every routine feature merge.

## 2. Dependency map

```text
P0: specification and roadmap approval
                  |
P1: joint ER + stable schema/service/fixture contracts
                  |
          +-------+-------+-------+-------+
          |       |       |       |       |
          A       B       C       D       E
       schema/  login/  screening booking reports/
       runtime  payments pricing  harness fixtures
          |       |       |       |       |
          +-------+-------+-------+-------+
             P2: incremental CLI integration
                         |
             P3: transaction/concurrency proof
                         |
             P4: submission and demo gate
                         |
             P5: optional web extension
```

Precise integration dependencies:

- B's database integration requires A's user/payment tables and connection contract.
- C's database integration requires A's catalog/theater/screening tables and agreed reference fixtures.
- D can implement transaction structure and isolated tests against agreed contracts before B/C finish their menus. Its end-to-end purchase needs B's principal/payment validation, C's pricing/lookup, and the database fixtures.
- E's reports can be verified using seeded purchases before live booking is finished; its final integration must also verify purchases created by D's service.
- The client/admin adapters are integrated as each slice lands, not held until every service is complete.
- P3 requires working real-MySQL transactions. Mocks and contract agreement do not satisfy concurrency acceptance.

**Critical path:** approved contracts → schema/runtime → transactional booking → coordinated concurrency proof → clean-install/demo verification. Reports, payment UI, search UI, documentation, and query preparation run alongside this path.

## 3. Phases and checkpoints

### P0 — Approve scope and proposals

**Dependency:** Current interview and approved module map.

- Review `SPEC.md`, especially proposed assumptions and open implementation decisions.
- Confirm the five workstream assignments when member names are available.
- Accept the required CLI, three analytics, and optional-web boundary.

**Exit gate:** Explicit approval of the complete specification and roadmap. Next action: `/breakdown`. No implementation is authorized by this draft.

### P1 — Establish contracts and start all five lanes

**Dependency:** P0 approval.

All members jointly review the ER diagram; A integrates the result. Agree the schema names/types, role representation, payment lifecycle, price/time rules, transaction ownership, operation shapes, and fixture expectations before incompatible implementations diverge.

Parallel outputs:

- **A:** ER model, constraint-enforcement map, schema/runtime/connection foundation.
- **B:** Authentication/payment contracts, credential setup, initial CLI dispatch and focused tests.
- **C:** Search/pricing/schedule contracts and boundary tests.
- **D:** Purchase/rollback contract and deterministic concurrency-test design.
- **E:** Seed plan, expected analytics, isolated test-fixture setup and five-query coverage matrix.

**Exit gate:** ER and contracts reviewed by all five; schema loads into clean MySQL; test database is isolated; every owner can identify the exact inputs/outputs their lane consumes. Record selected versions and command checks. Freeze a first contract revision; subsequent changes require an affected-owner review.

**Verification:** Fresh development/test service startup, schema load, basic connector smoke check, review of fixture consistency and ER-to-schema mapping.

### P2 — Build and integrate five vertical slices in parallel

**Dependency:** P1's approved contracts; each slice starts integration as its tables/runtime become available.

| Lane | Deliverable | Verification checkpoint |
|---|---|---|
| A | Complete schema/indexes; review schema changes; support integration | Clean rebuild; constraints and seeded sold-count reconciliation |
| B | Login/roles and payment management accessible from CLI | Invalid login, client denied admin action, foreign/inactive payment rejection, retained history |
| C | Combined search, correct prices, schedule creation/list/capacity | All returned fields; surcharge/discount boundaries; invalid language/time/overlap |
| D | Multi-ticket purchase, history, rollback path | Atomic insert/update; insufficient capacity; injected failure after write; isolated history |
| E | All three reports, coherent seed data, five-query artifact | Hand-calculated totals/occupancy; zero-sale cases; query-requirement checklist |

Introduce the required booking lock in the first booking slice. Do not postpone concurrency design until the final phase.

**Integration cadence:** Merge small reviewed slices after their focused checks pass. Hold a cross-lane checkpoint after every two or three completed slices, not just at phase end. Re-run broader integration checks when a shared contract/schema change affects multiple lanes.

**Exit gate:** From a clean setup, login as either role and exercise every required menu path; make a purchase and see its effect in history, available capacity, and reports.

### P3 — Prove transactions and shared invariants

**Dependency:** Integrated booking and screening/payment services on real MySQL.

Parallel responsibilities:

- **D + A review:** Coordinated capacity-10/sold-9 contention and rollback evidence.
- **C:** Concurrent overlapping-screening insertion test and opening-hour edge cases.
- **B:** Payment deactivation/booking ordering, ownership and direct service authorization tests.
- **E:** Report reconciliation after purchases, complete query coverage, shared evidence assembly.
- **All:** Fix and retest defects within their feature lane; exchange explanations of the lock sequence.

**Exit gate:** Exactly one last-seat success and one failure; final sold count 10; no partial losing purchase. Rollback removes inserted records/counter changes and releases locks. No concurrent schedule overlap. All required negative cases have evidence.

**Verification:** `python -m pytest tests/concurrency -q`, targeted integration tests for affected services, then the complete required suite once the integrated state is stable. Tests use bounded synchronization so lock failures do not hang indefinitely.

### P4 — Submission readiness and shared understanding

**Dependency:** P3 plus all mandatory functionality and analytics.

- **A:** Verify ER PDF and clean schema/setup on a fresh environment.
- **B:** Verify setup/login/payment instructions and documented synthetic credentials.
- **C:** Verify search/scheduling demonstration and assumptions.
- **D:** Prepare a repeatable booking/concurrency demonstration and lock explanation.
- **E:** Assemble README, query/analytic demonstrations, test evidence, and contribution records from all owners.
- **All:** Rehearse the whole demonstration; each member explains a module they did not primarily implement.

**Exit gate:** SC1–SC14 in `SPEC.md` are met, instructor-specific comment requirement is resolved, required files are present, and README commands work from a clean environment. Preserve a known-good mandatory deliverable before considering the web extension.

### P5 — Optional minimal web interface

**Dependency:** P4 passes and the team explicitly chooses to proceed.

Use Flask and server-rendered pages backed by the same services. Start with shared app/session/template contracts, then parallelize:

- **A:** Web configuration and integration support.
- **B:** Login/logout, session handling and payment pages.
- **C:** Screening search and administrator schedule pages.
- **D:** Booking/history pages and transaction regression checks.
- **E:** Analytics pages and shared web verification.

Keep styles minimal. Add CSRF protection for writes and enforce role/ownership checks through existing services. Do not duplicate pricing or transaction code in route handlers.

**Exit gate:** Browser flows preserve the tested rules, required CLI still passes, and optional setup/run instructions are documented. If the deadline is tight, omit this phase.

## 4. Collaboration and cross-review

- Use one primary editor per shared file. Propose schema/contract changes in writing with the affected modules and test impact before merging.
- Prefer short-lived feature branches and small merges into a working main branch.
- Each feature owner supplies code, tests, and a short explanation. Review pairing: A reviews D's transaction; D reviews C's scheduling lock; C reviews E's SQL; E reviews B's authorization/data cases; B reviews A's schema/configuration.
- Rotate walkthroughs so everyone explains the ER model, one nontrivial query, the role boundary, and the booking transaction.
- Record contributions as work happens rather than reconstructing them at submission.
- Once A's foundation work stabilizes, A supports the critical booking path and shared integration. Once E's reports stabilize, E helps verify end-to-end report/booking reconciliation. Rebalance at checkpoints without silently changing public contracts.

## 5. Risks and mitigations

| Risk | Impact | Mitigation / owner |
|---|---|---|
| Schema drift blocks several students | High | Joint ER/contract freeze, primary schema editor, affected-owner review; A + all |
| Booking waits on completed menus | High | Service contracts and shared fixtures allow D to work independently of UI completion; B/C/D |
| Concurrent buyers oversell | High | Early screening row lock, independent-connection contention test, atomic purchase/counter update; D, reviewed by A |
| Schedule check has a race | High | Lock theater before overlap check/insertion; test simultaneous inserts; C |
| Failed transaction leaves partial records or locks | High | Caller-owned transaction, injected failure after write, rollback/resource checks; D |
| Payment deactivation races with booking | Medium | Lock payment row and define linearized ordering; B/D |
| Analytics multiply capacity or revenue through joins | High | Aggregate at screening/purchase grain, test multiple purchases and known totals; E |
| Stale demo dates break purchasing | Medium | Controllable test date, generated relative-date demo screenings and pre-demo rehearsal; C/E |
| Fixture/test setup becomes one person's bottleneck | Medium | E owns shared lifecycle, each lane supplies focused data requirements/tests; all |
| Shared CLI/configuration files cause merge conflicts | Medium | Explicit primary editors and handler contracts, small integration merges; A/B/C/D |
| Differing MySQL/Python versions cause inconsistent results | Medium | Pin shared environment versions; verify fresh setup; A |
| Optional web consumes mandatory-deliverable effort | High | Start only after P4 and explicit go-ahead; all |
| Students cannot explain others' work | High | Cross-reviews and rotating full-system rehearsals; all |
| Deadline or member availability changes | Medium | Dependency-based phases, checkpoint rebalancing, retain optional scope buffer; all |
| Ambiguous PDF rules lead to inconsistent implementations | Medium | Approve the assumptions register and clarify instructor comment placement before finalization; all |

## 6. What `/breakdown` should produce next

After explicit approval, turn these phases into ordered, small tasks with:

- A workstream owner and reviewer.
- Concrete acceptance criteria tied to SPEC success-criterion IDs.
- Required contracts and predecessor tasks.
- Expected files, normally no more than about five per task.
- An executable focused verification command or a precise manual check.
- Explicit parallel groups and cross-lane checkpoints after every two or three completed slices.

Keep subsequent planning output under `docs/` (for example `docs/tasks.md`) unless the user changes the documentation-only path restriction. Do not create a default `tasks/` directory during this planning scope.

**Approval requested:** Approve `SPEC.md` and this roadmap, including the proposed implementation policies, or specify changes. Then run `/breakdown`.
