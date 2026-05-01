from services.news_fetcher import NewsFetcher

API_KEY = "d9656d853c9a4f7083c43a82b644784c"

if __name__ == "__main__":
    fetcher = NewsFetcher(API_KEY)
    fetcher.run()