from api.core import Mixin
from .base import db


class keys(Mixin, db.Model):
    """keys Table."""

    __tablename__ = "keys"

    key = db.Column(db.String, unique=True, primary_key=True)
    date_created = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Integer, nullable=False)
    is_used = db.Column(db.Integer, nullable=False)

    def __init__(self, key: str, date_created: str, is_admin: int, is_used: int):
        self.key = key
        self.date_created = date_created
        self.is_admin = is_admin
        self.is_used = is_used

    def __repr__(self):
        return f"<Key {self.key,self.date_created,self.is_admin,self.is_used}>"



