from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_socketio import SocketIO
import json

from sqlalchemy import Integer, String
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from passlib.hash import sha256_crypt

from PIL import Image

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your own secret key

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    body: Mapped[str]

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str]
    password: Mapped[str]

with app.app_context():
    db.create_all()

socketio = SocketIO(app)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id')
        flash("There was an erorr reading your login")
        return redirect(url_for("login"))
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        display_name = request.form['displayname']
        password = request.form['password']

        error = False

        if len(username) < 2 or len(username) > 10:
            flash("Username must be between 2 and 10 characters")
            error = True
        if len(display_name) < 1 or len(display_name) > 10:
            flash("Display Name must be between 1 and 10 characters")
            error = True
        if len(password) < 5 or len(password) > 10:
            flash("Password must be between 5 and 10 characters")
            error = True
        if 'profile-picture' in request.files and request.files['profile-picture']:
            file = request.files['profile-picture']
            try:
                pfp = Image.open(file)
                pfp.resize((70,70))
            except:
                flash("Could not read pfp")
                error = True
        else:
            pfp = Image.open("static/default_pfp.png")
        if (error):
            return redirect(url_for('register'))

        password = sha256_crypt.hash(password)

        usr = User(username = username, display_name=display_name, password=password)
        db.session.add(usr)
        db.session.commit()
        # using webp to annoy people
        pfp.save(f"static/pfp/{username}.webp")
        session['user_id'] = usr.id
        return redirect('/')
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        error = False

        if not username:
            flash("Please enter a valid username")
            error = True
        if not password:
            flash("Please enter a valid password")
            error = True

        if not error:
            user = User.query.filter_by(username=username).first()
            if not user:
                flash("Not a valid user")
                error = True
            elif not sha256_crypt.verify(password, user.password):
                flash("Invalid password")
                error = True
            if not error:
                session['user_id'] = user.id
                return redirect('/')
        return redirect(url_for('login'))

        session['user_id'] = usr.id
        return redirect('/')
    return render_template('login.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    messages = db.session.execute(db.select(Message))
    chatlog = []
    for msg in messages:
        chatlog.append({"username": msg[0].username, "message": msg[0].body})
    socketio.emit('backlog', json.dumps(chatlog), to=request.sid)
    

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)

    if 'user_id' in session:
        msg = Message(username=User.query.get(session['user_id']).username,body=data)
        db.session.add(msg)
        db.session.commit()

        socketio.emit('newMessage', json.dumps({'username': msg.username, 'message': msg.body}))

if __name__ == '__main__':
    socketio.run(app, debug=True)