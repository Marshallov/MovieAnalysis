import sqlite3
import pytest


class TestLinksTMDB:

    @pytest.fixture
    def db(self):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        with open("sql/01_init.sql", "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

        with open("sql/02_marts.sql", "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

        cursor.executescript(
            """
            INSERT INTO movies VALUES
                (1, 'Inception'),
                (2, 'The Room'),
                (3, 'Avatar'),
                (4, 'Budget Flop Film');

            INSERT INTO links VALUES
                (1, NULL, 101),
                (2, NULL, 102),
                (3, NULL, 103),
                (4, NULL, 104);

            INSERT INTO tmdb_data VALUES
                (101, 'Christopher Nolan', 160, 800, 148),
                (102, 'Tommy Wiseau', 60, 5, 99),
                (103, 'Christopher Nolan', 230, 2900, 162),
                (104, 'Unknown', 500, 100, 120);
            """
        )

        conn.commit()
        yield cursor
        conn.close()

    @pytest.mark.parametrize(
        "query, expected",
        [
            (
                "SELECT director, movies_count FROM mart_top_directors",
                [
                    ('Christopher Nolan', 2),
                    ('Tommy Wiseau', 1),
                ],
            ),
            (
                "SELECT title, budget FROM mart_most_expensive",
                [
                    ('Budget Flop Film', 500),
                    ('Avatar', 230),
                    ('Inception', 160),
                    ('The Room', 60),
                ],
            ),
            (
                "SELECT title, profit FROM mart_most_profitable",
                [
                    ('Avatar', 2670),
                    ('Inception', 640),
                    ('The Room', -55),
                    ('Budget Flop Film', -400),
                ],
            ),
            (
                "SELECT title, runtime FROM mart_longest_movies",
                [
                    ('Avatar', 162),
                    ('Inception', 148),
                    ('Budget Flop Film', 120),
                    ('The Room', 99),
                ],
            ),
            (
                "SELECT title, absolute_loss FROM mart_biggest_flops",
                [
                    ('Budget Flop Film', 400),
                    ('The Room', 55),
                ],
            ),
            (
                "SELECT director, total_profit FROM mart_top_earning_directors",
                [
                    ('Christopher Nolan', 3310),
                ],
            ),
        ],
        ids=[
            "top_directors",
            "most_expensive",
            "most_profitable",
            "longest_movies",
            "biggest_flops",
            "top_earning_directors",
        ],
    )
    def test_views(self, db, query, expected):
        db.execute(query)
        rows = db.fetchall()

        assert rows == expected

        if len(rows) > 1:
            values = [row[1] for row in rows]
            assert values == sorted(values, reverse=True)

    @pytest.mark.parametrize(
        "query, expected",
        [
            (
                "SELECT title, cost_per_minute FROM mart_top_cost_per_minute",
                [
                    ('Budget Flop Film', 4.17),
                    ('Avatar', 1.42),
                    ('Inception', 1.08),
                    ('The Room', 0.61),
                ],
            ),
            (
                "SELECT title, roi_percentage FROM mart_highest_roi",
                [
                    ('Avatar', 1160.87),
                    ('Inception', 400.00),
                    ('Budget Flop Film', -80.00),
                    ('The Room', -91.67),
                ],
            ),
        ],
        ids=[
            "top_cost_per_minute",
            "highest_roi",
        ],
    )
    def test_views_with_float(self, db, query, expected):
        db.execute(query)
        rows = db.fetchall()

        assert len(rows) == len(expected)

        for (title, value), (exp_title, exp_value) in zip(rows, expected):
            assert title == exp_title
            assert value == pytest.approx(exp_value, abs=0.01)

        values = [row[1] for row in rows]
        assert values == sorted(values, reverse=True)

    def test_top_directors_excludes_unknown(self, db):
        db.execute("SELECT director FROM mart_top_directors")
        directors = [row[0] for row in db.fetchall()]

        assert "Unknown" not in directors

    def test_top_directors_columns(self, db):
        db.execute("PRAGMA table_info(mart_top_directors)")
        columns = [col[1] for col in db.fetchall()]

        assert columns == ["director", "movies_count"]