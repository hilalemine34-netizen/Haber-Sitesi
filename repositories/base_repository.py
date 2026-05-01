class BaseRepository:

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host="localhost",
                user="root",
                password="...",
                database="news_tracking_db",
                autocommit=True
            )
        except Exception as e:
            print("DB bağlantısı yok:", e)
            return None

    def get_cursor(self, dictionary=False):
        conn = self.get_connection()

        if conn is None:
            return None

        try:
            cursor = conn.cursor(dictionary=dictionary, buffered=True)
            return cursor
        except:
            return None