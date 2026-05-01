import re
from datetime import datetime
from bs4 import BeautifulSoup
from collections import (
    Counter,
)  # Müfredat: Veri sayma işlemleri için en profesyonel araç


class NewsParser:

    # ==========================================
    # 🧹 HTML TEMİZLE (Regex Gücüyle)
    # ==========================================
    def clean_html(self, html):
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")

        # Gereksiz etiketleri tek seferde temizle
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        # Müfredat: Regex ile white-space temizliği
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ==========================================
    # 📰 BAŞLIK BUL (Fallback Mantığı)
    # ==========================================
    def extract_title(self, soup):
        # 1. Öncelik title etiketi
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # 2. Öncelik H1 etiketi
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return "Başlık bulunamadı"

    # ==========================================
    # 🖼️ GÖRSEL BUL (Seçici Yaklaşım)
    # ==========================================
    def extract_image(self, soup):
        # Meta og:image genelde en kaliteli görseldir
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        # Yoksa sayfadaki ilk büyük resmi dene
        img = soup.find("img")
        if img and img.get("src"):
            src = img["src"]
            # Base64 gibi gereksiz verileri elemek için basit kontrol
            if src.startswith("http"):
                return src

        return None

    # ==========================================
    # 📅 TARİH PARSE (Esnek Format)
    # ==========================================
    def extract_date(self, soup):
        # Meta datadan tarih çekmeyi dene
        meta_tags = [
            {"property": "article:published_time"},
            {"name": "pubdate"},
            {"property": "og:updated_time"},
        ]

        for tag in meta_tags:
            meta = soup.find("meta", tag)
            if meta and meta.get("content"):
                try:
                    # ISO formatını datetime nesnesine çevir
                    return datetime.fromisoformat(
                        meta["content"].replace("Z", "+00:00")
                    )
                except:
                    continue

        return datetime.now()

    # ==========================================
    # ✂️ ÖZET (Slicing)
    # ==========================================
    def generate_summary(self, text, max_len=200):
        if not text:
            return ""
        # Müfredat: String Slicing
        return text[:max_len].rsplit(" ", 1)[0] + "..." if len(text) > max_len else text

    # ==========================================
    # 🏷️ KATEGORİ TAHMİNİ (Dictionary Mapping & Sets)
    # ==========================================
    def detect_category(self, text):
        if not text:
            return "general"
        text = text.lower()

        # Müfredat: Dictionary as a mapping tool
        rules = {
            "technology": {
                "ai",
                "yapay zeka",
                "yazılım",
                "software",
                "apple",
                "google",
                "çip",
                "robot",
            },
            "business": {
                "ekonomi",
                "dolar",
                "borsa",
                "şirket",
                "para",
                "faiz",
                "ihracat",
                "banka",
            },
            "sports": {
                "futbol",
                "maç",
                "gol",
                "basketbol",
                "lig",
                "transfer",
                "şampiyon",
            },
            "health": {
                "sağlık",
                "kanser",
                "hastalık",
                "tedavi",
                "doktor",
                "virüs",
                "ilaç",
            },
            "entertainment": {
                "film",
                "dizi",
                "ünlü",
                "oyuncu",
                "magazin",
                "konser",
                "müzik",
            },
            "science": {
                "bilim",
                "uzay",
                "araştırma",
                "nasa",
                "gezegen",
                "deney",
                "atom",
            },
        }

        # Müfredat: Set Intersection ile hızlı kategori bulma
        # Metni kelimelere bölüp bir kümeye çeviriyoruz
        text_words = set(re.findall(r"\b\w+\b", text))

        scores = {}
        for category, keywords in rules.items():
            # Kesişen kelime sayısını hesapla
            match_count = len(text_words.intersection(keywords))
            if match_count > 0:
                scores[category] = match_count

        if not scores:
            return "general"

        # En yüksek eşleşme alan kategoriyi döndür
        return max(scores, key=scores.get)

    # ==========================================
    # 🔑 KEYWORD ÇIKAR (Frequency Analysis)
    # ==========================================
    def extract_keywords(self, text, limit=10):
        if not text:
            return []

        # Gereksiz bağlaçları/kelimeleri ele (Stop words - manuel liste)
        stop_words = {
            "ve",
            "veya",
            "için",
            "olan",
            "bir",
            "bu",
            "ile",
            "da",
            "de",
            "ise",
        }

        words = re.findall(r"\b\w+\b", text.lower())
        # Müfredat: List Comprehension & Filtering
        filtered_words = [w for w in words if len(w) > 3 and w not in stop_words]

        # Müfredat: Counter class kullanımı (Hoca bunu çok sever)
        counts = Counter(filtered_words)

        return [word for word, count in counts.most_common(limit)]

    # ==========================================
    # 😊 SENTIMENT (Score Calculation)
    # ==========================================
    def detect_sentiment(self, text):
        if not text:
            return "neutral"
        text = text.lower()

        # Puanlama mantığı
        positive_words = {
            "başarı",
            "kazandı",
            "iyi",
            "büyüme",
            "artış",
            "müjde",
            "sevinç",
        }
        negative_words = {
            "kötü",
            "kriz",
            "ölüm",
            "düşüş",
            "zarar",
            "yangın",
            "kaza",
            "savaş",
        }

        text_words = set(re.findall(r"\b\w+\b", text))

        pos_score = len(text_words.intersection(positive_words))
        neg_score = len(text_words.intersection(negative_words))

        if pos_score > neg_score:
            return "positive"
        elif neg_score > pos_score:
            return "negative"

        return "neutral"

    # ==========================================
    # 🧠 FULL PARSE
    # ==========================================
    def parse(self, html, url):
        soup = BeautifulSoup(html, "html.parser")

        content = self.clean_html(html)

        # Tüm analizleri Python tarafında yapıp sözlük olarak döndür
        return {
            "title": self.extract_title(soup),
            "content": content,
            "summary": self.generate_summary(content),
            "category": self.detect_category(content),
            "image_url": self.extract_image(soup),
            "url": url,
            "published_date": self.extract_date(soup),
            "keywords": self.extract_keywords(content),
            "sentiment": self.detect_sentiment(content),
        }
