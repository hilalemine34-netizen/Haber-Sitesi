from datetime import datetime, timedelta


class NotificationService:

    def __init__(self, news_repo, interaction_repo, user_repo):
        self.news_repo = news_repo
        self.interaction_repo = interaction_repo
        self.user_repo = user_repo

    # =========================
    #  YENİ HABER VAR MI 
    # =========================
    def has_new_articles(self, last_seen_id):
        latest_id = self.news_repo.get_latest_article_id()
        return latest_id > last_seen_id

    # =========================
    #  KULLANICIYA ÖZEL BİLDİRİMLER
    # =========================
    def get_user_notifications(self, user_id, last_seen_id=0):
        notifications = []

        #  SADECE SON HABERLERİ ÇEK
        all_articles = self.news_repo.get_trending_articles(50)

        # =========================
        #  1. KULLANICI ETKİLEŞİMLERİ
        # =========================
        interactions = self.interaction_repo.get_user_interactions(user_id) or []

        for inter in interactions[-5:]:
            article_id = inter.get("article_id") or inter.get("news_id")
            if not article_id:
                continue

            article = next((a for a in all_articles if a.id == article_id), None)

            if article:
                notifications.append(
                    {
                        "title": "👤 Etkileşim",
                        "message": f"{inter['interaction_type'].capitalize()} yaptın: {article.title}",
                        "article_id": article.id,
                    }
                )

        # =========================
        #  2. TERCİHLERE GÖRE & SON 24 SAAT
        # =========================
        user_categories = self.user_repo.get_user_categories(user_id) or []
        user_cats_set = {c.lower().strip() for c in user_categories}

        time_threshold = datetime.now() - timedelta(days=1)

        for article in all_articles:
            art_date = article.published_date or article.created_at

            art_cats_str = article.categories or ""
            art_cats = (
                {c.lower().strip() for c in art_cats_str.split(",")}
                if art_cats_str
                else set()
            )

            is_new = article.id > last_seen_id
            is_preferred = any(cat in user_cats_set for cat in art_cats)
            is_recent = art_date > time_threshold if art_date else False

            if is_new and (is_preferred or is_recent):
                notifications.append(
                    {
                        "title": "🆕 Sana Özel" if is_preferred else "🆕 Yeni Haber",
                        "message": article.title,
                        "article_id": article.id,
                    }
                )

        # =========================
        #  3. FALLBACK (TRENDING)
        # =========================
        if not notifications:
            trending = self.news_repo.get_trending_articles(3)
            for article in trending:
                notifications.append(
                    {
                        "title": "🔥 Trend Haber",
                        "message": article.title,
                        "article_id": article.id,
                    }
                )

        # =========================
        #  4. DUPLICATE TEMİZLE
        # =========================
        seen = set()
        unique_notifications = []

        for n in notifications:
            if n["article_id"] not in seen:
                unique_notifications.append(n)
                seen.add(n["article_id"])

        return unique_notifications

    # =========================
    #  TRENDING ALERT
    # =========================
    def get_trending_alert(self):
        trending = self.news_repo.get_trending_articles(1)
        if not trending:
            return None

        article = trending[0]

        return {
            "title": "🔥 Çok Popüler!",
            "message": article.title,
            "article_id": article.id,
        }