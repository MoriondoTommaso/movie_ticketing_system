# T01 — Contributions and contract review

14 November 2026. Submission: **23 November 2026**.
This is a review ledger, not an assertion that students performed generated work.

## Named responsibilities

| Member | Responsibility | T01 review scope |
|---|---|---|
| Tommaso | Core/contracts, schema, screening and booking services | ER keys, lifecycle, transactions, lock ordering |
| Eleonora | Runtime, interval rules, seeds, CLI integration, verification | Connections, clocks, fixtures, adapter contracts; T01 reviewer |
| Alessandro | Identity/payment lifecycle | Principal trust, credentials, ownership and active-state rules |
| Deniz | Analytics/five-query artifact | Query bindings, report types, zero-sale policy and numeric oracles |
| Bianca | Pricing, documentation, submission administration | Anniversary/rounding boundaries, assumptions and delivery records |

## Actual work recorded

- User completed the policy/design interview on 14 November; decisions are
  recorded in SPEC §12 and tasks/plan.md.
- Coding assistant drafted assumptions.md, contracts.md, fixtures.md and this
  review record for T01. No runtime implementation, database setup or student
  approval is claimed.

## Required joint review — T01-r1

Review SPEC §§4–7 and SC1–SC13 against all three design documents. Record a
review reference, date and requested amendments for each person, then freeze
the accepted revision. Silence, generated names and automated checks are not signoff.

| Reviewer | State | Review reference/date |
|---|---|---|
| Tommaso | Pending | — |
| Eleonora | Pending | — |
| Alessandro | Pending | — |
| Deniz | Pending | — |
| Bianca | Pending | — |

Until this gate passes, contracts remain draft, T01 is IN REVIEW and dependent
implementation tasks are not ready. Subsequent schema/contract changes require
affected-owner agreement and updated tests/evidence.

## Verification record

T01 uses documentation review and whitespace/consistency checks, not application
TDD: no executable behavior is changed. Build/lint/type tooling belongs to T02.
The PR/ledger records commands and actual results; live MySQL and future feature
tests are not claimed by this task.
