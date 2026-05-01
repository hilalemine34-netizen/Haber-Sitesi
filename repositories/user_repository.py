from .base_repository import BaseRepository
from models.user import User

class UserRepository(BaseRepository):

    # =========================
    #  KULLANICI İŞLEMLERİ
    # =========================
    def get_user_by_username(self, username):
        cursor, conn = self.get_cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users")
            all_users = cursor.fetchall()

            user = [u for u in all_users if u["username"] == username]
            if not user:
                return None
            u = user[0]

            return User(
                user_id=u["id"],
                username=u["username"],
                password=u["password"],
                email=u["email"],
                is_active=u.get("is_active", True),
                created_at=u.get("created_at")
            )

        finally:
            cursor.close()
            conn.close()

    def create_user(self, username, email, password_hash):
        cursor, conn = self.get_cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password_hash),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    # =========================
    #  KATEGORİ TERCİHLERİ
    # =========================
    def get_user_categories(self, user_id):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT category_id FROM user_preferences WHERE user_id = %s",
                (user_id,),
            )
            pref_ids = [row["category_id"] for row in cursor.fetchall()]

            cursor.execute("SELECT id, name FROM categories")
            all_categories = cursor.fetchall()

            return [c["name"] for c in all_categories if c["id"] in pref_ids]

        finally:
            cursor.close()
            conn.close()

    def update_preferences(self, user_id, selected_categories):
        """Tercihleri günceller (Yazma işlemi olduğu için SQL ağırlıklıdır)"""
        cursor, conn = self.get_cursor()
        try:
            # Önce mevcutları sil (SQL burada en temizi)
            cursor.execute(
                "DELETE FROM user_preferences WHERE user_id = %s", (user_id,)
            )

            if selected_categories:
                # Python ile veri hazırlığı
                data = [(user_id, int(cat_id)) for cat_id in selected_categories]

                # Toplu ekleme
                cursor.executemany(
                    "INSERT INTO user_preferences (user_id, category_id) VALUES (%s, %s)",
                    data,
                )
            conn.commit()
        except Exception as e:
            print(f" Tercih güncelleme hatası: {e}")
        finally:
            cursor.close()

    def get_user_by_id(self, user_id):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return User(
                user_id=row["id"],
                username=row["username"],
                password=row["password"],   # ✅ DÜZELTİLDİ
                email=row["email"],
                is_active=row.get("is_active", True),
                created_at=row.get("created_at")
            )
        finally:
            cursor.close()
            conn.close()
