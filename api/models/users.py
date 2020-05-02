from api.core import Mixin
from .base import db


class users(Mixin, db.Model):
    """users Table."""

    __tablename__ = "users"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    irdistrict = db.Column(db.String)
    defaultloclat = db.Column(db.String)
    defaultloclong = db.Column(db.String)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    isadmin = db.Column(db.Integer, nullable=False)
    ismaster = db.Column(db.Integer, nullable=False)

    datapoints = db.relationship("user_data", backref="user_data.user_id")

    def __init__(self, name: str, username: str, email: str, password: str, irdistrict: str, defaultloclat: str, defaultloclong: str, isadmin: int, ismaster: int):
        self.name = name
        self.username = username
        self.email = email
        self.irdistrict = irdistrict
        self.defaultloclat = defaultloclat
        self.defaultloclong = defaultloclong
        self.password = password
        self.isadmin = isadmin
        self.ismaster = ismaster

    def __repr__(self):
        return f"<User {self.name,self.username,self.email,self.irdistrict,self.defaultloclat,self.defaultloclong,self.password,self.isadmin,self.ismaster,self.datapoints}>"

