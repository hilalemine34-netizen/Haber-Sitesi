from controllers.web_controller import app
from repositories.news_repository import NewsRepository

repo = NewsRepository()

articles = repo.get_all_articles()

article = articles[0]

print(article)
print(article.title)
print(article.get_summary())

if __name__ == "__main__":
    app.run(debug=True)