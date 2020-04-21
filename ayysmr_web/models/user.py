from datetime import datetime

from ayysmr_web.store import db

class User(db.Model):
    __tablename__ = 'Users'

    id = db.Column(db.String(32), unique = True, primary_key = True, nullable = False)
    access_token = db.Column(db.Text())
    refresh_token = db.Column(db.Text())
    expire_time = db.Column(db.Integer())
    last_play_history_upd = db.Column(db.DateTime(), default = datetime(1970, 1, 1), nullable = False)

    def __repr__(self):
        return "<User {}>".format(self.id)
