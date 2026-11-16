-- T04 / T01-r1. Load once into an EMPTY, already-created MySQL 8.4 database.
-- No DROP, CREATE DATABASE, USE, seed rows or session constraint disabling.
-- IDs are unsigned, counts signed; money is captured as DECIMAL, not FLOAT.
-- DATETIME values are local Europe/Rome wall times (conversion is in services).

CREATE TABLE users (
    user_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(254) COLLATE utf8mb4_bin NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL,
    CONSTRAINT uq_user_email UNIQUE (email),
    CONSTRAINT ck_user_role CHECK (
        role COLLATE utf8mb4_0900_as_cs IN ('client', 'admin')
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE client_profiles (
    user_id INT UNSIGNED PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    address VARCHAR(255) NOT NULL,
    CONSTRAINT fk_client_user FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE payment_methods (
    payment_method_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id INT UNSIGNED NOT NULL,
    payment_type VARCHAR(6) NOT NULL,
    card_number VARCHAR(19) NOT NULL,
    billing_address VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1,
    CONSTRAINT ck_payment_type CHECK (
        payment_type COLLATE utf8mb4_0900_as_cs IN ('credit', 'debit')
    ),
    CONSTRAINT ck_payment_card CHECK (
        CHAR_LENGTH(card_number) BETWEEN 13 AND 19
        AND NOT REGEXP_LIKE(card_number, '[^0-9]', 'c')
    ),
    CONSTRAINT ck_payment_active CHECK (active IN (0, 1)),
    CONSTRAINT fk_payment_client FOREIGN KEY (client_id)
        REFERENCES client_profiles (user_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE theaters (
    theater_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    capacity INT NOT NULL,
    supports_3d BOOLEAN NOT NULL,
    enhanced_sound BOOLEAN NOT NULL,
    CONSTRAINT ck_theater_capacity CHECK (capacity > 0),
    CONSTRAINT ck_theater_3d CHECK (supports_3d IN (0, 1)),
    CONSTRAINT ck_theater_sound CHECK (enhanced_sound IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE languages (
    language_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    CONSTRAINT uq_language_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE genres (
    genre_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    CONSTRAINT uq_genre_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE movies (
    movie_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    release_date DATE NOT NULL,
    runtime_minutes INT NOT NULL,
    original_language_id INT UNSIGNED NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT ck_movie_runtime CHECK (runtime_minutes > 0),
    CONSTRAINT fk_movie_original_language FOREIGN KEY (original_language_id)
        REFERENCES languages (language_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE movie_languages (
    movie_id INT UNSIGNED NOT NULL,
    language_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (movie_id, language_id),
    CONSTRAINT fk_available_movie FOREIGN KEY (movie_id)
        REFERENCES movies (movie_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_available_language FOREIGN KEY (language_id)
        REFERENCES languages (language_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE movie_genres (
    movie_id INT UNSIGNED NOT NULL,
    genre_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    CONSTRAINT fk_genre_movie FOREIGN KEY (movie_id)
        REFERENCES movies (movie_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_movie_genre FOREIGN KEY (genre_id)
        REFERENCES genres (genre_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE screenings (
    screening_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    movie_id INT UNSIGNED NOT NULL,
    theater_id INT UNSIGNED NOT NULL,
    language_id INT UNSIGNED NOT NULL,
    starts_at DATETIME NOT NULL,
    sold_tickets INT NOT NULL DEFAULT 0,
    CONSTRAINT ck_screening_sold CHECK (sold_tickets >= 0),
    CONSTRAINT fk_screening_available_language FOREIGN KEY (movie_id, language_id)
        REFERENCES movie_languages (movie_id, language_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_screening_theater FOREIGN KEY (theater_id)
        REFERENCES theaters (theater_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE purchases (
    purchase_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id INT UNSIGNED NOT NULL,
    screening_id INT UNSIGNED NOT NULL,
    payment_method_id INT UNSIGNED NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    purchased_at DATETIME NOT NULL,
    CONSTRAINT ck_purchase_quantity CHECK (quantity > 0),
    CONSTRAINT ck_purchase_price CHECK (unit_price >= 0),
    CONSTRAINT ck_purchase_total CHECK (
        total_amount >= 0 AND total_amount = unit_price * quantity
    ),
    CONSTRAINT fk_purchase_client FOREIGN KEY (client_id)
        REFERENCES client_profiles (user_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_purchase_screening FOREIGN KEY (screening_id)
        REFERENCES screenings (screening_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_purchase_payment FOREIGN KEY (payment_method_id)
        REFERENCES payment_methods (payment_method_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Enforcement boundary (no cross-table CHECK claims):
-- Seed/auth: client profile exists iff role=client; normalized emails/passwords.
-- Seed: each movie has >=1 language and genre, original language is available.
-- Booking: stored role, client/payment ownership and active state; screening-row
-- lock protects capacity and counter/purchase reconciliation; seed verifies sums.
-- Scheduling: theater-row lock prevents overlap; service validates opening hours,
-- minute precision and future starts. SQL FKs enforce movie-language membership.
-- Services reject empty required strings, excessive lengths and bool quantities.
-- Retain purchase history: deactivate methods, never delete referenced records.
