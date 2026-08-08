import sqlite3

class RatingsETL:
    def __init__(self, db_path='dwh.sqlite', path_ratings='data/ratings.csv', count_line=1000):
        self.db_path = db_path
        self.path_ratings = path_ratings
        self.count_line = count_line

    def load_ratings_to_db(self):
        """Reading CSV ratings and loading them into SQLite databases"""
        
        def process_rating(line):
            fields = line.strip().split(',')
            return (int(fields[0]), int(fields[1]), float(fields[2]), int(fields[3]))

        with open(self.path_ratings, 'r', encoding='utf-8') as file:
            file.readline()
            
            extracted_data = tuple(map(process_rating, file.readlines()[:self.count_line]))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES (?, ?, ?, ?)",
                extracted_data
            )
            conn.commit()
            print(f"Successfully loaded {len(extracted_data)} ratings into the ratings table.")