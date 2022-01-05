import smtplib
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from sqlalchemy.sql.sqltypes import Integer
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_manager, login_user, LoginManager, login_required, current_user, logout_user
from forms import CommentForm, CreatePostForm, RegisterForm, LoginForm, ContactForm
from flask_gravatar import Gravatar
import datetime as dt
from functools import wraps
from dotenv import load_dotenv
import os 

app = Flask(__name__)

# Environment Data
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TO_EMAIL_ID = os.getenv("TO_MAIL_ID")
app.config['SECRET_KEY'] = os.getenv("BLOGPOST_SECRET_KEY")


ckeditor = CKEditor(app)
Bootstrap(app)

# Intialize the Gravatar
gravatar = Gravatar(app=app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure Flask_login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", backref="author")
    # Add parent relationship
    # "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", backref="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    # author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship("Comment", backref="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    user_comment = db.Column(db.String(1000), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))


db.create_all()


# Inject the year in all templates
@app.context_processor
def inject_year():
    return {"year": dt.datetime.now().year}


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        check_mail = User.query.filter_by(email=form.email.data).first()

        if not check_mail:
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(
                    password=form.password.data,
                    method='pbkdf2:sha256',
                    salt_length=8))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
        else:
            flash("You've already signed up with that email, Login Instead!")
            return redirect(url_for('login'))
    return render_template("register.html", form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        check_user = User.query.filter_by(email=form.email.data).first()

        if check_user:
            if check_password_hash(pwhash=check_user.password, password=form.password.data):
                login_user(check_user)
                return redirect(url_for('get_all_posts', id=check_user.id))
            else:
                flash("Password is incorrect. Try again!")
                return redirect(url_for('login'))
        else:
            flash("This email does not exist in database.")
            return redirect(url_for('login'))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    comment_form = CommentForm()
    requested_post = BlogPost.query.get(post_id)

    if comment_form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                user_comment=comment_form.comment_box.data,
                author_id=current_user.id,
                post_id=requested_post.id
            )
            db.session.add(new_comment)
            db.session.commit()
            comment_form.comment_box.data = ""
            return redirect(url_for('show_post', post_id=post_id))
        else:
            flash("You need to login to register the comment.")
            return redirect(url_for("login"))
    return render_template("post.html", post=requested_post, form=comment_form, user_table=User)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["POST", "GET"])
def contact():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        name = contact_form.name.data
        email = contact_form.email.data
        phone = contact_form.phone.data
        message = contact_form.message.data

        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=EMAIL, password=PASSWORD)
            connection.sendmail(from_addr=EMAIL,
                                to_addrs=TO_EMAIL_ID,
                                msg=f"Subject:New Message from BlogPost\n\nName: {name}\nEmail: {email}\nPhone No.: {phone}\nMessage: {message}")
            flash("Successfully sent your message.")
            return redirect(url_for('contact', msg_sent=True))
    return render_template("contact.html", current_user=current_user, form=contact_form)


# Admin only decorator
def admin_only(fun):
    @wraps(fun)
    def decorated_function(*args, **kwargs):
        try:
            the_id = current_user.id
        except:
            print("no user")
            the_id = 0
        if not current_user.is_authenticated or the_id != 1:
            return abort(403)
        else:
            return fun(*args, **kwargs)

    return decorated_function


@app.route("/new-post", methods=["POST", "GET"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["POST", "GET"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author_id=current_user.id,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author_id = current_user.id
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
