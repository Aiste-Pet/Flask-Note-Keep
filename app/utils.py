from app import app
import os
import secrets
from PIL import Image
from flask import url_for
from flask_mail import Message


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_images', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def send_email(email, token):
    msg = Message()
    msg.subject = "Atstatykite slaptažodį"
    msg.sender = "noreply@test.com"
    msg.recipients = [email]
    msg.body = f"Nuoroda slaptažodžiui atstatyti: {url_for('reset_password', token=token, _external=True)}"

    print(msg)
