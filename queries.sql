-- Q1: future screening search. Bind the named parameters with MySQL Connector.
-- NULL omits a filter. Escape !, %, and _ with ! in the title substring.
-- Keep this standalone SQL projection in parity with src.pricing (tested).
SELECT s.screening_id, m.movie_id, t.theater_id, m.title, l.name AS language,
       s.starts_at,
       CAST(
           (15 + 5 * t.supports_3d + 3 * t.enhanced_sound) *
           CASE WHEN DATE(s.starts_at) > DATE_ADD(m.release_date, INTERVAL 2 YEAR)
                THEN 0.80 ELSE 1.00 END
           AS DECIMAL(12, 2)
       ) AS unit_price,
       t.capacity - s.sold_tickets AS available_seats,
       t.supports_3d, t.enhanced_sound
FROM screenings s
JOIN movies m ON m.movie_id = s.movie_id
JOIN theaters t ON t.theater_id = s.theater_id
JOIN languages l ON l.language_id = s.language_id
WHERE s.starts_at > %(now_local)s
  AND (%(title_pattern)s IS NULL OR m.title LIKE %(title_pattern)s ESCAPE '!')
  AND (%(genre_id)s IS NULL OR EXISTS (
      SELECT 1 FROM movie_genres mg
      WHERE mg.movie_id = s.movie_id AND mg.genre_id = %(genre_id)s
  ))
  AND (%(language_id)s IS NULL OR s.language_id = %(language_id)s)
  AND (%(screening_date)s IS NULL OR DATE(s.starts_at) = %(screening_date)s)
  AND (%(time_from)s IS NULL OR TIME(s.starts_at) >= %(time_from)s)
  AND (%(time_to)s IS NULL OR TIME(s.starts_at) <= %(time_to)s)
ORDER BY s.starts_at, s.screening_id;

-- Q2: purchase history. Bind client_id from the verified client principal.
SELECT p.purchase_id, p.screening_id, p.quantity, m.title, l.name AS language,
       CONCAT('****', RIGHT(pm.card_number, 4)) AS masked_number, s.theater_id,
       s.starts_at, p.purchased_at, p.unit_price, p.total_amount
FROM purchases p
JOIN screenings s ON s.screening_id = p.screening_id
JOIN movies m ON m.movie_id = s.movie_id
JOIN languages l ON l.language_id = s.language_id
JOIN payment_methods pm ON pm.payment_method_id = p.payment_method_id
WHERE p.client_id = %(client_id)s
ORDER BY p.purchased_at DESC, p.purchase_id DESC;
