import jwt
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db, login_manager, bcrypt
from app.forms import (
    RegistrationForm,
    LoginForm,
    UserProfileEditForm,
    UserRequestResetPasswordForm,
    UserResetPasswordForm,
)
from app.models.User import User
from app.utils import save_picture, send_email
from datetime import datetime, timezone, timedelta


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/registration", methods=["GET", "POST"])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        form.check_email(email=form.email)
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(email=form.email.data, password=encrypted_password)
        db.session.add(user)
        db.session.commit()
        flash("Account creation successful, you can now login", "success")
        return redirect(url_for("home"))
    return render_template("registration.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Login failed. Check your email and password", "danger")
    return render_template("login.html", form=form)


@app.route("/request-reset-password", methods=["GET", "POST"])
def request_reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = UserRequestResetPasswordForm()
    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            encoded_jwt = jwt.encode(
                {
                    "user_id": user.id,
                    "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=10),
                },
                app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            send_email(form.email.data, encoded_jwt)
        flash(
            "If you have an account registered with this email, we have sent you a link to reset a password.",
            "success",
        )
    return render_template("request_reset_password.html", form=form)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    token = request.args.get("token", "", type=str)
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")
        user = User.query.get(payload["user_id"])
        form = UserResetPasswordForm()
        if user and request.method == "POST" and form.validate_on_submit():
            encrypted_password = bcrypt.generate_password_hash(
                form.password.data
            ).decode("utf-8")
            user.password = encrypted_password
            db.session.add(user)
            db.session.commit()
            flash("Password changed! You can now login.", "success")
            return redirect(url_for("login"))
        return render_template("reset_password.html", form=form, token=token)
    except jwt.InvalidSignatureError:
        flash("Error or link no longer valid", "danger")
        return redirect(url_for("login"))
    except jwt.ExpiredSignatureError:
        flash("Error or link no longer valid", "danger")
        return redirect(url_for("login"))


@app.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UserProfileEditForm()
    if request.method == "POST" and form.validate_on_submit():
        form.check_email(email=form.email)
        if form.picture.data:
            picture = save_picture(form.picture.data)
            current_user.picture = picture
        current_user.email = form.email.data
        db.session.commit()
        flash("Tavo paskyra atnaujinta!", "success")
        return redirect(url_for("profile"))
    elif request.method == "GET":
        form.email.data = current_user.email
    picture = url_for("static", filename=f"/profile_images/{current_user.picture}")
    return render_template("profile.html", form=form, picture=picture)


@app.route("/about")
def about():
    return render_template("about.html")


@app.errorhandler(401)
def unauthorized(error):
    return render_template("unauthorized.html"), 401


@app.errorhandler(404)
def not_found(error):
    return render_template("not_found.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("server_error.html"), 500
