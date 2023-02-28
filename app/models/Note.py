from app import db


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(255), nullable=False)
    text = db.Column(db.String(800), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

    def __init__(self, user_id, name, text, category_id):
        self.user_id = user_id
        self.name = name
        self.text = text
        self.category_id = category_id
