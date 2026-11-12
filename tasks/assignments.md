# Team assignments

Updated 12 November 2026. This is the authoritative sequential ownership/review plan,
superseding provisional A–E staffing throughout the original planning documents.
Letters remain architectural lane identifiers. Scope, prerequisites, acceptance
criteria and completion states are unchanged. The block order below replaces the
earlier parallel-workstream schedule. Issue numbers remain stable; execute in
block order, not numerical issue order.

## Sequential blocks and handoffs

**Only one implementation block is active across the team.** The next owner starts
after the previous block's tasks are verified, reviewed, merged into `main`, and
the handoff is recorded. Reviews and pairing support the active owner; they do
not open another implementation lane. All blocks currently remain TODO.

| Block | Owner | Tasks in execution order | Checkpoints / handoff |
|---|---|---|---|
| B01 — Database foundation | Tommaso | T01, T02, T03, T04 | C01 after T03; hand over reviewed schema/runtime after T04 |
| B02 — Pure business rules | Bianca | T05, T12 | Hand over tested price and interval helpers |
| B03 — Seeded integration baseline | Eleonora | T06 | C02; hand over coherent data and fixture expectations |
| B04 — Client discovery and payments | Alessandro | T07, T08, T09, T10, T11 | C03 after T09; C04 after T11 |
| B05 — Transaction engine and race proof | Tommaso | T13, T15, T16, T17, T22, T23 | Reviewed booking/scheduling invariants; Eleonora assists with evidence |
| B06 — Read-only views and SQL reports | Deniz | T14, T18, T19, T20, T21, T24 | C05 after T14; C06 after T18; C07 after T21; C08 after T24 |
| B07 — Integrated experience and demo | Eleonora | T25, T26 | Hand over working CLI journey evidence and contention demo |
| B08 — Documentation and submission preparation | Bianca | T27, T29, T30 | C09 after T27; instructor confirmation and team rehearsal before handoff |
| B09 — Independent delivery verification | Eleonora | T28 | C10 final delivery gate, coordinated by Tommaso |

The seed baseline and fresh-install check are deliberately small support blocks:
the first needs Bianca's pricing rules, and the last needs her finished README.
Tommaso returns for transaction work after client/payment prerequisites exist.
This keeps complex work with Tommaso and easier work with Bianca without assigning
someone a block that is blocked on a later owner's work.

Within B05, record an interim integration review after T13/T15/T16 and another
after T17/T22/T23, running the delivered suite and inspecting race evidence.
Do not close C05/C06 early: their view/history requirements become available in
B06. Every other named checkpoint retains its original acceptance criteria and
prerequisites; the table says when they are all available.

On the final task issue of each block, record:

```text
Block Bxx complete; handing off to <next owner / block>.
Merged PRs and main commit: ...
Verification commands/results and checkpoint links: ...
Changed contracts/shared files and setup notes: ...
Open blockers: none (otherwise stop the handoff).
Reviewer sign-off: ...
Next owner: acknowledge receipt before starting from updated main.
```

Use small task PRs inside the block rather than one oversized PR. The block owner
coordinates all shared-file edits during that turn. At handoff, transfer context
and file responsibility to the next owner. Do not change owners opportunistically
or start future blocks to bypass a blocked prerequisite.

## Workload

| Member | GitHub | Primary tasks | Responsibility |
|---|---|---|---|
| Tommaso | @MoriondoTommaso | 10 | B01/B05: foundation, transactions and races; lead reviews |
| Eleonora | @eleonoraraimondo-hub | 4 | B03/B07/B09: fixture and verification support; review assistance |
| Alessandro | @AlessandroTorre-hub | 5 | Medium identity, payments and client flows |
| Deniz | @deniztaylan06 | 6 | B06: medium views, history, reports and SQL parity |
| Bianca | @bimarino | 5 | B02/B08: easier pure rules, docs and administration |

Counts are not equal effort. Tommaso deliberately takes the heaviest technical
load; Eleonora's smaller primary queue reserves capacity to pair on his foundation
and transaction blocks and review their evidence. Alessandro's security/payment
work is balanced against Deniz's slightly larger, cohesive read/report queue.
Bianca assembles evidence provided by each owner rather than diagnosing everyone's
implementation. Easier rules still require all boundary tests. Review effort and
Eleonora's checkpoint coordination count toward workload, not just task counts.

Tommaso reviews all other owners' tasks; Eleonora reviews Tommaso's work and helps
triage reviews. No self-approval. Eleonora coordinates C01–C09 evidence, with
Tommaso leading technical review. Tommaso owns C10 coordination, reviewed by
Eleonora. All five participate in checkpoints and rehearsal. Issue assignees are
primary owners; reviewers are recorded in bodies and requested on actual PRs.

At every checkpoint, compare actual effort/blockers and explicitly rebalance
remaining tasks if needed. Keep one active implementation block for the whole team.
Eleonora pairs on Tommaso's failure/race evidence before taking extra work.
All owners supply their own tests, evidence and contributions. No hours or dates
are invented; ledger dependencies remain binding.

## Task allocation

| Task | Issue | Owner | Difficulty / focus | Reviewer |
|---|---|---|---|---|
| T01 | #1 | Tommaso | Complex shared contracts | Eleonora |
| T02 | #2 | Tommaso | Foundation runtime | Eleonora |
| T03 | #3 | Tommaso | Complex connection/reset isolation | Eleonora |
| T04 | #5 | Tommaso | Complex ER/schema | Eleonora |
| T05 | #6 | Bianca | Easy bounded pricing rules | Tommaso |
| T06 | #7 | Eleonora | Seeded baseline support | Tommaso |
| T07 | #9 | Alessandro | Medium authentication | Tommaso |
| T08 | #10 | Alessandro | Medium CLI dispatch | Tommaso |
| T09 | #11 | Alessandro | Medium payment management | Tommaso |
| T10 | #13 | Alessandro | Medium deactivation | Tommaso |
| T11 | #14 | Alessandro | Medium screening search | Tommaso |
| T12 | #15 | Bianca | Easy bounded interval rules | Tommaso |
| T13 | #17 | Tommaso | Complex serialized scheduling | Eleonora |
| T14 | #18 | Deniz | Read-only schedule views | Tommaso |
| T15 | #19 | Tommaso | Complex atomic purchase | Eleonora |
| T16 | #21 | Tommaso | Complex rollback proof; Eleonora assists | Eleonora |
| T17 | #22 | Tommaso | Complex last-seat contention | Eleonora |
| T18 | #23 | Deniz | Medium purchase history | Tommaso |
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
- Tommaso integrates environment metadata in B01; Eleonora supplies fixture and
  verification support in B03 and subsequent reviews.
- Alessandro integrates authentication, payments, top-level/client CLI routing.
- Alessandro hands screening search to Tommaso for scheduling writes, then Deniz
  adds read-only views in B06. Each handoff covers `src/screenings.py` and adapters.
- Deniz integrates analytics, history and queries in B06, using Eleonora's seed
  baseline. Tommaso hands over `src/booking.py` before Deniz adds T18 history.
  Eleonora coordinates isolated verification runs.
- Bianca assembles README/contributions/demo notes from each responsible owner.
  Bianca sends the T01 instructor clarification request and follows up in T29,
  replacing provisional B. All five review contracts and confirm contributions.

## Pending invitation

GitHub currently rejects @deniztaylan06 assignment eligibility (HTTP 404).
His six issues are reserved in their bodies and this plan, not given to someone
else. After he accepts, run:

```sh
for issue in 18 23 25 26 27 31; do
  gh issue edit "$issue" --repo MoriondoTommaso/movie_ticketing_system --add-assignee deniztaylan06
done
```

Verify all six assignee fields, then remove the pending-invitation notices.
