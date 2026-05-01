from datetime import datetime
from .base_model import BaseModel


class TrackingLog(BaseModel):

    def __init__(self, log_id, source_id, status, message, created_at=None):
        self.id = log_id
        self.source_id = source_id
        self.status = status
        self.message = message
        self.created_at = created_at or datetime.now()

   
    def is_success(self):
        return self.status == "SUCCESS"

    def is_failed(self):
        return self.status == "FAILED"

    def is_timeout(self):
        return self.status == "TIMEOUT"

    def summary(self):
        return f"[{self.status}] {self.message[:50]}"

    def is_recent(self):
        return (datetime.now() - self.created_at).seconds < 3600