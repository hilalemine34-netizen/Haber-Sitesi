from datetime import datetime
from werkzeug.security import check_password_hash
from .base_model import BaseModel


class User(BaseModel):

    def __init__(self, user_id, username, password, email=None, is_active=True, created_at=None):
        self.id = user_id
        self.username = username
        self._password = password   #  encapsulation
        self.email = email
        self.is_active = is_active
        self.created_at = created_at or datetime.now()

    #  şifre kontrolü
    def check_password(self, raw_password):
        return check_password_hash(self._password, raw_password)

    #  durum kontrolü
    def is_active_user(self):
        return self.is_active

    def deactivate(self):
        self.is_active = False

    #  email kontrol
    def has_email(self):
        return self.email is not None and "@" in self.email

    #  basit profil bilgisi
    def display_name(self):
        return self.username.capitalize()

    #  validasyon
    def is_valid(self):
        return self.username != "" and self._password is not None