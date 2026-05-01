import mysql.connector
from mysql.connector import Error


def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="K334z91h36.",
            database="news_tracking_db",
        )
        return conn
    except Error as e:
        print("DB hata:", e)
        return None
