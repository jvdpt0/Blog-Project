from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
db = SQLAlchemy()
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,user_id)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

##CONFIGURE TABLE
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User",lazy='subquery', back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment",lazy='subquery', back_populates="parent_post")

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = relationship("BlogPost", lazy='subquery', back_populates="author")
    comments = relationship("Comment", lazy='subquery', back_populates="comment_author")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", lazy='subquery', back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()


@app.route('/')
def get_all_posts():
    with app.app_context():
        posts = db.session.query(BlogPost).all()
    return render_template("index.html", all_posts=posts, current_user = current_user)


@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if db.session.query(User).filter_by(email=form.email.data).first():
            flash('Email already signed up, log in instead.')
            return redirect(url_for('login'))
        with app.app_context():
            new_user = User(
                email = form.email.data,
                password = generate_password_hash(password=form.password.data, method='pbkdf2:sha256', salt_length=8),
                name = form.name.data
            )
            db.session.add(new_user)
            db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if not user:
            flash('Email does not exist, try again.')
            return redirect(url_for('login'))
        if not check_password_hash(user.password, password):
            flash('Incorrect password, try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    form = CommentForm()
    with app.app_context():
        requested_post = db.session.get(BlogPost, post_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for('login'))
        with app.app_context():
            new_comment = Comment(
                text=form.body.data,
                comment_author=current_user,
                parent_post=requested_post
                )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))
    return render_template("post.html", post=requested_post, current_user = current_user, form=form)


@app.route("/about")
def about():
    return render_template("about.html", current_user = current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user = current_user)


@app.route('/new-post', methods=['GET','POST'])
@admin_only
def new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        with app.app_context():
            new_post = BlogPost(
                title = form.title.data,
                subtitle = form.subtitle.data,
                date = date.today().strftime("%B %d, %Y"),
                body = form.body.data,
                author = current_user,
                img_url = form.img_url.data
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('get_all_posts', current_user = current_user))
    return render_template('make-post.html', form=form, current_user = current_user)


@app.route('/edit-post/<int:post_id>', methods=['GET','POST'])
@admin_only
def edit_post(post_id):
    post = db.session.get(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        with app.app_context():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            post.author = edit_form.author.data
            post.body = edit_form.body.data
            db.session.merge(post)
            db.session.commit()
        return redirect(url_for('show_post', post_id = post.id, current_user = current_user))
    return render_template('make-post.html', form = edit_form, is_edit=True, current_user = current_user)


@app.route('/delete/<int:post_id>')
@admin_only
def delete_post(post_id):
    with app.app_context():
        post = db.session.get(BlogPost, post_id)
        if post:
            db.session.delete(post)
            db.session.commit()
    return redirect(url_for('get_all_posts', current_user = current_user))


if __name__ == '__main__':
    app.run(debug=True)