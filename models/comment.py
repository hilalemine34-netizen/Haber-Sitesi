from datetime import datetime
from .base_model import BaseModel


class Comment(BaseModel):

    def __init__(self, comment_id, user_id, article_id, content, created_at=None, username=None):
        self.id = comment_id
        self.user_id = user_id
        self.article_id = article_id
        self.content = content
        self.created_at = created_at or datetime.now()
        self.username = username

    
    def short(self):
        return self.content[:50]

    def is_long(self):
        return len(self.content) > 200
    