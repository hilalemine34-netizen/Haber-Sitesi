from .base_model import BaseModel


class UserPreference(BaseModel):

    def __init__(self, user_id, category_id):
        self.user_id = user_id
        self.category_id = category_id


    def matches_category(self, category_id):
        return self.category_id == category_id

    def is_valid(self):
        return self.user_id is not None and self.category_id is not None