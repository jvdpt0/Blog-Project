from flask import Flask, render_template
import requests


all_posts = requests.get('https://api.npoint.io/e804a12b698002b4dc64').json()
app = Flask(__name__)


@app.route('/')
def get_home_page():
    return render_template('index.html', posts = all_posts)


@app.route('/post/<int:id>')
def get_post(id):
    return render_template('post.html', id=id, posts = all_posts)

@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/contact')
def contact_page():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)