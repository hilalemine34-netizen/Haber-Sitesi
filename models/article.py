from datetime import datetime, timedelta
from .base_model import BaseModel


class NewsArticle(BaseModel):

    def __init__(
        self,
        article_id,
        title,
        content,
        article_url,
        source_id,
        published_date=None,
        created_at=None,
        view_count=0,
        like_count=0,
        source_name=None,
        categories=None,
        image_url=None  
    ):
        self.id = article_id
        self.title = title
        self.content = content
        self.article_url = article_url
        self.source_id = source_id
        self.published_date = published_date
        self.created_at = created_at

      
        self.view_count = view_count
        self.like_count = like_count
        self.source_name = source_name
        self.categories = categories

        self.image_url = image_url  

    def get_summary(self, length=120):
        if not self.content:
            return ""
        return self.content[:length] + "..."

    def is_recent(self):
        if not self.published_date:
            return False
        return self.published_date > datetime.now() - timedelta(days=1)

    def short_title(self, length=60):
        if not self.title:
            return "No title"
        return self.title[:length]