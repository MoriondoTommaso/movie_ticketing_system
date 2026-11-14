# T01 — Assumptions and enforcement register

Revision: T01-r1, 14 November 2026. Status: proposed contracts, awaiting all-lane
review. Approved interview policies below are not reopened by this draft.
Submission: **23 November 2026**. Required delivery is CLI; Flask remains deferred.

## Approved policies

- Python 3.13, MySQL 8.4/InnoDB via Compose, explicit parameterized SQL.
  Exact compatible package/image pins belong to T02, not this design task.
- One cinema, `Europe/Rome`; screening `DATETIME` values represent local time.
  An injected aware clock is converted to Rome before removing timezone metadata.
  Start precision is minutes; reject nonzero seconds/microseconds in scheduling.
- Opening interval: start at or after 10:00, finish by 23:59 on the same date.
  Half-open screening intervals allow back-to-back shows; no cleaning interval.
- Default search and booking require start strictly later than the current instant.
  New administrator scheduling also requires a future start.
- EUR 15 base, +5 for theater 3D and +3 for enhanced sound. Discount the whole
  unit amount by 20% only after the second calendar anniversary of release.
  A February 29 anniversary is February 28 in non-leap years.
  Use Decimal, ROUND_HALF_UP to two decimal places, then multiply by quantity.
- Preloaded accounts only; email is stripped and casefolded before storage/lookup.
  Each account has exactly one role. Client name/address live in client_profiles.
  Admin credentials cannot buy; use a separate client account.
- Passwords use salted standard-library scrypt. Store algorithm, n/r/p, salt and
  derived key; synthetic demo credentials only. Proposed encoding:
  `scrypt$16384$8$1$<salt_hex>$<key_hex>`, 16-byte salt, 32-byte key.
  Verification accepts only these bounded parameters and lengths.
- Synthetic credit/debit only; remove ASCII spaces and hyphens, then require
  13–19 ASCII digits and a stripped nonempty billing address. No Luhn, CVV,
  expiry or bank authorization. Displays show only the last four digits.
- Deactivation is permanent and preserves purchase references; no deletion,
  reactivation, cancellation, refunds, registration or seat assignment.
- All scheduled screenings, including historical ones, count in analytics.
  Zero-sale entities remain visible; occupancy is weighted by offered seats.
  No screenings means occupancy None, rendered N/A.

## Enforcement map

| Invariant | Enforcement |
|---|---|
| Unique normalized email, valid role/type, positive local numeric fields | SQL UNIQUE/CHECK/NOT NULL; auth/payment services normalize input |
| Mandatory client profile for client role; no admin profile | Seed validation/authentication; cross-table role rule is not a local CHECK |
| At least one available language and genre; original language available | Seed validation; catalog is read-only in this delivery |
| Screening language belongs to movie | Composite SQL FK to movie_languages |
| Purchase client/payment ownership and active state | Booking payment helper with payment-row lock |
| Capacity never exceeded; counter equals purchase quantities | Booking screening-row lock, one transaction; seed reconciliation |
| No theater overlap; valid runtime/opening hours/future start | Screening service locks theater before current overlap read |
| Positive integer quantity, excluding bool | Booking service before transaction plus SQL positive CHECK |
| Captured price/total consistent | Booking recomputes Decimal price; SQL amount/quantity CHECK |
| Retained purchase history | Restrictive foreign keys; deactivate, never delete |
| Role/ownership enforced outside menus too | Every public service validates authenticated principal |
| Test reset cannot target development | T03 target guard plus separate scoped MySQL account |

Direct ad-hoc SQL writes are unsupported; SQL constraints do not claim to enforce
cross-row capacity, role/profile completeness, or schedule overlap.

## Review and changes

Exact schema, operation and fixture proposals are in contracts.md and fixtures.md.
All five lanes must review before freeze. Record real approvals in contributions.md;
no generated document constitutes a student's approval.
