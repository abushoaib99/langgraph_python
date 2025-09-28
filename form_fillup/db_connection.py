import psycopg2
from decouple import config

# PostgreSQL Database configuration
db_config = {
    "host": config("DB_HOST"),
    "port": config("DB_PORT"),
    "database": config("DB_NAME"),
    "user": config("DB_USER"),
    "password": config("DB_PASSWORD")
}


# Function to get a database connection
def get_db_connection():
    conn = psycopg2.connect(**db_config)
    return conn
