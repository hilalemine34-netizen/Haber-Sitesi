import requests
from newspaper import Article
from repositories.news_repository import NewsRepository
import time
import logging
from models.article import NewsArticle
from datetime import datetime

logging.basicConfig(level=logging.INFO)


class NewsFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.repo = NewsRepository()
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # 🔥 API'den çek (hala dict döner → burada normal)
    def fetch(self, category="general"):
        url = f"{self.base_url}/top-headlines?country=us&category={category}&apiKey={self.api_key}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()
            return data.get("articles", [])
        except Exception as e:
            logging.error(f"❌ {category} kategorisi çekilirken hata: {e}")
            return []

    # 🔥 İçerik çekme (değişmedi)
    def get_full_content(self, url, fallback):
        try:
            article = Article(url)
            article.config.browser_user_agent = self.headers["User-Agent"]
            article.config.request_timeout = 10

            for i in range(3):
                try:
                    article.download()
                    article.parse()
                    break
                except Exception:
                    time.sleep(2)
            else:
                return fallback or "İçerik bulunamadı."

            content = article.text
            if not content or len(content.strip()) < 200:
                return fallback or "İçerik bulunamadı."

            return content[:3000]
        except Exception:
            return fallback or "İçerik bulunamadı."
        
    def resolve_url(self, url):
        try:
            response = requests.get(url, allow_redirects=True, timeout=5)
            return response.url
        except:
            return url
        
    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
                # NewsAPI format: 2026-05-01T12:30:00Z
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception as e:
                logging.warning(f"Tarih parse edilemedi: {date_str} - {e}")
                return None

    # 🔥 EN KRİTİK: dict → object dönüşümü
    def _map_api_to_model(self, data: dict) -> NewsArticle:
        return NewsArticle(
            article_id=None,
            title=data.get("title"),
            content=data.get("content") or data.get("description"),
            article_url=data.get("url"),
            source_id=None,

            # 🔥 DATETIME PARSE (çok önemli)
            published_date=self._parse_date(data.get("publishedAt")),

            created_at=None,
            view_count=0,
            like_count=0,

            source_name=(data.get("source") or {}).get("name")
            if isinstance(data.get("source"), dict)
            else data.get("source_name"),

            categories=data.get("category"),

            # 🔥 EN KRİTİK SATIR
            image_url=data.get("urlToImage") or data.get("image_url")
        )

    # 🔥 ANA AKIŞ
    def run(self):
        categories = [
            "technology",
            "business",
            "sports",
            "science",
            "entertainment",
            "health",
        ]

        # 🔥 DB'den gelenler zaten object
        all_articles = self.repo.get_all_articles()

        # 🔥 object üzerinden duplicate set
        existing_titles = {
            (a.title or "").lower().strip()
            for a in all_articles
            if a.title
        }

        for cat in categories:
            logging.info(f"🔄 {cat.upper()} kategorisi çekiliyor...")

            raw_articles = self.fetch(cat)

            # 🔥 BURASI OLAY: API → OBJECT
            fetched_articles = [
                self._map_api_to_model(a)
                for a in raw_articles
                if a.get("title")
            ]

            for article in fetched_articles:
                if article.source_name == "Google News":
                    continue
                time.sleep(0.5)

                if not article.title or not article.article_url:
                    continue

                clean_title = article.title.lower().strip()

                # 🔥 duplicate kontrol
                if clean_title in existing_titles:
                    logging.info(f"⏩ Atlandı (Zaten var): {article.title[:40]}")
                    continue

                # 🔥 içerik çek
                real_url = self.resolve_url(article.article_url)
                article.content = self.get_full_content(
                real_url,
                article.content
            )


                try:
                    self.repo.save_article(
                        title=article.title,
                        content=article.content,
                        url=real_url,   
                        image_url=article.image_url,
                        category=cat,
                        source_name=article.source_name or "Unknown",
                    )

                    existing_titles.add(clean_title)

                    logging.info(f"✅ Kaydedildi: {article.title[:50]}")

                except Exception as e:
                    logging.error(f"❌ DB kayıt hatası: {e}")

        logging.info("🎉 Tüm kategoriler güncellendi.")