from flask import Flask, render_template, request, session, flash, redirect, url_for

from flask_socketio import SocketIO, join_room
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
    room: Mapped[str]

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str]
    password: Mapped[str]

class Room(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

with app.app_context():
    db.create_all()
    
socketio = SocketIO(app)

@app.route('/', methods=['GET', 'POST'])
def landing():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    if request.method == 'POST':
        roomname = request.form['room'].lower()
        error = False
        if len(roomname) < 1 or len(roomname) > 20:
            flash("Room name must be between 1 and 20 characters")
            error = True
        if not roomname.isalpha:
            flash("Room name must only contain English letters")
            error = True
        if error:
            return redirect(url_for('landing'))
        room = Room.query.filter_by(name=roomname).first()
        if not room:
            db.session.add(Room(name=roomname))
            db.session.commit()
        return redirect(url_for('chat', roomname=roomname))
        
        
    user = User.query.get(session['user_id'])
    return render_template('index.html', username=user.username, display_name=user.display_name)

@app.route('/room/<roomname>')
def chat(roomname):
    roomname = roomname.lower()
    if 'user_id' not in session:
        return redirect(url_for("login"))
    Room.query.filter_by(name=roomname).first_or_404()
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id')
        flash("There was an erorr reading your login")
        return redirect(url_for("login"))
    return render_template('chat.html', user=user, roomname=roomname)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()
        display_name = request.form['displayname']
        password = request.form['password']

        error = False

        if len(username) < 2 or len(username) > 20:
            flash("Username must be between 2 and 20 characters")
            error = True
        if len(display_name) < 1 or len(display_name) > 20:
            flash("Display Name must be between 1 and 20 characters")
            error = True
        if len(password) < 5 or len(password) > 20:
            flash("Password must be between 5 and 20 characters")
            error = True
        if not username.isalpha():
            flash("Username must only contain english letters")
            error = True
        if User.query.filter_by(username=username).first():
            flash("Username already exists (not case sensitive)")
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
        username = request.form['username'].lower()
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
    return render_template('login.html')

@app.route('/update', methods=['GET', 'POST'])
def update():
    if not 'user_id' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        display_name = request.form['displayname']
        error = False
        if len(display_name) < 1 or len(display_name) > 20:
            flash("Display Name must be between 1 and 20 characters")
            error = True
        if error:
            return redirect(url_for('update'))
        User.query.get(session['user_id']).display_name = display_name
        db.session.commit()
        if 'profile-picture' in request.files and request.files['profile-picture']:
            file = request.files['profile-picture']
            try:
                pfp = Image.open(file)
                pfp.resize((70,70))
                pfp.save(f"static/pfp/{User.query.get(session['user_id']).username}.webp")
            except:
                flash("Could not read pfp")
                error = True
        if error:
            return redirect(url_for('update'))
        return redirect('/')
    display_name = User.query.get(session['user_id']).display_name
    return render_template('update.html', display_name=display_name)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not 'user_id' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        password = request.form['password']
        new_password = request.form['new-password']
        user = User.query.get(session['user_id'])
        error = False
        if len(new_password) < 5 or len(new_password) > 20:
            flash("Password must be between 5 and 20 characters")
            error = True
        if not sha256_crypt.verify(password, user.password):
            flash("Current password is invalid")
            error = True
        if error:
            return redirect(url_for('change_password'))
        new_password = sha256_crypt.hash(new_password)
        user.password = new_password
        db.session.commit()
        return redirect(url_for('update'))
    return render_template('password.html')
    

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('getBacklog')
def get_backlog(roomname):
    print(roomname)
    join_room(roomname)
    messages = db.session.execute(db.select(Message).filter_by(room=roomname))
    chatlog = []
    for msg in messages:
        display_name = User.query.filter_by(username=msg[0].username).first().display_name
        chatlog.append({"username": msg[0].username, "body": msg[0].body, 'displayname': display_name})
    socketio.emit('backlog', json.dumps(chatlog), to=request.sid)
    

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)

    obj = json.loads(data)
    body = obj['body']
    roomname = obj['roomname']

    if 'user_id' in session and Room.query.filter_by(name=roomname).first():
        
        msg = Message(username=User.query.get(session['user_id']).username,body=body, room=roomname)
        db.session.add(msg)
        db.session.commit()

        display_name = User.query.get(session['user_id']).display_name

        socketio.emit('newMessage', json.dumps({'username': msg.username, 'body': msg.body, 'displayname': display_name}), to=roomname)

if __name__ == '__main__':
    socketio.run(app, debug=True)
    app.run(debug=True)