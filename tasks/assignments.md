# Team assignments

Updated 10 November 2026. This is the authoritative named ownership/review plan,
superseding provisional A–E staffing throughout the original planning documents.
Letters remain architectural lane identifiers. Scope, prerequisites, acceptance
criteria and completion states are unchanged.

## Workload

| Member | GitHub | Primary tasks | Responsibility |
|---|---|---|---|
| Tommaso | @MoriondoTommaso | 8 | Most complex contracts, schema, transactions and races; lead reviews |
| Eleonora | @eleonoraraimondo-hub | 5 | Runtime/verification support and review assistance |
| Alessandro | @AlessandroTorre-hub | 5 | Medium identity, payments and client flows |
| Deniz | @deniztaylan06 | 6 | Medium fixtures, search, reports and SQL parity |
| Bianca | @bimarino | 6 | Easier pure rules, read-only views, docs and administration |

Counts are not equal effort. Tommaso deliberately takes the heaviest technical
load; Eleonora's smaller primary queue reserves capacity to help him. Alessandro's
security/payment work is balanced against Deniz's slightly larger, cohesive report
queue. Bianca assembles evidence provided by each owner rather than diagnosing
everyone's implementation. Easier rules still require all boundary tests.

Tommaso reviews all other owners' tasks; Eleonora reviews Tommaso's work and helps
triage reviews. No self-approval. Eleonora coordinates C01–C09 evidence, with
Tommaso leading technical review. Tommaso owns C10 coordination, reviewed by
Eleonora. All five participate in checkpoints and rehearsal. Issue assignees are
primary owners; reviewers are recorded in bodies and requested on actual PRs.

At every checkpoint, compare actual effort/blockers and explicitly rebalance
remaining tasks if needed. Keep one active implementation task per person.
Eleonora pairs on Tommaso's failure/race evidence before taking extra work.
All owners supply their own tests, evidence and contributions. No hours or dates
are invented; ledger dependencies remain binding.

## Task allocation

| Task | Issue | Owner | Difficulty / focus | Reviewer |
|---|---|---|---|---|
| T01 | #1 | Tommaso | Complex shared contracts | Eleonora |
| T02 | #2 | Eleonora | Runtime support | Tommaso |
| T03 | #3 | Tommaso | Complex connection/reset isolation | Eleonora |
| T04 | #5 | Tommaso | Complex ER/schema | Eleonora |
| T05 | #6 | Bianca | Easy bounded pricing rules | Tommaso |
| T06 | #7 | Deniz | Medium coherent fixtures | Tommaso |
| T07 | #9 | Alessandro | Medium authentication | Tommaso |
| T08 | #10 | Alessandro | Medium CLI dispatch | Tommaso |
| T09 | #11 | Alessandro | Medium payment management | Tommaso |
| T10 | #13 | Alessandro | Medium deactivation | Tommaso |
| T11 | #14 | Deniz | Medium screening search | Tommaso |
| T12 | #15 | Bianca | Easy bounded interval rules | Tommaso |
| T13 | #17 | Tommaso | Complex serialized scheduling | Eleonora |
| T14 | #18 | Bianca | Easy read-only schedule views | Tommaso |
| T15 | #19 | Tommaso | Complex atomic purchase | Eleonora |
| T16 | #21 | Eleonora | Support rollback proof, paired with Tommaso | Tommaso |
| T17 | #22 | Tommaso | Complex last-seat contention | Eleonora |
| T18 | #23 | Alessandro | Medium purchase history | Tommaso |
| T19 | #25 | Deniz | Medium movie revenue | Tommaso |
| T20 | #26 | Deniz | Medium theater revenue | Tommaso |
| T21 | #27 | Deniz | Medium weighted occupancy | Tommaso |
| T22 | #29 | Tommaso | Complex scheduling race | Eleonora |
| T23 | #30 | Tommaso | Complex payment/booking race | Eleonora |
| T24 | #31 | Deniz | Medium five-query parity | Tommaso |
| T25 | #33 | Eleonora | Support CLI integration verification | Tommaso |
| T26 | #34 | Eleonora | Support contention harness/demo | Tommaso |
| T27 | #35 | Bianca | Easy handover assembly; owners supply evidence | Tommaso |
| T28 | #37 | Eleonora | Support fresh-install verification | Tommaso |
| T29 | #38 | Bianca | Easy submission administration | Tommaso |
| T30 | #39 | Bianca | Easy rehearsal coordination; all five present | Tommaso |

## Shared-file coordination

- Tommaso integrates schema, contracts, database and booking transaction changes.
- Eleonora integrates environment metadata and test lifecycle with Tommaso.
- Alessandro integrates authentication, payments, top-level/client CLI routing.
- Tommaso integrates screening writes; Deniz contributes search, Bianca views.
  Serialize their changes to `src/screenings.py` and `src/admin.py`.
- Deniz integrates analytics, seeds, queries and fixture requirements; Eleonora
  coordinates isolated test runs. Alessandro coordinates T18 booking-file edits
  with Tommaso before starting.
- Bianca assembles README/contributions/demo notes from each responsible owner.
  Bianca sends the T01 instructor clarification request and follows up in T29,
  replacing provisional B. All five review contracts and confirm contributions.

## Pending invitation

GitHub currently rejects @deniztaylan06 assignment eligibility (HTTP 404).
His six issues are reserved in their bodies and this plan, not given to someone
else. After he accepts, run:

```sh
for issue in 7 14 25 26 27 31; do
  gh issue edit "$issue" --repo MoriondoTommaso/movie_ticketing_system --add-assignee deniztaylan06
done
```

Verify all six assignee fields, then remove the pending-invitation notices.
