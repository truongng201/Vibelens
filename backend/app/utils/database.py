import psycopg2
import os

class Database:
    def __init__(self):
        self.connection = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'vibelens'),
            user=os.getenv('POSTGRES_USER', 'admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'admin')
        )
        self.cursor = self.connection.cursor()
        
    def close(self):
        if self.connection:
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection closed.")
            
    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            result = self.cursor.fetchall()
            return result
        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Error executing query: {e}")
        except Exception as e:
            self.connection.rollback()
            print(f"Unexpected error: {e}")
        return None    