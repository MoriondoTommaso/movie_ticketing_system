-- T06 / approved T01-r1 fixture oracle. Anchor D = 2026-11-23, Europe/Rome.
-- Load ONCE after schema.sql into an empty isolated database. Never reset here.
-- Explicit dates: no CURRENT_DATE dependency. See docs/fixtures.md for rebasing.
-- Synthetic credentials: scrypt n=16384/r=8/p=1, 16-byte random salts, 32-byte keys.
START TRANSACTION;

INSERT INTO users (user_id, email, password_hash, role) VALUES
(1, 'admin@example.test', 'scrypt$16384$8$1$f595c94ab5a035d1c642b8a611d2df2a$3fc5e5174da81330e9d963fe1e058e734fc6d3398f62bc0cb13f9281041b0a88', 'admin'),
(11, 'client11@example.test', 'scrypt$16384$8$1$403e8255fcbca25978c9c0d69c5a1a3f$5a69a8bfad7ec80afcbc277583c3901273a209903079020416b2c2e42b318b26', 'client'),
(12, 'client12@example.test', 'scrypt$16384$8$1$6bdf204877b2e7b1cd8a01ecb8db40a7$562196ceb1c5b8b197274663b189b2f3447711f06d92878078203f984367d13c', 'client'),
(13, 'client13@example.test', 'scrypt$16384$8$1$c5940882bda36cfc3308a99b0b125510$69b90cd558d7fdeb641ca0d5d9a6cea9a249779b6a40e3def7800ad1e6c0894b', 'client'),
(14, 'client14@example.test', 'scrypt$16384$8$1$76a85e5d1bf5f50660c31e0eae26a253$5ba898b9357ed14a670fba585eac15e6d8bf34ff3359163edf86d2194fc19e17', 'client'),
(15, 'client15@example.test', 'scrypt$16384$8$1$4dfd069765c3923d4766500fc1d437a6$87008c53367b9047b40f8e2d7fb9f32a433e15a5ddaa363976d4cc07c9a26084', 'client'),
(16, 'client16@example.test', 'scrypt$16384$8$1$4bae17db22d4c87e9a7b1d38c4c19252$67c6b9f7cde7b2391c80b93802ee866d6f5c1fc0ab94be4657be8babaa0c13ee', 'client');

INSERT INTO client_profiles (user_id, full_name, address) VALUES
(11, 'Demo Client Eleven', '11 Fictional Lane, Example City'),
(12, 'Demo Client Twelve', '12 Fictional Lane, Example City'),
(13, 'Demo Client Thirteen', '13 Fictional Lane, Example City'),
(14, 'Demo Client Fourteen', '14 Fictional Lane, Example City'),
(15, 'Demo Client Fifteen', '15 Fictional Lane, Example City'),
(16, 'Demo Client Sixteen', '16 Fictional Lane, Example City');

INSERT INTO payment_methods
(payment_method_id, client_id, payment_type, card_number, billing_address, active) VALUES
(201, 11, 'credit', '0000000000000201', '11 Fictional Lane, Example City', 1),
(202, 11, 'debit', '0000000000000202', '11 Fictional Lane, Example City', 0),
(203, 12, 'debit', '0000000000000203', '12 Fictional Lane, Example City', 1),
(204, 13, 'credit', '0000000000000204', '13 Fictional Lane, Example City', 1),
(205, 14, 'debit', '0000000000000205', '14 Fictional Lane, Example City', 1),
(206, 15, 'credit', '0000000000000206', '15 Fictional Lane, Example City', 1),
(207, 16, 'debit', '0000000000000207', '16 Fictional Lane, Example City', 1);

INSERT INTO theaters (theater_id, capacity, supports_3d, enhanced_sound) VALUES
(1, 10, 0, 0), (2, 20, 1, 0), (3, 30, 0, 1);
INSERT INTO languages (language_id, name) VALUES (1, 'Italian'), (2, 'English');
INSERT INTO genres (genre_id, name) VALUES (1, 'Drama'), (2, 'Comedy');
INSERT INTO movies
(movie_id, title, release_date, runtime_minutes, original_language_id, description) VALUES
(1, 'Fixture Movie 1', '2026-11-23', 90, 2, 'Synthetic ensemble drama and comedy.'),
(2, 'Fixture Movie 2', '2026-11-23', 90, 2, 'Synthetic sold-out premiere drama.'),
(3, 'Fixture Movie 3', '2023-11-23', 90, 2, 'Synthetic classic drama and comedy.'),
(4, 'Fixture Movie 4', '2023-11-23', 90, 2, 'Synthetic classic sound showcase.'),
(5, 'Fixture Movie 5', '2026-11-23', 90, 2, 'Synthetic contemporary drama.'),
(6, 'Fixture Movie 6', '2026-11-23', 90, 2, 'Synthetic unsold premiere drama.'),
(7, 'Fixture Movie 7', '2023-11-23', 90, 2, 'Synthetic unsold classic drama.'),
(8, 'Fixture Movie 8', '2026-11-23', 90, 2, 'Synthetic unscheduled drama.');
INSERT INTO movie_languages (movie_id, language_id) VALUES
(1,1), (1,2), (2,1), (2,2), (3,1), (3,2), (4,1), (4,2),
(5,1), (5,2), (6,1), (6,2), (7,1), (7,2), (8,1), (8,2);
INSERT INTO movie_genres (movie_id, genre_id) VALUES
(1,1), (1,2), (2,1), (3,1), (3,2), (4,1), (5,1), (6,1), (7,1), (8,1);

INSERT INTO screenings
(screening_id, movie_id, theater_id, language_id, starts_at, sold_tickets) VALUES
(101, 1, 1, 2, '2026-11-24 10:00:00', 9),
(102, 1, 2, 2, '2026-11-24 10:00:00', 4),
(103, 2, 3, 2, '2026-11-24 10:00:00', 30),
(104, 2, 1, 2, '2026-11-25 10:00:00', 0),
(105, 3, 1, 2, '2026-11-26 10:00:00', 2),
(106, 3, 2, 2, '2026-11-25 10:00:00', 0),
(107, 4, 3, 2, '2026-11-25 10:00:00', 3),
(108, 4, 1, 2, '2026-11-27 10:00:00', 0),
(109, 5, 2, 2, '2026-11-26 10:00:00', 0),
(110, 5, 3, 2, '2026-11-26 10:00:00', 1),
(111, 6, 1, 2, '2026-11-28 10:00:00', 0),
(112, 7, 2, 2, '2026-11-27 10:00:00', 0);

-- Method 202 was active for purchase 301 and subsequently deactivated.
INSERT INTO purchases
(purchase_id, client_id, screening_id, payment_method_id, quantity,
 unit_price, total_amount, purchased_at) VALUES
(301, 11, 101, 202, 5, 15.00, 75.00, '2026-11-23 08:00:00'),
(302, 12, 101, 203, 4, 15.00, 60.00, '2026-11-23 08:00:00'),
(303, 11, 102, 201, 1, 20.00, 20.00, '2026-11-23 08:00:00'),
(304, 13, 102, 204, 3, 20.00, 60.00, '2026-11-23 08:00:00'),
(305, 14, 103, 205, 30, 18.00, 540.00, '2026-11-23 08:00:00'),
(306, 15, 105, 206, 2, 12.00, 24.00, '2026-11-23 08:00:00'),
(307, 16, 107, 207, 3, 14.40, 43.20, '2026-11-23 08:00:00'),
(308, 11, 110, 201, 1, 18.00, 18.00, '2026-11-23 08:00:00');
COMMIT;
