import sqlite3
from src.config import Config
from src.utils.logger import get_action_logger

logger = get_action_logger("db_client")

class DatabaseClient:
    def __init__(self, db_path=Config.DATABASE_FILE_PATH):
        self.db_path = db_path

    def _get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def execute_query(self, query, params=None):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def fetch_all(self, query, params=None):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching data: {e}")
            raise
        finally:
            conn.close()

    def fetch_one(self, query, params=None):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Error fetching data: {e}")
            raise
        finally:
            conn.close()

    def create_table(self, table_name, columns):
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
        self.execute_query(query)
        logger.info(f"Table {table_name} created or already exists")

    def insert_data(self, table_name, data):
        placeholders = ', '.join(['?' for _ in data])
        columns = ', '.join(data.keys())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.execute_query(query, tuple(data.values()))
        logger.info(f"Data inserted into {table_name}")

    def update_data(self, table_name, data, condition):
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self.execute_query(query, tuple(data.values()))
        logger.info(f"Data updated in {table_name}")

    def delete_data(self, table_name, condition):
        query = f"DELETE FROM {table_name} WHERE {condition}"
        self.execute_query(query)
        logger.info(f"Data deleted from {table_name}")

# Example usage:
if __name__ == "__main__":
    db = DatabaseClient()

    # Create a table
    db.create_table("songs", "id INTEGER PRIMARY KEY, title TEXT, artist TEXT")

    # Insert data
    db.insert_data("songs", {"title": "Song Name", "artist": "Artist Name"})

    # Fetch data
    result = db.fetch_all("SELECT * FROM songs")
    print(result)

    # Update data
    db.update_data("songs", {"title": "New Song Name"}, "id = 1")

    # Delete data
    db.delete_data("songs", "id = 1")