from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func

from ayysmr_web.store import db

class Track(db.Model):
    __tablename__ = 'Tracks'

    id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    track_id = db.Column(db.String(32))
    timestamp = db.Column(db.DateTime, nullable = False, server_default = func.now())
    name = db.Column(db.String(120))
    artist = db.Column(db.String(32))
    preview_url = db.Column(db.String(120))

    artist_id = db.Column(db.String(32), nullable = False)
    genres = db.Column(ARRAY(db.String()))
    popularity = db.Column(db.Integer())

    danceability = db.Column(db.Float())
    energy = db.Column(db.Float())
    key = db.Column(db.Float())
    loudness = db.Column(db.Float())
    mode = db.Column(db.Float())
    speechiness = db.Column(db.Float())
    acousticness = db.Column(db.Float())
    instrumentalness = db.Column(db.Float())
    liveness = db.Column(db.Float())
    valence = db.Column(db.Float())
    tempo = db.Column(db.Float())

    def __repr__(self):
        return "<track {}>".format(self.id)