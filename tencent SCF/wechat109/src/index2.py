from flask import Flask
from flask import request
from flask import make_response
app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def home():
    resp = make_response('<h1>Home</h1>', 200)
    return resp
@app.route('/signin', methods=['GET'])
def signin_form():
    # action url 中的service_name,function_name need replace
    html = '''<form action="/2016-08-15/proxy/service_name/func_name/signin" method="post">
         <p><input name="username"></p>
         <p><input name="password" type="password"></p>
         <p><button type="submit">Sign In</button></p>
         </form>'''
    resp = make_response(html, 200)
    return resp
@app.route('/signin', methods=['POST'])
def signin():
    if request.form['username'] == 'admin' and request.form['password'] == 'password':
        html = '<h3>Hello, admin!</h3>'
    else:
        html = '<h3>Bad username or password.</h3>'
    resp = make_response(html, 200)
    return resp
@app.route('/signin2', methods=['GET'])
def signin2():
    if request.args.get('username') == 'admin' and request.args.get('password') == 'password':
        html = '<h3>Hello2, admin!</h3>'
    else:
        html = '<h3>Bad username or password.</h3>'
    resp = make_response(html, 200)
    return resp
def main_handler(event, context):
    # maybe pre do something here
    return app(event, context)