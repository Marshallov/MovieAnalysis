import sqlite3
import pytest


class TestRatingsMarts:
    
    @pytest.fixture
    def db(self):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        with open("sql/01_init.sql", "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

        with open("sql/02_marts.sql", "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

        cursor.executescript("""
            INSERT INTO movies (movie_id, title) VALUES
                (1, 'Interstellar'),  
                (2, 'Dune'),           
                (3, 'Whiplash'),       
                (4, 'Short Film');     
        """)

        ratings = []
        
        for i in range(1, 16):
            ratings.append((i, 1, 1.0, 1577836800))  
        for i in range(16, 31):
            ratings.append((i, 1, 5.0, 1577836800))
        for i in range(31, 62):
            ratings.append((i, 2, 3.2, 1577836800))
        for i in range(62, 77):
            ratings.append((i, 3, 4.5, 1609459200))  
        for i in range(77, 82):
            ratings.append((i, 4, 4.0, 1609459200))
        for i in range(12):
            ratings.append((999, 100 + i, 4.0, 1640995200)) 
        for i in range(4):
            ratings.append((999, 112 + i, 3.5, 1641081600))  
        for i in range(8):
            ratings.append((888, 100 + i, 5.0, 1640995200))

        cursor.executemany(
            "INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES (?, ?, ?, ?)",
            ratings
        )

        conn.commit()
        yield cursor
        conn.close()


    @pytest.mark.parametrize(
        "query, expected",
        [
            (
                "SELECT rating_year, ratings_count FROM mart_ratings_by_year",
                [
                    ('2020', 61),  
                    ('2021', 20),  
                    ('2022', 24), 
                ],
            ),
            (
                "SELECT rating, ratings_count FROM mart_ratings_distribution",
                [
                    (1.0, 15),
                    (3.2, 31),
                    (3.5, 4),
                    (4.0, 17),  
                    (4.5, 15),
                    (5.0, 23),  
                ],
            ),
            (
                "SELECT title, num_of_ratings FROM mart_top_by_num_of_ratings",
                [
                    ('Dune', 31),
                    ('Interstellar', 30),
                    ('Whiplash', 15),
                    ('Short Film', 5),
                ],
            ),
            (
                "SELECT user_id, max_ratings_in_a_day FROM mart_top_marathoners LIMIT 2",
                [
                    (999, 12),  
                    (888, 8),  
                ],
            ),
        ],
        ids=[
            "ratings_by_year",
            "ratings_distribution",
            "top_by_num_of_ratings",
            "top_marathoners",
        ]
    )
    def test_exact_matches(self, db, query, expected):
        db.execute(query)
        rows = db.fetchall()
        assert rows == expected


    @pytest.mark.parametrize(
        "query, expected",
        [
            (
                "SELECT title, avg_rating, total_ratings FROM mart_top_by_avg_rating",
                [
                    ('Whiplash', 4.5, 15),
                    ('Short Film', 4.0, 5),
                    ('Dune', 3.2, 31),
                    ('Interstellar', 3.0, 30),
                ],
            ),
            (
                "SELECT title, avg_rating, rating_count FROM mart_hidden_gems",
                [
                    ('Whiplash', 4.5, 15),
                    ('Dune', 3.2, 31),
                    ('Interstellar', 3.0, 30),
                ],
            ),
            (
                "SELECT title, polarizing_ratio, total_ratings FROM mart_polarizing_movies",
                [
                    ('Interstellar', 1.0, 30), 
                    ('Dune', 0.0, 31),          
                ],
            ),
        ],
        ids=[
            "top_by_avg_rating",
            "hidden_gems",
            "polarizing_movies",
        ]
    )
    def test_float_metrics(self, db, query, expected):
        db.execute(query)
        rows = db.fetchall()

        assert len(rows) == len(expected)

        for row, exp in zip(rows, expected):
            assert row[0] == exp[0]                           
            assert row[1] == pytest.approx(exp[1], abs=0.01)  
            assert row[2] == exp[2]                           