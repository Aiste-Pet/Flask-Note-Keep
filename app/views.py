import jwt
from flask import flash, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db, login_manager, bcrypt
from app.forms import (
    RegistrationForm,
    LoginForm,
    UserProfileEditForm,
    UserRequestResetPasswordForm,
    UserResetPasswordForm,
    NoteForm,
    CategoryForm,
)
from app.models.User import User
from app.utils import save_picture, send_email
from datetime import datetime, timezone, timedelta
from app.models.Category import Category
from app.models.Image import Image
from app.models.Note import Note
from sqlalchemy.orm import joinedload


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
        flash("Your profile has been updated!", "success")
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


@app.route("/", methods=["GET", "POST"])
def home():
    if current_user.is_authenticated:
        notes = (
            Note.query.options(joinedload(Note.category))
            .filter_by(user_id=current_user.id)
            .all()
        )
        return render_template("index.html", notes=notes)
    return render_template("index.html")


@app.route("/edit_note/<int:note_id>", methods=["GET", "POST"])
@login_required
def edit_note(note_id):
    note = Note.query.get(note_id)
    note_category = Category.query.filter_by(
        id=note.category_id, user_id=current_user.id
    ).first()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form = NoteForm(request.form)
    if request.method == "POST" and form.validate():
        selected_category_name = request.form.get("category")
        if selected_category_name == "Create new..":
            other_value = request.form.get("other")
            validation = validate_category(category_name=other_value)
            if validation:
                category = Category(
                    name=other_value,
                    user_id=current_user.id,
                )
            db.session.add(category)
            db.session.commit()
            note.category_id = Category.query.filter_by(name=other_value).first().id
        else:
            selected_category_id = Category.query.filter_by(
                name=selected_category_name
            ).first()
            note.category_id = selected_category_id.id
        note.name = form.name.data
        note.text = form.text.data

        db.session.commit()
        flash("Note saved successfully", "success")
        return redirect(url_for("home"))
    return render_template(
        "edit_note.html",
        note=note,
        form=form,
        note_category=note_category,
        categories=categories,
    )


@app.route("/delete_note/<int:note_id>", methods=["GET", "POST"])
@login_required
def delete_note(note_id):
    note = Note.query.get(note_id)
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted successfully", "success")
    return redirect(url_for("home"))


@app.route("/create_note", methods=["GET", "POST"])
@login_required
def create_note():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    note_form = NoteForm(request.form)
    if request.method == "POST" and note_form.validate():
        selected_category_name = request.form.get("category")
        if selected_category_name == "Create new..":
            other_value = request.form.get("other")
            validation = validate_category(category_name=other_value)
            if validation:
                category = Category(
                    name=other_value,
                    user_id=current_user.id,
                )
                db.session.add(category)
                db.session.commit()
            else:
                flash("This category already exists", "danger")
            other_value_id = Category.query.filter_by(name=other_value).first().id
            note = Note(
                name=note_form.name.data,
                text=note_form.text.data,
                category_id=other_value_id,
                user_id=current_user.id,
            )
        else:
            selected_category_id = Category.query.filter_by(
                name=selected_category_name
            ).first()
            note = Note(
                name=note_form.name.data,
                text=note_form.text.data,
                category_id=selected_category_id.id,
                user_id=current_user.id,
            )
        db.session.add(note)
        db.session.commit()
        flash("Note created successfully", "success")
        return redirect(url_for("home"))
    return render_template(
        "create_note.html",
        note_form=note_form,
        categories=categories,
    )


@app.route("/create_category", methods=["GET", "POST"])
@login_required
def create_category():
    form = CategoryForm(request.form)
    if request.method == "POST" and form.validate():
        category_name = request.form.get("name")
        validation = validate_category(category_name=category_name)
        if validation:
            category = Category(
                name=category_name,
                user_id=current_user.id,
            )
            db.session.add(category)
            db.session.commit()
            flash("Category created successfully", "success")
        else:
            flash("This category already exists", "danger")
    return redirect(url_for("categories"))


@app.route("/delete_category/<int:category_id>", methods=["GET", "POST"])
@login_required
def delete_category(category_id):
    category = Category.query.get(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted successfully", "success")
    return redirect(url_for("categories"))


@app.route("/edit_category/<int:category_id>", methods=["POST"])
@login_required
def edit_category(category_id):
    category = Category.query.get(category_id)
    data = request.form
    category_name = data.get("name")
    validation = validate_category(category_name=category_name, category_id=category.id)
    if validation:
        category.name = category_name
        db.session.commit()
        response = {"success": True, "message": "Category edited successfully"}
    else:
        response = {"success": False, "message": "This category already exists"}
    return jsonify(response)


@app.route("/categories", methods=["GET"])
@login_required
def categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form = CategoryForm(request.form)
    return render_template("categories.html", categories=categories, form=form)


def validate_category(category_name, category_id=None):
    print(category_name, category_id)
    category = Category.query.filter_by(
        name=category_name, user_id=current_user.id
    ).first()
    print(category)
    if not category:
        return True
    elif category_id:
        if category.id == category_id:
            return True
    else:
        return True
