from app import db


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"))

    def __init__(self, file_name, note_id):
        self.file_name = file_name
        self.note_id = note_id
