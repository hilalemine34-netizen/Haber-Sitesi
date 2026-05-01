from datetime import datetime
from .base_model import BaseModel


class Interaction(BaseModel):

    def __init__(self, interaction_id, user_id, article_id, interaction_type, created_at=None):
        self.id = interaction_id
        self.user_id = user_id
        self.article_id = article_id
        self.interaction_type = interaction_type
        self.created_at = created_at or datetime.now()

    def is_like(self):
        return self.interaction_type == "like"

    def is_favorite(self):
        return self.interaction_type == "favorite"

    def is_view(self):
        return self.interaction_type == "view"