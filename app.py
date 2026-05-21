from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from flask_bcrypt import Bcrypt
import os
import re

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret123"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    products = Product.query.all()
    return render_template("home.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not name or not email or not phone or not password:
            error = "所有欄位都必填"

        elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            error = "Email 格式錯誤"

        elif not re.match(r"^09\d{8}$", phone):
            error = "手機格式錯誤，請輸入 09 開頭的 10 碼手機"

        elif len(password) < 6:
            error = "密碼至少需要 6 碼"

        elif password != confirm_password:
            error = "兩次密碼不一致"

        elif User.query.filter_by(email=email).first():
            error = "Email 已被註冊"

        elif User.query.filter_by(phone=phone).first():
            error = "手機已被註冊"

        else:
            hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

            user = User(
                name=name,
                email=email,
                phone=phone,
                password=hashed_pw
            )

            db.session.add(user)
            db.session.commit()

            return redirect("/login")

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        account = request.form["account"]
        password = request.form["password"]

        user = User.query.filter(
            (User.email == account) | (User.phone == account)
        ).first()

        if not user:
            error = "帳號不存在"

        elif not bcrypt.check_password_hash(user.password, password):
            error = "密碼錯誤"

        else:
            login_user(user)
            return redirect("/dashboard")

    return render_template("login.html", error=error)


@app.route("/dashboard")
@login_required
def dashboard():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", products=products)


@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    error = None

    if request.method == "POST":
        title = request.form["title"]
        price = request.form["price"]
        description = request.form["description"]

        if not title or not price or not description:
            error = "所有商品欄位都必填"
        else:
            product = Product(
                title=title,
                price=price,
                description=description,
                user_id=current_user.id
            )

            db.session.add(product)
            db.session.commit()

            return redirect("/dashboard")

    return render_template("add_product.html", error=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)