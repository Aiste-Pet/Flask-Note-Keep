from app import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    notes = db.relationship('Note', backref='category', lazy=True)

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id
