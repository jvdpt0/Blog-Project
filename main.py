from flask import Flask, render_template
import requests

app = Flask(__name__)

blog_url = 'https://api.npoint.io/c790b4d5cab58020d391'
all_posts = requests.get(blog_url).json()


@app.route('/')
def home():
    return render_template("index.html", posts=all_posts)


@app.route('/post/<int:id>')
def get_post(id):
    return render_template("post.html", id=id , posts=all_posts)


if __name__ == "__main__":
    app.run(debug=True)
