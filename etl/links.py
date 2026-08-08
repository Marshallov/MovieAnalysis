import sqlite3
import requests
from bs4 import BeautifulSoup
import re

class LinksETL:
    def __init__(self, db_path='dwh.sqlite', path_links='data/links.csv', path_movies='data/movies.csv', count_line=100):
        self.db_path = db_path
        self.path_links = path_links
        self.path_movies = path_movies
        self.count_line = count_line
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
        }

    @staticmethod
    def to_int(number):
        try:
            return int(number)
        except Exception:
            return 0

    def load_movies_to_db(self):
        """Reading movies.csv and loading it into the database"""
        def process_movie(line):
            movie_id_str, rest = line.split(',', 1)
            title, _ = rest.rsplit(',', 1)
            return (int(movie_id_str), title.strip('"'))

        with open(self.path_movies, 'r', encoding='utf-8') as f:
            f.readline()
            lines = f.readlines()
            non_empty_lines = tuple(filter(lambda l: l.strip(), lines))
            extracted_data = tuple(map(process_movie, non_empty_lines))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO movies (movie_id, title) VALUES (?, ?)",
                extracted_data
            )
            conn.commit()
            print(f"Loaded {len(extracted_data)} movies into the movies table.")

    def load_links_to_db(self):
        """Reading links.csv and loading it into the database"""
        def process_link_line(line):
            field = line.strip().split(',')
            return (self.to_int(field[0]), self.to_int(field[1]), self.to_int(field[2]))

        with open(self.path_links, 'r', encoding='utf-8') as f:
            f.readline()
            lines = f.readlines()[:self.count_line]
            extracted_data = tuple(map(process_link_line, lines))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO links (movie_id, imdb_id, tmdb_id) VALUES (?, ?, ?)",
                extracted_data
            )
            conn.commit()
            print(f"Loaded {len(extracted_data)} links into the links table.")

    def get_tmdb(self, list_of_movies, list_of_fields=None):
        """Scraping TMDB pages"""
        if list_of_fields is None:
            list_of_fields = ['Director', 'Budget', 'Cumulative Worldwide Gross', 'Runtime']

        tmdb_info = []
        with requests.Session() as session:
            session.headers.update(self.header)

            for movie_id in list_of_movies:
                if movie_id == 0:
                    continue
                url_tmdb = f'https://www.themoviedb.org/movie/{movie_id}/'
                
                try:
                    response = session.get(url_tmdb, timeout=10)
                    response.raise_for_status() 
                except requests.RequestException as e:
                    print(f"Error loading movie {movie_id}: {e}")
                    continue  
                
                soup = BeautifulSoup(response.text, 'lxml')

                tmdb_stats = [movie_id]
                if 'Director' in list_of_fields:
                    director = soup.select_one('.profile a')
                    tmdb_stats.append(director.get_text(strip=True) if director else "Unknown")
                if 'Budget' in list_of_fields:
                    budget = soup.select_one('.facts.left_column p:nth-of-type(3)')
                    if budget:
                        strong_tag = budget.find('strong')
                        if strong_tag:
                            strong_tag.decompose()
                        clean_budget = budget.get_text(strip=True)[1:-3].replace(',', '')
                        tmdb_stats.append(clean_budget if clean_budget else "0")
                    else:
                        tmdb_stats.append("0")
                if 'Cumulative Worldwide Gross' in list_of_fields:
                    revenue = soup.select_one('.facts.left_column p:nth-of-type(4)')
                    if revenue:
                        strong_tag = revenue.find('strong')
                        if strong_tag:
                            strong_tag.decompose()
                        clean_revenue = revenue.get_text(strip=True)[1:-3].replace(',', '')
                        tmdb_stats.append(clean_revenue if clean_revenue else "0")
                    else:
                        tmdb_stats.append("0")
                if 'Runtime' in list_of_fields:
                    runtime = soup.select_one('.facts .runtime')
                    tmdb_stats.append(runtime.get_text(strip=True) if runtime else "0h 0m")

                tmdb_info.append(tmdb_stats)

        tmdb_info.sort(key=lambda x: x[0], reverse=True)
        return tmdb_info

    def load_tmdb_data_to_db(self):
        """Saving parsing results to a database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tmdb_id FROM links")
            tmdb_ids = tuple(map(lambda row: row[0], cursor.fetchall()))

        print(f"Let's start parsing {len(tmdb_ids)} movies")
        tmdb_info_list = self.get_tmdb(tmdb_ids)

        def convert_to_second(time_str):
            h_match = re.search(r'(\d+)h', time_str)
            m_match = re.search(r'(\d+)m', time_str)
            hours = int(h_match.group(1)) if h_match else 0
            minutes = int(m_match.group(1)) if m_match else 0
            return (hours * 3600) + (minutes * 60)

        def prepare_db_row(field):
            return (
                self.to_int(field[0]),
                field[1],
                self.to_int(field[2]),
                self.to_int(field[3]),
                convert_to_second(field[4])
            )

        ready_to_insert = tuple(map(prepare_db_row, tmdb_info_list))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO tmdb_data (tmdb_id, director, budget, cumulative_worldwide_gross, runtime) VALUES (?, ?, ?, ?, ?)",
                ready_to_insert
            )
            conn.commit()
            print(f"Data for {len(ready_to_insert)} movies has been loaded into tmdb_data.")