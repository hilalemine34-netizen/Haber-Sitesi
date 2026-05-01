import sys

# 🔥 repositories klasörünü path'e ekle
sys.path.append("repositories")

from repositories.news_repository import NewsRepository

repo = NewsRepository()

articles = repo.get_all_articles()

if articles:
    a = articles[0]
    print(a)
    print(a.title)
    print(a.view_count)