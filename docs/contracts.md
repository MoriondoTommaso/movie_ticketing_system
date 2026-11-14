# T01 — Shared database and service contracts

Revision T01-r1, 14 November 2026. **Draft for joint review, not frozen.**
Policies: assumptions.md. Deterministic data and SQL examples: fixtures.md.
These are target interfaces, not claims about implemented modules.

## 1. Schema proposal

All tables use InnoDB, utf8mb4, restrictive deletes/updates, explicit constraints.
All columns below are NOT NULL unless marked nullable. IDs are unsigned INT,
auto-increment primary keys unless noted. Counts are signed INT with CHECKs.
Money is DECIMAL(12,2), dates DATE, local times DATETIME (no implicit timezone).
Booleans are BOOLEAN with CHECK IN (0,1).

| Table | Columns and keys |
|---|---|
| users | user_id PK; email VARCHAR(254) UNIQUE with utf8mb4_bin collation; password_hash VARCHAR(255); role VARCHAR(10) CHECK IN ('client','admin') |
| client_profiles | user_id PK/FK users; full_name VARCHAR(120); address VARCHAR(255) |
| payment_methods | payment_method_id PK; client_id FK client_profiles.user_id; payment_type VARCHAR(6) CHECK IN ('credit','debit'); card_number VARCHAR(19); billing_address VARCHAR(255); active BOOLEAN DEFAULT 1 |
| theaters | theater_id PK; capacity INT CHECK >0; supports_3d BOOLEAN; enhanced_sound BOOLEAN |
| languages | language_id PK; name VARCHAR(60) UNIQUE |
| genres | genre_id PK; name VARCHAR(60) UNIQUE |
| movies | movie_id PK; title VARCHAR(200); release_date DATE; runtime_minutes INT CHECK >0; original_language_id FK languages; description TEXT |
| movie_languages | movie_id FK movies; language_id FK languages; composite PK(movie_id,language_id) |
| movie_genres | movie_id FK movies; genre_id FK genres; composite PK(movie_id,genre_id) |
| screenings | screening_id PK; movie_id FK movies; theater_id FK theaters; language_id; starts_at DATETIME; sold_tickets INT DEFAULT 0 CHECK >=0; composite FK(movie_id,language_id) to movie_languages |
| purchases | purchase_id PK; client_id FK client_profiles.user_id; screening_id FK screenings; payment_method_id FK payment_methods; quantity INT CHECK >0; unit_price DECIMAL(12,2) CHECK >=0; total_amount DECIMAL(12,2) CHECK >=0 AND =unit_price*quantity; purchased_at DATETIME |

Services reject empty required strings and values longer than their schema limit.
Synthetic card normalization/format rules are in assumptions.md; SQL enforces
card length and digit-only format too. No card number is unique: clients may
add another synthetic method, even with the same number.

Cardinalities: user has 0..1 client profile (exactly 1 iff role=client).
Client has 0..N methods and purchases; each method has exactly one client.
Movie has exactly one original language, 1..N available languages and genres,
and 0..N screenings. Language/genre may have 0..N movies.
Theater has 0..N screenings. Each screening has one movie, theater and language,
and 0..N purchases. Each purchase has exactly one client, screening and method.
Each method has 0..N purchases. Minimum child counts require seed validation.

Indexes: screenings(theater_id,starts_at), screenings(movie_id,starts_at),
screenings(starts_at,screening_id), purchases(client_id,purchased_at,purchase_id),
purchases(screening_id), payment_methods(client_id,active). Foreign-key indexes
and association reverse lookup indexes support language/genre filtering.
T04 verifies actual query needs and ER correspondence; changes require consumers.

## 2. Shared values, errors and trust

`Role = Literal["client","admin"]`; `PaymentType = Literal["credit","debit"]`.
Dataclasses are frozen; collection returns are lists. IDs/quantities are Python
int (bool rejected); amounts Decimal; DATE date; DATETIME naive datetime in Rome.

| Value | Fields |
|---|---|
| Principal (auth.py) | user_id: int, role: Role; issued only after successful authentication |
| PaymentMethod (payments.py) | payment_method_id, client_id: int; payment_type: PaymentType; masked_number, billing_address: str; active: bool |
| ScreeningView (screenings.py) | screening_id, movie_id, theater_id: int; title, language: str; starts_at: datetime; unit_price: Decimal; available_seats: int; supports_3d, enhanced_sound: bool |
| LockedScreening (screenings.py) | screening_id, theater_id, capacity, sold_tickets, runtime_minutes: int; starts_at: datetime; release_date: date; supports_3d, enhanced_sound: bool |
| BookingReceipt (booking.py) | purchase_id, quantity: int; unit_price, total_amount: Decimal |
| PurchaseView (booking.py) | purchase_id, screening_id, quantity: int; title, language, masked_number: str; theater_id: int; starts_at, purchased_at: datetime; unit_price, total_amount: Decimal |
| MovieRevenue (analytics.py) | movie_id: int; title: str; tickets_sold: int; revenue: Decimal |
| TheaterRevenue (analytics.py) | theater_id, tickets_sold: int; revenue: Decimal |
| MovieOccupancy (analytics.py) | movie_id: int; title: str; tickets_sold, offered_seats: int; occupancy_percent: Decimal or None |

Shared exceptions live in database.py (no extra shared module):
`CinemaError` base; `ValidationError`, `AuthenticationError`,
`AuthorizationError`, `NotFoundError`, `CapacityError`, `DatabaseError`;
`RetryableDatabaseError(DatabaseError)` for lock timeout/deadlock.
Missing/foreign payment identifiers both raise ValidationError to avoid disclosure;
inactive methods also raise ValidationError. Invalid credentials and malformed
stored hashes raise the same AuthenticationError. Missing screening/movie/theater
raises NotFoundError. Overlap, time, language or format failures raise ValidationError.
Connector failures become DatabaseError without credentials, SQL values or card
numbers in interface messages. Services do not print or prompt.

A Principal is in-process trusted state, never deserialized from CLI fields.
Public services require a Principal, re-read its user/role from MySQL on their
connection, and deny a mismatch, missing user, or missing client profile.
`require_role` checks local shape/role; it alone does not establish provenance.
Only authentication issues session principals; no user-supplied role is trusted.
The same process's Python callers are not a sandbox/security boundary.

## 3. Connection, clock and transaction ownership

`database.connect(*, target: Literal["dev","test"]="dev") -> MySQLConnection`
returns a new connection, autocommit=False, REPEATABLE READ. Configuration is
DB_HOST/PORT/NAME/USER/PASSWORD or TEST_DB_HOST/PORT/NAME/USER/PASSWORD, never a
silent test-to-dev fallback. Caller closes connection and cursors.
`database.verify_principal(conn, principal, required_role) -> None` performs
the database-backed check above without commit/rollback or owning the connection.
T03 supplies lifecycle/guard tests; T07 supplies authentication/principal tests.

Public service signatures below take keyword-only `connect=database.connect`
as an injectable zero-argument factory. Tests pass a dedicated test-target factory.
Each public service opens/closes its own connection. Writes begin a transaction
before database principal checks, commit once on success and rollback on every
failure. Read services also end their transaction before closing; no leaked reads.
Helpers with `conn` borrow the caller's connection and never begin, commit,
rollback or close it. No shared global connection.

`Clock = Callable[[], datetime]` yields an aware instant;
`database.default_clock() -> datetime` uses UTC now.
Pure conversion is explicit: instant.astimezone(ZoneInfo("Europe/Rome")),
then strip tzinfo for database comparison. Reject naive injected clock values.
Capture now once per operation; booking captures it after the screening lock.
Scheduling captures it after the theater lock. This prevents stale eligibility
when a call waits for a lock. Purchase timestamp uses that same captured instant.

## 4. Operation signatures

Each public database operation below has the factory keyword above.
Date/time filter None means absent; filters combine with AND.

| Module | Operation and result |
|---|---|
| auth | authenticate(email: str, password: str) -> Principal |
| auth | require_role(principal: Principal, role: Role) -> None (pure guard) |
| payments | list_methods(principal) -> list[PaymentMethod], client only, includes inactive, ID ascending |
| payments | add_method(principal, payment_type, card_number: str, billing_address: str) -> PaymentMethod |
| payments | deactivate_method(principal, payment_method_id: int) -> None; owned inactive method is an idempotent no-op |
| payments | lock_valid_method(conn, principal, payment_method_id: int) -> PaymentMethod; client/owned/active, FOR UPDATE |
| pricing | calculate_unit_price(release_date: date, screening_date: date, supports_3d: bool, enhanced_sound: bool) -> Decimal; pure |
| schedule_rules | validate_interval(starts_at: datetime, runtime_minutes: int) -> datetime end; pure, minute precision/opening hours |
| schedule_rules | overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool; pure half-open rule |
| screenings | search_screenings(principal, *, title: str or None=None, genre_id: int or None=None, language_id: int or None=None, screening_date: date or None=None, time_from: time or None=None, time_to: time or None=None, clock=default_clock) -> list[ScreeningView]; client only |
| screenings | lock_screening(conn, screening_id: int) -> LockedScreening; FOR UPDATE/current read, availability computed from authoritative capacity |
| screenings | create_screening(principal, movie_id: int, theater_id: int, language_id: int, starts_at: datetime, *, clock=default_clock) -> int screening_id; admin only |
| screenings | list_schedule(principal, *, screening_date: date or None=None) -> list[ScreeningView]; admin, includes historical |
| screenings | list_capacity(principal, *, screening_date: date or None=None) -> list[ScreeningView]; same fields/order as schedule |
| booking | book_tickets(principal, screening_id: int, quantity: int, payment_method_id: int, *, clock=default_clock) -> BookingReceipt; client only |
| booking | list_purchases(principal) -> list[PurchaseView]; client only, purchased_at DESC then purchase_id DESC |
| analytics | revenue_by_movie(principal, *, minimum_tickets: int=0) -> list[MovieRevenue]; admin only |
| analytics | revenue_by_theater(principal) -> list[TheaterRevenue]; admin only |
| analytics | occupancy_by_movie(principal) -> list[MovieOccupancy]; admin only |

Search title is a literal substring (escape SQL LIKE wildcards); genre/language
use exact IDs chosen from catalog. Add screenings catalog operations:
`list_movies(principal) -> list[MovieOption(movie_id:int,title:str)]`,
`list_theaters(principal) -> list[TheaterOption(theater_id:int,capacity:int)]`,
`list_languages(principal, *, movie_id:int or None=None) ->
list[LanguageOption(language_id:int,name:str)]`,
`list_genres(principal) -> list[GenreOption(genre_id:int,name:str)]`.
These accept either stored role and the same factory; order by ID.
If movie_id is supplied, languages are limited to its available languages.
Unknown movie_id raises NotFoundError. Catalog dataclasses live in screenings.py.
SQL bindings/output columns are specified below; search date/time is local Rome.
Reject time_from > time_to; overnight ranges are not supported.

## 5. Write sequences and SQL artifact

Booking: validate quantity; begin; verify principal; lock screening; capture now;
reject started/capacity; lock and validate payment; calculate price; insert purchase;
update counter; commit. Roll back any failure, including after either write.
Booking helpers borrow this same connection. No automatic retry, input prompt,
or external operation while locks are held.

Scheduling: begin; verify admin; lock theater; capture now; read movie/language;
validate future interval; current/locking overlap read; insert; commit.
Overlap is existing_start < new_end AND existing_end > new_start.
Deactivation: begin; verify client; lock owned payment; set inactive; commit.
Whichever locks a payment first establishes booking/deactivation ordering.

`queries.sql` will contain exactly Q1–Q5. Named connector placeholders use
`%(name)s` and cursor.execute(statement, mapping), never string interpolation.

| Query | Binding names/types | Output columns / order |
|---|---|---|
| Q1 | title_pattern str/None (escaped literal surrounded by %); genre_id int/None; language_id int/None; screening_date date/None; time_from/time_to time/None; now_local datetime | ScreeningView columns; starts_at ASC, screening_id ASC; require starts_at > now_local; use EXISTS for genre to avoid duplicates |
| Q2 | client_id int from verified principal | PurchaseView columns; purchased_at DESC, purchase_id DESC |
| Q3 | minimum_tickets int >=0 | MovieRevenue columns; revenue DESC, movie_id ASC; LEFT JOIN, GROUP BY, HAVING ticket sum >= minimum_tickets |
| Q4 | none | TheaterRevenue columns; revenue DESC, theater_id ASC; LEFT JOIN/GROUP BY |
| Q5 | none | MovieOccupancy columns; movie_id ASC; purchases pre-aggregated per screening then sum capacity once; NULLIF denominator; two-decimal percent |

Revenue uses captured totals, never current prices. Q5 derives sold quantities
from purchases (tests reconcile counters), not purchase row counts. Preserve all
movies/theaters including zero sales; no screenings yields offered_seats=0 and
occupancy_percent=None. Reports have no implicit future-only restriction.
