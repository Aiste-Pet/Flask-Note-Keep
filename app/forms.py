from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
)
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError, Length
from app.models.User import User
from app.models.Category import Category


class RegistrationForm(FlaskForm):
    email = StringField("E-mail", [DataRequired(), Email()])
    password = PasswordField("Password", [DataRequired()])
    confirm_password = PasswordField(
        "Repeat password", [EqualTo("password", "Password must match.")]
    )

    def check_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("This email address is already registered.")


class LoginForm(FlaskForm):
    email = StringField("E-mail", [DataRequired(), Email()])
    password = PasswordField("Password", [DataRequired()])
    remember = BooleanField("Remember")


class UserProfileEditForm(FlaskForm):
    email = StringField("E-mail", [DataRequired(), Email()])
    picture = FileField(
        "Change profile picture", validators=[FileAllowed(["jpg", "png"])]
    )

    def check_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("This email address is already registered.")


class UserRequestResetPasswordForm(FlaskForm):
    email = StringField("E-mail", [DataRequired(), Email()])


class UserResetPasswordForm(FlaskForm):
    password = PasswordField("Password", [DataRequired()])
    confirm_password = PasswordField(
        "Repeat password", [EqualTo("password", "Passwords must match.")]
    )


class NoteForm(FlaskForm):
    name = StringField("Name", [DataRequired(), Length(max=255)])
    text = StringField("Text", [DataRequired()])
    category = StringField("Category", [DataRequired(), Length(max=255)])


class CategoryForm(FlaskForm):
    name = StringField("Name", [DataRequired(), Length(max=255)])
