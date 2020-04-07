from sqlalchemy.dialects.postgresql import ARRAY

from ayysmr_web.store import db

class Track(db.Model):
    __tablename__ = 'Tracks'

    # TODO: Add a timestamp to distinguish between duplicate entries
    # a user can listen to a song more than once, and it will be 
    # represented in the database
    id = db.Column(db.String(32), unique = True, primary_key = True, nullable = False)
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