import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    # Database connection parameters
    db_params = {
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'hrithiq21'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }

    # Connect to PostgreSQL server
    conn = psycopg2.connect(**db_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check if database exists
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (os.getenv('DB_NAME', 'refl3kt_db'),))
    exists = cur.fetchone()
    
    if not exists:
        print("Creating database...")
        cur.execute(f"CREATE DATABASE {os.getenv('DB_NAME', 'refl3kt_db')}")
        print("Database created successfully!")
    else:
        print("Database already exists.")

    # Close connection
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_database() 