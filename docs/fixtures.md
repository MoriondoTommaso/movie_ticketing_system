# T01 — Fixture IDs, report oracles and race contracts

T01-r1 oracle (approved by the user on 14 November 2026), implemented by T06.
Shipped `data.sql` anchor: **D = 2026-11-23**. All data is fictional.

## Identity and reference IDs

- users: admin 1; clients 11–16, each with client_profiles and distinct fictional
  names/addresses. Credentials: admin@example.test / DemoAdmin-2026!,
  client11@example.test through client16@example.test / DemoClient-2026!.
   T06 generated a distinct random 16-byte salt per account, frozen in `data.sql`.
   Encoding: `scrypt$16384$8$1$<salt_hex>$<key_hex>`; 32-byte derived key,
   UTF-8 password, standard-library `hashlib.scrypt(n=16384, r=8, p=1, dklen=32)`.
   Tests independently derive every stored key from the documented password.
- payment_methods: 201 client11 active credit; 202 client11 inactive debit;
  203 client12 active debit; 204 client13 active credit; 205 client14 active debit;
  206 client15 active credit; 207 client16 active debit. Every address is synthetic.
  Use `0000000000000201` through `0000000000000207` respectively.
- theaters: 1 capacity10 plain; 2 capacity20 3D; 3 capacity30 enhanced sound.
  Focused tests add theater4 capacity10 with both flags; not part of report oracle.
- languages: 1 Italian, 2 English; genres: 1 Drama, 2 Comedy.
- movies 1–8 have titles Fixture Movie 1–8, runtime90, nonempty description,
  original_language_id=2, available languages {1,2}. Genre1 on every movie;
  genre2 additionally on movies1 and3 to expose duplicate search joins.
- Movies1,2,5,6,8 release on anchor D; movies3,4,7 release on D minus three
  calendar years (Feb29 maps to Feb28 if necessary). All seeded screenings below
  therefore have a stable full-price/discount category.

## Demo dates and database lifecycle

T06 declares one anchor D in a header/fixtures record. For delivery, choose
2026-11-23; all screenings are future relative to that day's demonstration.
Tests use a fixed clock at D 09:00 Rome and never depend on machine date.
For a later demo, regenerate date literals from a newly declared D before loading
an empty isolated demo database; do not alter purchased historical records.
The SQL seed remains executable SQL with explicit literals and documented D.
Test suites reset only their dedicated target under the T03 guard, never dev/demo.
Each independent verifier uses separate Compose project/ports/credentials/volumes,
or Eleonora serializes reset-bearing runs on a shared test target.

### Loading and repeating the demo

Load `schema.sql`, then `data.sql`, once into an empty dedicated database using
the plan's MySQL import commands. The seed uses one transaction and explicit
INSERTs, ending with COMMIT; it has no resets, upserts or constraint disabling.
Do not use mysql `--force`: an import error must stop loading. A duplicate import
is an error, not an update mechanism. Keep existing purchase history intact.

For another demo date D', make a separate copy of `data.sql` for a **new empty**
demo database and update its header with D'. Apply this complete mapping:

| Original literal | Replacement |
|---|---|
| 2026-11-23 | D' (recent releases and purchase day) |
| 2023-11-23 | D' minus three calendar years; Feb29 maps to Feb28 |
| 2026-11-24 through 2026-11-28 | D'+1 through D'+5 respectively |

Compute all replacements from the original copy, in one pass (avoid cascading
find/replace). Preserve purchase time 08:00 and screening time 10:00, IDs,
quantities and amounts. Recheck the twelve rows against the day-offset table
below before importing. All old releases stay over two years old and all new
releases stay recent; the price/report oracles therefore remain unchanged.
Use an injected aware clock D' 09:00 in `Europe/Rome` for a scripted rehearsal.
The checked-in SQL and automated tests always retain the original fixed anchor;
they never silently shift with the machine's current date.

### Explicit test lifecycle

- `db_connection` / `db_factory`: independent connections, no schema or seed reset.
- `schema_database`: opts into `empty_database`'s validated test-only reset,
  loads schema, and yields the connection; teardown resets that test target.
- `seeded_database`: opts into schema plus the actual committed `data.sql`.
  Independent connections see the rows; fixture cleanup closes connections before
  the guarded reset. No production service implicitly seeds.
- `pricing_database`: additionally inserts/commits theater4 (capacity10, both
  flags) for focused coverage of all eight prices. Ordinary seed/report tests
  still contain exactly three theaters, so capacity totals remain 220.

Verification: `python -m pytest tests/integration/test_seed.py -q` uses real
MySQL, validates credentials, calendar/schedule constraints, ownership,
per-screening counters, captured amounts and the independent report totals below.
These are fixture-oracle checks, not implementation of the later Q1–Q5 services.

## Twelve-screening seed and purchase reconciliation

All screening starts are 10:00; rows sharing the date use different theaters.
All use language2. Price is captured at purchase, Decimal EUR.

| Screening | Day | Movie | Theater/capacity | Sold | Unit price |
|---|---|---|---|---|---|
| 101 | D+1 | 1 | 1/10 | 9 | 15.00 |
| 102 | D+1 | 1 | 2/20 | 4 | 20.00 |
| 103 | D+1 | 2 | 3/30 | 30 | 18.00 |
| 104 | D+2 | 2 | 1/10 | 0 | 15.00 |
| 105 | D+3 | 3 | 1/10 | 2 | 12.00 |
| 106 | D+2 | 3 | 2/20 | 0 | 16.00 |
| 107 | D+2 | 4 | 3/30 | 3 | 14.40 |
| 108 | D+4 | 4 | 1/10 | 0 | 12.00 |
| 109 | D+3 | 5 | 2/20 | 0 | 20.00 |
| 110 | D+3 | 5 | 3/30 | 1 | 18.00 |
| 111 | D+5 | 6 | 1/10 | 0 | 15.00 |
| 112 | D+4 | 7 | 2/20 | 0 | 16.00 |

Purchase IDs below have purchased_at D 08:00; equal-time ordering uses ID DESC.
Every listed client uses its own active method except 301: method202 was active
when bought and was subsequently deactivated, preserving this historical record.

| Purchase | Screening | Client/method | Quantity | Unit | Total |
|---|---|---|---|---|---|
| 301 | 101 | 11/202 | 5 | 15.00 | 75.00 |
| 302 | 101 | 12/203 | 4 | 15.00 | 60.00 |
| 303 | 102 | 11/201 | 1 | 20.00 | 20.00 |
| 304 | 102 | 13/204 | 3 | 20.00 | 60.00 |
| 305 | 103 | 14/205 | 30 | 18.00 | 540.00 |
| 306 | 105 | 15/206 | 2 | 12.00 | 24.00 |
| 307 | 107 | 16/207 | 3 | 14.40 | 43.20 |
| 308 | 110 | 11/201 | 1 | 18.00 | 18.00 |

## Hand-computed Q1–Q5 oracles

Q1: all defaults at D 09:00 return 101,102,103,104,106,107,105,109,110,108,112,111
in that order. title "Movie 1", genre1, language2, date D+1,
time_from=time_to=10:00 returns 101,102 exactly once each.
Q2 client11 returns purchase IDs 308,303,301, with captured totals 18,20,75.
Searching or buying with client11 cannot expose client12's method203.

| Movie | Q3 tickets | Q3 revenue | Q5 offered seats | Q5 occupancy % |
|---|---|---|---|---|
| 1 | 13 | 215.00 | 30 | 43.33 |
| 2 | 30 | 540.00 | 40 | 75.00 |
| 3 | 2 | 24.00 | 30 | 6.67 |
| 4 | 3 | 43.20 | 40 | 7.50 |
| 5 | 1 | 18.00 | 50 | 2.00 |
| 6 | 0 | 0.00 | 10 | 0.00 |
| 7 | 0 | 0.00 | 20 | 0.00 |
| 8 | 0 | 0.00 | 0 | None/N/A |

Q3 default order: 2,1,4,3,5,6,7,8. minimum_tickets=3 yields 2,1,4.
Q4 order: theater3 (34 tickets, EUR601.20), theater1 (11, EUR159.00),
theater2 (4, EUR80.00). Global totals: 49 tickets, EUR840.20, 220 offered seats.
Report amounts come from purchases, not recomputed prices; zero rows stay visible.

## Focused boundary and failure fixtures

- Price tests use all four theater flags, both age categories, exact second
  anniversary, day before/after and leap-day mapping. Both-flags price23/18.40.
- Interval tests: 10:00 valid, 09:59 invalid, end23:59 valid, end next day invalid;
  adjacent intervals valid, one-minute overlap invalid. Starts at clock now fail.
- Role tests cover missing/forged/mismatched principals and client->admin denial.
  Email tests include surrounding spaces, mixed case and duplicate normalization.
- Client11 method202 is inactive; client12 method203 is foreign; missing999999
  is invalid. Invalid quantity includes 0, -1, 1.5 and True.
- Capacity contention starts at screening101 with history301+302=9 of10.
  Buyer11/method201 and buyer12/method203 each request1 using separate connections.
  A synchronization event signals first lock held; the second attempt starts
  before release, with bounded waits and evidence of lock contention.
  Expected: one new purchase, one CapacityError, sold10, history sum10.
- Rollback injects failures after purchase insert and after counter update.
  Fresh fixture each run: history/count unchanged, independent connection books
  successfully afterwards, proving locks released.
- Schedule race: two administrator transactions insert overlapping 90-minute
  starts in the same otherwise empty theater/date; exactly one succeeds.
- Payment race uses method201 and a fresh screening: booking-first may commit
  then deactivation succeeds; deactivation-first makes booking fail with no writes.
  Both orderings use bounded explicit synchronization, not sleep-only timing.
