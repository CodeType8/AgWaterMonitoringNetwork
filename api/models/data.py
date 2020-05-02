from api.core import Mixin
from .base import db

# Note that we use sqlite for our tests, so you can't use Postgres Arrays
class user_data(Mixin, db.Model):
    """user_data Table."""

    __tablename__ = "user_data"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    datapoint = db.Column(db.String, nullable=False)
    dataunit = db.Column(db.String, nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    location = db.Column(db.String, nullable=False)
    xgeo = db.Column(db.Numeric, nullable=True)
    ygeo = db.Column(db.Numeric, nullable=True)
    date = db.Column(db.String, nullable=False)
    comments = db.Column(db.String, nullable=False)

    def __init__(self, datapoint: str, dataunit: str, location: str, xgeo: float, ygeo: float, date: str, comments: str,user_id: int):
        self.datapoint = datapoint
        self.dataunit = dataunit
        self.location = location
        self.xgeo = xgeo
        self.ygeo = ygeo
        self.date = date
        self.comments = comments
        self.user_id = user_id

    def __repr__(self):
        return f"<Datapoint {self.id, self.datapoint, self. dataunit, self.location, self.xgeo, self.ygeo, self.date, self.comments}>"
