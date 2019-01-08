from flask import Flask, current_app, url_for

#SERVER_NAME = 'mydomain.com'
app = Flask(__name__)


with app.app_context(), app.test_request_context():
    print(url_for('static', filename="Users/brend/Downloads/cego.jpg", _external=True))