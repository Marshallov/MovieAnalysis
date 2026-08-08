import sqlite3
from etl.links import LinksETL
from etl.ratings import RatingsETL

class MovieETLPipeline:
    def __init__(self, db_path='dwh.sqlite'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def init_database(self):
        with open('sql/01_init.sql', 'r') as f:
            self.cursor.executescript(f.read())
        
        self.conn.commit()
        print("The dwh.sqlite database and tables have been successfully created!")

    def run_pipeline(self):
        """The main method that starts the entire boot process"""
        
        print("Run ETL-pipeline")

        links_etl = LinksETL(db_path='dwh.sqlite', path_links='data/links.csv', path_movies='data/movies.csv')
        links_etl.load_movies_to_db()
        links_etl.load_links_to_db()
        links_etl.load_tmdb_data_to_db()
        
        ratings_etl = RatingsETL(db_path='dwh.sqlite', path_ratings='data/ratings.csv', count_line=100_836)
        ratings_etl.load_ratings_to_db()

        print("Formation of analytical SQL-windows (Data Marts)")

        with open('sql/02_marts.sql', 'r', encoding='utf-8') as f:
            self.cursor.executescript(f.read())
        self.conn.commit()
        
        print("The ETL pipeline has completed successfully!")

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    pipeline = MovieETLPipeline()
    try:
        pipeline.init_database()
        pipeline.run_pipeline()
    finally:
        pipeline.close()