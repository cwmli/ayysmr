from ayysmr_web import db

class User(db.Model):
    __tablename__ = 'Users'

    id = db.Column(db.String(32), unique = True, primary_key = True, nullable = False)
    access_token = db.Column(db.Text())
    refresh_token = db.Column(db.Text())
    expire_time = db.Column(db.Integer())

    def __repr__(self):
        return "<User {}>".format(self.id)