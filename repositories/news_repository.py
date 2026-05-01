from .base_repository import BaseRepository
import re
from datetime import datetime
from models.article import NewsArticle


class NewsRepository(BaseRepository):

    # ==========================================
    #  YARDIMCI METOT: HAM VERİ ÇEKİCİ
    # ==========================================
    def __get_raw_data(self):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            query = """
                SELECT 
                    a.*,
                    s.name AS source_name,

                    GROUP_CONCAT(DISTINCT c.name) AS categories,

                    COUNT(DISTINCT CASE 
                        WHEN i.interaction_type='view' THEN i.id 
                    END) AS view_count,

                    COUNT(DISTINCT CASE 
                        WHEN i.interaction_type='like' THEN i.id 
                    END) AS like_count

                FROM articles a

                LEFT JOIN sources s ON a.source_id = s.id
                LEFT JOIN interactions i ON a.id = i.article_id
                LEFT JOIN article_categories ac ON a.id = ac.article_id
                LEFT JOIN categories c ON ac.category_id = c.id

                GROUP BY a.id
                ORDER BY a.created_at DESC
            """

            cursor.execute(query)
            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

    # ==========================================
    #  TÜM HABERLER
    # ==========================================
    def get_all_articles(self, category="all", source=None):
        rows = self.__get_raw_data()

        articles = [
            NewsArticle(
                article_id=r["id"],
                title=r["title"],
                content=r["content"],
                article_url=r["article_url"],
                source_id=r["source_id"],
                published_date=r.get("published_date"),
                created_at=r.get("created_at"),
                image_url=r.get("image_url"),

                
                view_count=r.get("view_count", 0),
                like_count=r.get("like_count", 0),
                source_name=r.get("source_name"),
                categories=r.get("categories")
            )
            for r in rows
    ]

        # Kategori Filtreleme
        if category and category != "all":
            articles = [
                a
                for a in articles
                if getattr(a, "categories", None) and category in getattr(a, "categories", None).split(",")
            ]

        # Kaynak Filtreleme
        if source:
            articles = [a for a in articles if a.source_name == source]

        # Sıralama (NoneType Hatası İçin Önlem Alındı)
        articles.sort(
        key=lambda x: (
            x.published_date if x.published_date else x.created_at
        ),
        reverse=True
    )

        return articles

    # ==========================================
    #  SEARCH
    # ==========================================
    def search_articles(self, keyword):
        rows = self.__get_raw_data()
        keyword = (keyword or "").lower()

        articles = [
            NewsArticle(
                article_id=r["id"],
                title=r["title"],
                content=r["content"],
                article_url=r["article_url"],
                source_id=r["source_id"],
                published_date=r.get("published_date"),
                created_at=r.get("created_at"),
                view_count=r.get("view_count", 0),
                like_count=r.get("like_count", 0),
                source_name=r.get("source_name"),
                categories=r.get("categories"),
                image_url=r.get("image_url"),
            )
            for r in rows
        ]

        results = []
        for a in articles:
            title = (a.title or "").lower()
            content = (a.content or "").lower()
            if keyword in f"{title} {content}":
                results.append(a)

        results.sort(
            key=lambda x: x.published_date or x.created_at,
            reverse=True
        )
        return results

    # ==========================================
    # TRENDING
    # ==========================================
    def get_trending_articles(self, limit=5):
        rows = self.__get_raw_data()

        articles = [
            NewsArticle(
                article_id=r["id"],
                title=r["title"],
                content=r["content"],
                article_url=r["article_url"],
                source_id=r["source_id"],
                published_date=r.get("published_date"),
                created_at=r.get("created_at"),
                view_count=r.get("view_count", 0),
                like_count=r.get("like_count", 0),
                source_name=r.get("source_name"),
                categories=r.get("categories"),
                image_url=r.get("image_url"),
            )
            for r in rows
        ]

        for a in articles:
            a.trend_score = (a.view_count * 0.6) + (a.like_count * 0.4)

        articles.sort(key=lambda x: getattr(x, "trend_score", 0), reverse=True)
        return articles[:limit]

    # ==========================================
    #  TEK HABER
    # ==========================================
    def get_article_by_id(self, article_id):
        rows = self.__get_raw_data()

        for r in rows:
            if r["id"] == article_id:
                return NewsArticle(
                    article_id=r["id"],
                    title=r["title"],
                    content=r["content"],
                    article_url=r["article_url"],
                    source_id=r["source_id"],
                    published_date=r.get("published_date"),
                    created_at=r.get("created_at"),
                    view_count=r.get("view_count", 0),
                    like_count=r.get("like_count", 0),
                    source_name=r.get("source_name"),
                    categories=r.get("categories"),
                    image_url=r.get("image_url"),
                )
        return None

    # ==========================================
    #  HABER KAYDET
    # ==========================================
    def save_article(self, title, content, url, image_url, category, source_name):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute("SELECT id FROM sources WHERE name=%s", (source_name,))
            res = cursor.fetchone()
            source_id = res[0] if res else None

            if not source_id:
                cursor.execute("INSERT INTO sources (name) VALUES (%s)", (source_name,))
                source_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO articles (title, content, article_url, image_url, source_id)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (title, content, url, image_url, source_id),
            )

            article_id = cursor.lastrowid

            cursor.execute("SELECT id FROM categories WHERE name=%s", (category,))
            cat_res = cursor.fetchone()
            if cat_res:
                cursor.execute(
                    "INSERT INTO article_categories (article_id, category_id) VALUES (%s, %s)",
                    (article_id, cat_res[0]),
                )

            conn.commit()
        finally:
            cursor.close()

    # ==========================================
    #  MULTI CATEGORY (HATA GİDERİLDİ)
    # ==========================================
    def get_articles_by_multiple_categories(self, categories, limit=20):
        if not categories:
            return self.get_trending_articles(limit)

        all_articles = self.get_all_articles()

        target_cats = set(categories)

        results = [
            a
            for a in all_articles
            if a.categories
            and any(cat in target_cats for cat in a.categories.split(","))
        ]

        return sorted(
            results,
            key=lambda x: x.published_date or x.created_at,
            reverse=True,
        )[:limit]

    # ==========================================
    # TÜM KATEGORİLER
    # ==========================================
    def get_all_categories(self):
        cursor, conn = self.get_cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM categories")
            all_cats = cursor.fetchall()

            return sorted(all_cats, key=lambda x: x['name'].lower())

        finally:
            cursor.close()
            conn.close()


    def get_latest_article_id(self):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute("SELECT MAX(id) FROM articles")
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0
        finally:
            cursor.close()
            conn.close()

    def get_liked_articles(self, user_id):
        all_articles = self.get_all_articles()  #  TEK DOĞRU KAYNAK
        liked_ids = self._get_liked_ids(user_id)

        return [a for a in all_articles if a.id in liked_ids]


    def get_user_feed(self, user_id):
        return self.get_all_articles()
    

    def _get_liked_ids(self, user_id):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute(
                "SELECT article_id FROM interactions WHERE user_id=%s AND interaction_type='like'",
                (user_id,)
            )
            return {row[0] for row in cursor.fetchall()}
        finally:
            cursor.close()