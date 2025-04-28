import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="dpg-d07dhgs9c44c739ssq2g-a",
        database="inventarios_m0he",
        user="inventarios_m0he_user",
        password="9YMkzbvMEPVJTjK3gT1jkqhyHSxbTv5p"
    )
    return conn
