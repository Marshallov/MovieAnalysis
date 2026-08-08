-- Movie-Based Videos and TMDB (Links & TMDB)

CREATE VIEW IF NOT EXISTS mart_top_directors AS
SELECT 
    director,
    COUNT(tmdb_id) AS movies_count
FROM tmdb_data
WHERE director IS NOT NULL AND director != 'Unknown'
GROUP BY director
ORDER BY movies_count DESC;

CREATE VIEW IF NOT EXISTS mart_most_expensive AS
SELECT 
    m.title,
    t.budget
FROM tmdb_data t
JOIN links l ON t.tmdb_id = l.tmdb_id
JOIN movies m ON l.movie_id = m.movie_id
WHERE t.budget > 0
ORDER BY t.budget DESC;

CREATE VIEW IF NOT EXISTS mart_most_profitable AS
SELECT 
    m.title,
    (t.cumulative_worldwide_gross - t.budget) AS profit
FROM tmdb_data t
JOIN links l ON t.tmdb_id = l.tmdb_id
JOIN movies m ON l.movie_id = m.movie_id
WHERE t.budget > 0 AND t.cumulative_worldwide_gross > 0
ORDER BY profit DESC;

CREATE VIEW IF NOT EXISTS mart_longest_movies AS
SELECT 
    m.title,
    t.runtime
FROM tmdb_data t
JOIN links l ON t.tmdb_id = l.tmdb_id
JOIN movies m ON l.movie_id = m.movie_id
WHERE t.runtime > 0
ORDER BY t.runtime DESC;

CREATE VIEW IF NOT EXISTS mart_top_cost_per_minute AS
SELECT 
    m.title,
    ROUND(CAST(t.budget AS REAL) / t.runtime, 2) AS cost_per_minute
FROM tmdb_data t
JOIN links l ON t.tmdb_id = l.tmdb_id
JOIN movies m ON l.movie_id = m.movie_id
WHERE t.runtime > 0 AND t.budget > 0
ORDER BY cost_per_minute DESC;

CREATE VIEW IF NOT EXISTS mart_highest_roi AS
SELECT 
    m.title,
    ROUND(((CAST(t.cumulative_worldwide_gross AS REAL) - t.budget) / t.budget) * 100, 2) AS roi_percentage
FROM tmdb_data t
JOIN links l ON t.tmdb_id = l.tmdb_id
JOIN movies m ON l.movie_id = m.movie_id
WHERE t.budget > 0 AND t.cumulative_worldwide_gross > 0
ORDER BY roi_percentage DESC;

CREATE VIEW IF NOT EXISTS mart_biggest_flops AS
SELECT 
    m.title,
    (t.budget - t.cumulative_worldwide_gross) AS absolute_loss
FROM tmdb_data t
JOIN links l ON t.tmdb_id = l.tmdb_id
JOIN movies m ON l.movie_id = m.movie_id
WHERE t.budget > 0 
  AND t.cumulative_worldwide_gross > 0 
  AND t.budget > t.cumulative_worldwide_gross
ORDER BY absolute_loss DESC;

CREATE VIEW IF NOT EXISTS mart_top_earning_directors AS
SELECT 
    director,
    SUM(cumulative_worldwide_gross - budget) AS total_profit
FROM tmdb_data
WHERE budget > 0 
  AND cumulative_worldwide_gross > 0 
  AND cumulative_worldwide_gross > budget
  AND director IS NOT NULL 
  AND director != 'Unknown'
GROUP BY director
ORDER BY total_profit DESC;



-- SHOWCASES BY RATINGS

CREATE VIEW IF NOT EXISTS mart_ratings_by_year AS
SELECT 
    strftime('%Y', datetime(timestamp, 'unixepoch')) AS rating_year, 
    COUNT(rating) AS ratings_count
FROM ratings
GROUP BY rating_year
ORDER BY rating_year ASC;

CREATE VIEW IF NOT EXISTS mart_ratings_distribution AS
SELECT 
    rating, 
    COUNT(rating) AS ratings_count
FROM ratings
GROUP BY rating
ORDER BY rating ASC;

CREATE VIEW IF NOT EXISTS mart_top_by_num_of_ratings AS
SELECT 
    m.title, 
    COUNT(r.rating) AS num_of_ratings
FROM ratings r
JOIN movies m ON r.movie_id = m.movie_id
GROUP BY r.movie_id, m.title
ORDER BY num_of_ratings DESC;

CREATE VIEW IF NOT EXISTS mart_top_by_avg_rating AS
SELECT 
    m.title, 
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(r.rating) AS total_ratings
FROM ratings r
JOIN movies m ON r.movie_id = m.movie_id
GROUP BY r.movie_id, m.title
ORDER BY avg_rating DESC;

CREATE VIEW IF NOT EXISTS mart_hidden_gems AS
SELECT 
    m.title, 
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(r.rating) AS rating_count
FROM ratings r
JOIN movies m ON r.movie_id = m.movie_id
GROUP BY r.movie_id, m.title
HAVING rating_count BETWEEN 10 AND 50
ORDER BY avg_rating DESC;

CREATE VIEW IF NOT EXISTS mart_polarizing_movies AS
SELECT 
    m.title, 
    ROUND(SUM(CASE WHEN r.rating <= 1.5 OR r.rating >= 4.5 THEN 1.0 ELSE 0.0 END) / COUNT(r.rating), 2) AS polarizing_ratio,
    COUNT(r.rating) AS total_ratings
FROM ratings r
JOIN movies m ON r.movie_id = m.movie_id
GROUP BY r.movie_id, m.title
HAVING total_ratings >= 30
ORDER BY polarizing_ratio DESC;

CREATE VIEW IF NOT EXISTS mart_top_marathoners AS
SELECT 
    user_id,
    MAX(ratings_given) AS max_ratings_in_a_day
FROM (
    SELECT 
        user_id,
        date(timestamp, 'unixepoch') AS activity_date,
        COUNT(movie_id) AS ratings_given
    FROM ratings
    GROUP BY user_id, activity_date
) 
GROUP BY user_id
ORDER BY max_ratings_in_a_day DESC;