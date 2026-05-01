import mysql.connector

class BaseRepository:

    def get_connection(self):
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="K334z91h36.",
            database="news_tracking_db",
            autocommit=True
        )

    def get_cursor(self, dictionary=False):
        conn = self.get_connection()
        conn.ping(reconnect=True)  #  otomatik reconnect
        cursor = conn.cursor(dictionary=dictionary, buffered=True)
        return cursor, conn