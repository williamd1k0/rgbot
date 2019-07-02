import os
import psycopg2

def create_connection():
    config = {
        'user': os.environ.get('RGB_DBUSER', ''),
        'password': os.environ.get('RGB_DBPASS', ''),
        'host': os.environ.get('RGB_DBHOST'),
        'port': os.environ.get('RGB_DBPORT'),
        'database': os.environ.get('RGB_DBNAME', ''),
    }
    return psycopg2.connect(**config)

def migrate(sql):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
