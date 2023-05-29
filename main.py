from flask import Flask, render_template, request
import requests
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.environ.get('EMAIL')
PASSWORD = os.environ.get('PASSWORD')
all_posts = requests.get('https://api.npoint.io/e804a12b698002b4dc64').json()
app = Flask(__name__)


@app.route('/')
def get_home_page():
    return render_template('index.html', posts = all_posts)


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/contact', methods = ['GET', 'POST'])
def contact_page():
    if request.method == 'GET':
        return render_template('contact.html')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        print(name, email, phone, message)
        with smtplib.SMTP('smtp.gmail.com',587) as connection:
            connection.starttls()
            connection.login(EMAIL, PASSWORD)
            connection.sendmail(
                from_addr=EMAIL, 
                to_addrs='jvdpt0@gmail.com',
                msg= f'Subject: New Form Submit! \n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}'.encode('utf-8')
                )
            return "<h1>Succesfully sent your message</h1>"
        


@app.route('/post/<int:id>')
def get_post(id):
    return render_template('post.html', id=id, posts = all_posts)


if __name__ == '__main__':
    app.run(debug=True)