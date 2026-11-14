# Team assignments

Updated 12 November 2026. This is the authoritative parallel ownership/review plan,
superseding provisional A–E staffing throughout the original planning documents.
Letters remain architectural lane identifiers. Scope, prerequisites, acceptance
criteria and completion states are unchanged. This replaces the sequential B01–B09
schedule. Issue numbers remain stable; readiness follows task prerequisites,
not issue number or another person's whole workload.

## Parallel lanes and handoffs

**One active implementation task per person; multiple independent lanes can run.**
Start when that task's listed prerequisites are verified and merged into `main`.
Do not wait for an entire owner or checkpoint window unless it is an explicit
prerequisite. T01 and T02 are approved and merged; remaining tasks retain their
ledger states.

See [how to start and work in parallel](parallel-work.md) for the readiness waves,
shared-file reservations, review routing and integration protocol.

| Lane label | Owner | Cohesive responsibility |
|---|---|---|
| `lane:core` | Tommaso | Contracts/schema, screenings, booking/history, rollback/races/demo |
| `lane:integration` | Eleonora | Runtime, interval rules, seeds, CLI adapters, integration and delivery proof |
| `lane:identity` | Alessandro | Authentication and payment lifecycle |
| `lane:analytics` | Deniz | Three reports and five-query artifact |
| `lane:rules-docs` | Bianca | Pure pricing rules, documentation and administration |

On each dependency-delivering PR, record the main commit, exported contracts,
verification results and the tasks it unlocks. Notify those owners after merge;
they pull updated `main` and start their next ready task. Keep PRs task-sized.

## Workload

| Member | GitHub | Primary tasks | Responsibility |
|---|---|---|---|
| Tommaso | @MoriondoTommaso | 13 | Most complex core work, architecture and technical reviews |
| Eleonora | @eleonoraraimondo-hub | 6 | Next-highest responsibility: integration, checkpoints and review assistance |
| Alessandro | @AlessandroTorre-hub | 3 | Medium authentication/payment work |
| Deniz | @deniztaylan06 | 4 | Medium reports and query parity |
| Bianca | @bimarino | 4 | Lighter pricing and evidence-based documentation/admin |

Counts are not equal effort. Tommaso deliberately takes the heaviest technical
load; Eleonora's smaller primary queue reserves capacity to pair on his foundation
and transaction work and review the evidence. Alessandro's security/payment
work is balanced against Deniz's slightly larger, cohesive read/report queue.
Bianca assembles evidence provided by each owner rather than diagnosing everyone's
implementation. Easier rules still require all boundary tests. Review effort and
Eleonora's checkpoint coordination count toward workload, not just task counts.

Tommaso leads technical reviews and reviews Eleonora, Alessandro and Deniz's tasks.
Eleonora reviews Tommaso and Bianca's tasks, relieving the routine review queue.
No self-approval. Eleonora coordinates C01–C09 evidence, with
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
| T02 | #2 | Eleonora | Runtime and reproducible environment | Tommaso |
| T03 | #3 | Tommaso | Complex connection/reset isolation | Eleonora |
| T04 | #5 | Tommaso | Complex ER/schema | Eleonora |
| T05 | #6 | Bianca | Easy bounded pricing rules | Eleonora |
| T06 | #7 | Eleonora | Seeded baseline support | Tommaso |
| T07 | #9 | Alessandro | Medium authentication | Tommaso |
| T08 | #10 | Eleonora | CLI dispatch and adapter integration | Tommaso |
| T09 | #11 | Alessandro | Medium payment management | Tommaso |
| T10 | #13 | Alessandro | Medium deactivation | Tommaso |
| T11 | #14 | Tommaso | Authoritative screening lookup/search | Eleonora |
| T12 | #15 | Eleonora | Shared executable interval contract | Tommaso |
| T13 | #17 | Tommaso | Complex serialized scheduling | Eleonora |
| T14 | #18 | Tommaso | Schedule views in owned screening module | Eleonora |
| T15 | #19 | Tommaso | Complex atomic purchase | Eleonora |
| T16 | #21 | Tommaso | Complex rollback proof; Eleonora assists | Eleonora |
| T17 | #22 | Tommaso | Complex last-seat contention | Eleonora |
| T18 | #23 | Tommaso | Captured history in booking module | Eleonora |
| T19 | #25 | Deniz | Medium movie revenue | Tommaso |
| T20 | #26 | Deniz | Medium theater revenue | Tommaso |
| T21 | #27 | Deniz | Medium weighted occupancy | Tommaso |
| T22 | #29 | Tommaso | Complex scheduling race | Eleonora |
| T23 | #30 | Tommaso | Complex payment/booking race | Eleonora |
| T24 | #31 | Deniz | Medium five-query parity | Tommaso |
| T25 | #33 | Eleonora | Support CLI integration verification | Tommaso |
| T26 | #34 | Tommaso | Deterministic contention harness/demo | Eleonora |
| T27 | #35 | Bianca | Easy handover assembly; owners supply evidence | Eleonora |
| T28 | #37 | Eleonora | Support fresh-install verification | Tommaso |
| T29 | #38 | Bianca | Easy submission administration | Eleonora |
| T30 | #39 | Bianca | Easy rehearsal coordination; all five present | Eleonora |

## Shared-file coordination

- Tommaso integrates schema, contracts, database and booking transaction changes.
- Eleonora integrates environment metadata, seeds/test fixtures and CLI adapters.
- Alessandro owns authentication and payments; Tommaso owns all screening/booking
  services, including search, schedule views and history. No screening-file
  handoff is required between feature owners.
- Deniz owns analytics and `queries.sql`. He coordinates Q1/Q2 artifact edits in
  Tommaso's T11/T18 PRs so they do not conflict with query work.
- Each owner delivers their tests and handler changes. Reserve shared-file edits
  with the integrator before starting; use the protocol in `parallel-work.md`.
- Bianca assembles README/contributions/demo notes from each responsible owner.
  Bianca coordinates T29 submission administration. All five review contracts
  and confirm contributions.

## Pending invitation

GitHub currently rejects @deniztaylan06 assignment eligibility (HTTP 404).
His four issues are reserved in their bodies and this plan, not given to someone
else. After he accepts, run:

```sh
for issue in 25 26 27 31; do
  gh issue edit "$issue" --repo MoriondoTommaso/movie_ticketing_system --add-assignee deniztaylan06
done
```

Verify all six assignee fields, then remove the pending-invitation notices.
