from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_login import login_user, current_user, logout_user, login_required, LoginManager
from flask_login import UserMixin #imports

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = ''
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = ''
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) #returns the user if logged in

class Post(db.Model): #class for each message posted
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(400), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)
    datestring = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    
    def __init__(self, title, body, date, expiry, user_id, username):
        self.title = title
        self.body = body
        self.date = date
        self.expiry = expiry
        self.datestring = date.strftime("%d-%m-%Y")
        self.user_id = user_id
        self.username = username

class User(db.Model, UserMixin): #class for every user
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.route('/')
@app.route('/home') #routes to home page
def home():
    posts = Post.query.order_by(Post.expiry) #returns all posts currently stored
    for each in posts:
        if each.expiry < datetime.now(): #if the post has expired, delete it
            db.session.delete(Post.query.get_or_404(each.id))
    db.session.commit() #commit all chanfes
    posts = Post.query.order_by(Post.date.desc()) #sort posts by most recent
    return render_template('bulletin.html', post = posts) #return webpage with the posts in

@app.route('/login', methods=['GET', 'POST']) #routes to login page
def login():
    if request.method == 'POST':
        loginuser = User(request.form['username'], request.form['password']) #gets login details that the user has inputed
        user = User.query.filter_by(username=loginuser.username).first() #returns user in database that first matches user input
        if user and (loginuser.password == user.password): #if inputed password matches expected password
            login_user(user) #login the user
            flash('You have been logged in.', 'success') #login message
            return redirect(url_for('home'))
        else:
            flash('Failed to login. Please check your username and password.') #failure message
    return render_template('bulletinlogin.html') #when page accessed use the correct html page

@app.route('/add', methods=['GET', 'POST'])
@login_required #require user to login before adding a post
def add():
    if request.method == 'POST':
        post = Post(request.form['title'], request.form['message'], datetime.now(), datetime.strptime(request.form['expiry'],'%Y-%m-%d'), current_user.id, current_user.username) #input required for post, user id is from login_manager
        db.session.add(post) 
        db.session.commit() #add post and commit
        flash('New message posted', 'success')
        return redirect(url_for('home'))
    return render_template('bulletinadd.html') #when page accessed use the correct html page

@app.route("/myposts") #posts currently displayed that the user has added themselves
@login_required
def my_posts():
    posts = (Post.query
             .order_by(Post.date.desc())
             .filter_by(user_id=current_user.id).all()) #sort by user first then most recent
    return render_template('bulletinmyposts.html', post = posts) #when page accessed use the correct html page, displaying the users posts

@app.route("/logout") #routes to logout page
@login_required
def logout():
    logout_user() #login_manager logs user out
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route("/delete", methods=['GET', 'POST']) #page routed to when delete button pressed
def delete():
    if request.method == 'POST':
        post_id = request.form['post_id']
        post = Post.query.get_or_404(post_id) #return info for post if it can be found
        if post.user_id != current_user.id: 
            abort(403) #only delete if user is user who posted
        db.session.delete(post)
        db.session.commit() #delete and commit
        flash('Your post has been deleted', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug = True)
