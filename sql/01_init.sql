CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS links (
    movie_id INTEGER,
    imdb_id INTEGER,
    tmdb_id INTEGER PRIMARY KEY,
    FOREIGN KEY (movie_id) REFERENCES movies (movie_id)
);

CREATE TABLE IF NOT EXISTS tmdb_data (
    tmdb_id INTEGER PRIMARY KEY,
    director TEXT,
    budget INTEGER,
    cumulative_worldwide_gross INTEGER,
    runtime INTEGER,
    FOREIGN KEY (tmdb_id) REFERENCES links (tmdb_id)
);

CREATE TABLE IF NOT EXISTS ratings (
    user_id INTEGER,
    movie_id INTEGER,
    rating REAL,
    timestamp INTEGER,
    FOREIGN KEY (movie_id) REFERENCES movies (movie_id)
);