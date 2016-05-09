from flask import Flask, render_template, redirect, request, session, flash
from mysql_theWall import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')
PASSWORD_REGEX = re.compile(r'^([^0-9]*|[^A-Z]*)$')
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "ThisIsSecret!"
mysql = MySQLConnector(app,'the_wall')
@app.route('/', methods=['GET'])
def index():
	return render_template('main.html')
@app.route('/wall', methods = ['GET'])
def wall():
	all_messages = mysql.query_db("SELECT messages.user_id, messages.message, messages.id AS message_id, messages.created_at, concat(users.first_name, ' ', users.last_name) as name FROM messages LEFT JOIN users ON users.id = messages.user_id ORDER BY messages.created_at DESC;")
	all_comments = mysql.query_db("SELECT comments.id AS comment_id, comments.comment, comments.created_at, message_id, user_id, concat(users.first_name, ' ', users.last_name) AS name FROM comments LEFT JOIN users ON users.id = comments.user_id ORDER BY comments.created_at ASC;")
	# print all_comments
	return render_template('wall_page.html', all_messages = all_messages, all_comments = all_comments)	
@app.route('/register', methods =['POST'])
def register():
	error = 1
	if len(request.form['first_name']) < 2 or not request.form['first_name'].isalpha():
		flash("Invalid First Name. (Letters only, at least 2 characters.)")
	if len(request.form['last_name']) < 2 or not request.form['last_name'].isalpha():
		flash("Invalid Last Name. (Letters only, at least 2 characters.)")
	if len(request.form['email']) < 1 or not EMAIL_REGEX.match(request.form['email']):
		flash ("Invalid Email Address!")   	
	if len(request.form['password']) < 8 :
		flash("Password should be more than 8 characters")
	if not request.form['password'] != request.form['confirm_password']:
		flash ("Password do not match. Try again!")
	if PASSWORD_REGEX.match(request.form['confirm_password']):
		flash("Password requires to have at least 1 uppercase letter and 1 numeric value ")
	else:  
		error = 0
		data = {'first_name' : request.form['first_name'],'last_name' : request.form['last_name'],'email' : request.form['email'],'pw_hash' : bcrypt.generate_password_hash(request.form['password'])}
		query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :pw_hash, NOW(), NOW())"
		mysql.query_db(query,data)
		return redirect ('/wall')
	return redirect('/')
@app.route('/login', methods = ['POST'])
def login():
		query = "SELECT * FROM users WHERE email = :email LIMIT 1"
		data = {'email' : request.form['email']}
		user = mysql.query_db(query,data) 
		print user
		if len(request.form['password']) < 8 or not EMAIL_REGEX.match(request.form['email']) or user == [] or not bcrypt.check_password_hash(user[0]['password'], request.form['password']):	
			flash ("Invalid Email/Password!") 
			return redirect('/')
		else:
			user_query = "SELECT  * FROM users"
			mysql.query_db(user_query)
			session['user_id'] = user[0]['id']
			session['user_name'] = user[0]['first_name']
			return redirect ('/wall')
@app.route('/logoff')
def logoff():
    session.clear()
    return redirect('/')
@app.route('/message', methods = ['POST'])
def post_message():
	if request.form['message'] != '':
		query2 = "INSERT INTO messages(message, created_at, updated_at, user_id) VALUES(:message, now(), now(), :id);"
		data2 = {'message': request.form['message'],'id': session['user_id']}
		mysql.query_db(query2, data2)
		return redirect ('/wall')
	return redirect ('/wall')
@app.route('/delete/<id>', methods=['GET'])
def delete(id):
    query = "DELETE FROM messages WHERE id = :id"
    data = {
           'id': id
           }
    mysql.query_db(query, data)
    return redirect ('/wall')
@app.route('/comment', methods=['POST'])
def comment():
	if request.form['comment'] != '':
		query = "INSERT INTO comments (message_id, user_id, comment, created_at, updated_at) VALUES (:message_id, :user_id, :comment, NOW(), NOW());"
		data = { 'message_id': request.form['message_id'], 'user_id': session['user_id'], 'comment': request.form['comment'] }
		print query
		print data
		mysql.query_db(query, data)
		return redirect('/wall')
	return redirect('/wall')
app.run(debug=True)