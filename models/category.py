from .base_model import BaseModel

class Category(BaseModel):

    def __init__(self, category_id, name):
        self.id = category_id
        self.name = name

    def matches(self, keyword):
        return keyword.lower() in self.name.lower()