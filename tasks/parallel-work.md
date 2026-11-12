# Parallel work with minimal merge friction

This is the current execution policy, replacing sequential B01–B09. The task
dependencies in [the ledger](todo.md) remain mandatory. A lane is a person's area
of responsibility, not permission to start all their issues immediately.

## Start here

1. **Tommaso starts T01 (#1)** with a shared contract review. Freeze schema names,
   function signatures/result/error shapes, principal, clock, fixtures and lock
   order. Eleonora checks runtime/fixtures, Alessandro auth/payments, Deniz report
   expectations and Bianca rule boundaries. Bianca sends the instructor question.
2. **After T01 merges, Eleonora delivers T02 (#2).** Other members can prepare
   designs and test cases against agreed contracts, but cannot claim blocked
   implementation tasks are complete.
3. **After T02 merges, actual implementation branches split:** Tommaso does
   T03 → T04, Bianca does T05, and Eleonora does T12. They edit different files.
4. **After T04, Alessandro starts T07.** Eleonora starts T06 when T05 is also
   merged. These are independent auth and seed changes.
5. **After T07, Eleonora delivers T08.** T06 and T08 are both her work: finish one
   before the other. Their order can follow readiness; no additional dependency
   is added between them.
6. **After T06 and T08, three substantial lanes run together:** Alessandro
   T09 → T10, Deniz T19 → T20 → T21, Tommaso T11 then T13 (T13 also needs T12).
   Tommaso also owns T14 after T13, keeping all screening edits in one lane.
   Bianca can prepare documentation from merged evidence while its final T27
   verification remains blocked. Eleonora reviews,
   integrates adapter changes and runs due checkpoints rather than opening a
   competing feature lane.

There is a real foundation bottleneck. Five people cannot independently build
working database features on day one; preparation is useful but not verified
feature completion. Once seeds and dispatch land, the lanes overlap naturally.

## Subsequent readiness, not numerical order

| Work | Owner | Required merged tasks |
|---|---|---|
| T14 schedule views | Tommaso | T13 |
| T15 atomic booking | Tommaso | T05, T06, T09, T10, T11 |
| T16 → T17 rollback/last-seat proof | Tommaso | T15, then T16 |
| T18 history | Tommaso | T15 |
| T22 schedule race | Tommaso | T13 |
| T23 payment race | Tommaso | T10, T15 |
| T26 contention demo | Tommaso | T17 |
| T24 five-query artifact | Deniz | T11, T18, T21 |
| T25 integrated CLI proof | Eleonora | T10, T14, T17, T18, T21, T22, T23, T24 |
| T27 handover documentation | Bianca | T24, T25, T26 |
| T28 clean installation | Eleonora | T27 and C09 |
| T29 instructor/submission closure | Bianca | T01, T08, T27 |
| T30 rehearsal | Bianca coordinates all five | T26, T27 |

Tommaso's suggested post-discovery order is T13 → T14 → T15 → T18 → T16 → T17 →
T22 → T23 → T26. T18 is deliberately early to unlock Deniz's T24. If payment
work blocks T15, do ready T22 instead. This is one person's queue, not parallel
tasks assigned to Tommaso. Deniz's reports do not wait for live booking; their
seed-based tests are followed by the later live cross-service checks.

## Shared files: one editor at a time, not one team member at a time

| Integrator | Files / seam | How others contribute |
|---|---|---|
| Tommaso | Schema, contracts, `src/database.py`, `src/screenings.py`, `src/booking.py` | Agree contract changes first; all screening/booking edits stay in this lane |
| Eleonora | Runtime metadata, `data.sql`, `tests/conftest.py`, `src/main.py`, `src/client.py`, `src/admin.py` | Feature owners supply service tests and narrow adapter changes; serialize adapter edits |
| Alessandro | `src/auth.py`, `src/payments.py` | Booking uses the agreed caller-owned transaction helper; no duplicate payment logic |
| Deniz | `src/analytics.py`, `queries.sql` | Reserve Q1/Q2 changes in T11/T18; T24 starts after both merge |
| Bianca | Pure pricing module, README and assembled docs | Other owners supply evidence instead of rewriting the shared documentation |

Before touching a shared file, comment on the issue/PR:

```text
Editing: src/client.py
Task/branch: T09 / feat/t09-payment-methods
Integrator: Eleonora
Release condition: this PR merged; next editor starts from updated main
```

The integrator confirms the slot and notes the next waiting editor. Until then,
work on task-local service/tests, not another version of the shared adapter.
Pairing or committing to the same task branch is fine by agreement. Keep one PR
per task where practical; the task cannot close until its CLI/SQL additions and
all other acceptance criteria pass. A file reservation is released at merge,
not when its author merely finishes editing.

Eleonora owns the pure `src/schedule_rules.py` contract (T12); Tommaso consumes it
from screening services rather than implementing a second version.
Do not perform whole-project formatting or opportunistic renames in feature PRs.

## Review and merge without making Tommaso the only queue

- Eleonora reviews Tommaso and Bianca; Tommaso reviews Eleonora, Alessandro and
  Deniz.
- Review prerequisite-unblocking PRs first: runtime/schema, seeds/auth/dispatch,
  payment/search helpers, then history/query parity. Give reviews a short daily
  team slot rather than waiting until the end of an implementation block.
- Authors include commands/results, affected contracts and unlocked task IDs.
  Integrators check their shared-file sections; this is not a second review of
  every unrelated file.
- Tommaso or Eleonora can merge a reviewed PR after required checks pass. Neither
  self-approves. Eleonora can merge routine approved work so Tommaso keeps coding.
- Branch from updated `main` after prerequisites merge. Avoid long-lived personal
  branches, branches off unmerged feature branches, and cross-branch cherry-picks.
  The [Git guide](../docs/git-workflow.md) has the commands.

## Integration and status

Keep one implementation issue in progress per person. Use `lane:*` labels to
filter ownership; they are not readiness labels. In issue updates distinguish
**blocked by #...**, **in progress**, **in review**, and **done with evidence**.
Do not remove a dependency just to mark a task ready.

Eleonora coordinates C01–C09; Tommaso coordinates C10. Named checkpoints keep
their original dependencies and acceptance criteria: reports may finish early,
but C07 cannot pass before C06. After every 2–3 merged tasks, review the delivered
scope and run applicable broad checks even if a named checkpoint is not yet
ready; record this interim evidence without falsely closing that checkpoint.

Parallel verification uses separate local Compose projects, published ports,
test databases/credentials and volumes. T02/T03 establish and verify that setup.
If a shared target must be used, Eleonora serializes reset-bearing suites and
demo runs. Never reset a target used by another member's tests.

At each merge, notify owners of newly unblocked tasks with the main commit and
contract/evidence links. At the daily check, report just: ready next task,
blocker, shared-file slot needed, PR waiting for review. Escalate contract changes
to the affected owners before implementation, rather than resolving semantic
conflicts during a merge.
