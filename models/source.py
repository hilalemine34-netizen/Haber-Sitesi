from datetime import datetime
from .base_model import BaseModel

class Source(BaseModel):

    def __init__(self, source_id, name, base_url, created_at=None):
        self.id = source_id
        self.name = name
        self.base_url = base_url
        self.created_at = created_at or datetime.now()

    def is_valid(self):
        return self.base_url.startswith("http")