from .base_repository import BaseRepository
from models.comment import Comment
from models.article import NewsArticle


class InteractionRepository(BaseRepository):

    # =========================
    #  YORUMLAR
    # =========================
    def get_comments_by_article(self, article_id):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT c.*, u.username
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.article_id = %s
                ORDER BY c.created_at DESC
            """, (article_id,))

            return [
                Comment(
                    comment_id=c["id"],
                    user_id=c["user_id"],
                    article_id=c["article_id"],
                    content=c["content"],
                    created_at=c["created_at"],
                    username=c["username"]
                )
                for c in cursor.fetchall()
            ]

        finally:
            cursor.close()

    def add_comment(self, user_id, article_id, content, username):
        cursor, conn = self.get_cursor()
        cursor.execute("""
        INSERT INTO comments (user_id, article_id, content)
        VALUES (%s, %s, %s)
    """, (user_id, article_id, content))

    # =========================
    #  FAVORİ
    # =========================
    def add_favorite(self, user_id, article_id):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute(
                "SELECT id FROM interactions WHERE user_id=%s AND article_id=%s AND interaction_type='favorite'",
                (user_id, article_id),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute("DELETE FROM interactions WHERE id=%s", (existing[0],))
            else:
                cursor.execute(
                    "INSERT INTO interactions (user_id, article_id, interaction_type) VALUES (%s, %s, 'favorite')",
                    (user_id, article_id),
                )

            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_user_favorites(self, user_id):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT article_id FROM interactions WHERE user_id=%s AND interaction_type='favorite'",
                (user_id,),
            )
            fav_ids = [row["article_id"] for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM articles")
            all_articles = cursor.fetchall()

            return [
                NewsArticle(
                    article_id=a["id"],
                    title=a["title"],
                    content=a["content"],
                    article_url=a["article_url"],
                    source_id=a["source_id"],
                    created_at=a.get("created_at"),
                    image_url=a.get("image_url"),
                )
                for a in all_articles if a["id"] in fav_ids
            ]

        finally:
            cursor.close()
            conn.close()

    # =========================
    #  LIKE 
    # =========================
    def add_like(self, user_id, article_id):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute(
                "SELECT id FROM interactions WHERE user_id=%s AND article_id=%s AND interaction_type='like'",
                (user_id, article_id),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute("DELETE FROM interactions WHERE id=%s", (existing[0],))
            else:
                cursor.execute(
                    "INSERT INTO interactions (user_id, article_id, interaction_type) VALUES (%s, %s, 'like')",
                    (user_id, article_id),
                )

            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_user_liked_articles(self, user_id):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT article_id FROM interactions WHERE user_id=%s AND interaction_type='like'",
                (user_id,),
            )
            liked_ids = [row["article_id"] for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM articles")
            all_articles = cursor.fetchall()

            return [
                NewsArticle(
                    article_id=a["id"],
                    title=a["title"],
                    content=a["content"],
                    article_url=a["article_url"],
                    source_id=a["source_id"],
                    created_at=a.get("created_at"),
                    image_url=a.get("image_url"),
                )
                for a in all_articles if a["id"] in liked_ids
            ]

        finally:
            cursor.close()

    # =========================
    #  VIEW
    # =========================
    def get_like_count(self, article_id):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM interactions WHERE article_id=%s AND interaction_type='like'",
                (article_id,)
            )
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def get_view_count(self, article_id):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM interactions WHERE article_id=%s AND interaction_type='view'",
                (article_id,)
            )
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def add_view(self, user_id, article_id):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute(
                "SELECT id FROM interactions WHERE user_id=%s AND article_id=%s AND interaction_type='view'",
                (user_id, article_id),
            )
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO interactions (user_id, article_id, interaction_type) VALUES (%s, %s, 'view')",
                    (user_id, article_id),
                )
                conn.commit()
        finally:
            cursor.close()

    def get_view_count(self, article_id):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT interaction_type FROM interactions WHERE article_id=%s",
                (article_id,),
            )
            interactions = cursor.fetchall()
            return len([i for i in interactions if i["interaction_type"] == "view"])
        finally:
            cursor.close()

    # =========================
    #  INTERACTION DATA
    # =========================
    def get_user_interactions(self, user_id):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT 
                    i.article_id,
                    i.interaction_type,
                    GROUP_CONCAT(DISTINCT c.name) AS categories
                FROM interactions i
                LEFT JOIN article_categories ac ON i.article_id = ac.article_id
                LEFT JOIN categories c ON ac.category_id = c.id
                WHERE i.user_id = %s
                GROUP BY i.id, i.article_id, i.interaction_type
                """,
                (user_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    # =========================
    #  PREFERENCES
    # =========================
    def get_user_preferences(self, user_id):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT up.user_id, c.id, c.name FROM user_preferences up JOIN categories c ON up.category_id = c.id"
            )
            all_prefs = cursor.fetchall()
            return [p for p in all_prefs if p["user_id"] == user_id]
        finally:
            cursor.close()