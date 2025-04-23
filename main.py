from flask import Flask, render_template, request, session, flash, redirect, url_for

from flask_socketio import SocketIO, join_room
import json

from passlib.hash import sha256_crypt

from PIL import Image

import re

from models import ExternalMessage, User, Message, Room, Bridge, db

from time import time

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db.init_app(app)
with app.app_context():
    db.create_all()

# git seemingly does not store empty paths, create a pfp directory if it doesn't exist
if not os.path.isdir('static/pfp'):
    os.mkdir('static/pfp')

socketio = SocketIO(app)

# routes

@app.route('/', methods=['GET', 'POST'])
def room_select():
    # check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for("welcome"))
    # validate user exists
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id')
        flash("There was an erorr reading your session, please login again")
        return redirect(url_for("login"))
    # join room
    if request.method == 'POST':
        roomname = request.form['room'].lower()
        error = False
        # validate room name
        if len(roomname) < 1 or len(roomname) > 20:
            flash("Room name must be between 1 and 20 characters")
            error = True
        if not re.match("^[a-z-]*$", roomname):
            flash("Room name must only contain English letters or dashes")
            error = True
        if error:
            return redirect(url_for('room_select'))
        room = Room.query.filter_by(name=roomname).first()
        # create room if it doesn't exist
        if not room:
            db.session.add(Room(name=roomname))
            db.session.commit()
        return redirect(url_for('chat', roomname=roomname))
        
        
    user = User.query.get(session['user_id'])
    return render_template('roomselect.html', username=user.username, display_name=user.display_name)

@app.route('/welcome')
def welcome():
    # check if user is logged in
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('welcome.html', user=user)

@app.route('/room/<roomname>')
def chat(roomname):
    # check if user is logged in
    roomname = roomname.lower()
    if 'user_id' not in session:
        return redirect(url_for("login"))
    # search for room, 404ing if it doesn't exist
    Room.query.filter_by(name=roomname).first_or_404()
    # give an error if user doesn't exist
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id')
        flash("There was an erorr reading your login")
        return redirect(url_for("login"))
    return render_template('chat.html', user=user, roomname=roomname)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # get user information from form
        username = request.form['username'].lower()
        display_name = request.form['displayname']
        password = request.form['password']

        # validate user information
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
        if not re.match("^[a-z-]*$", username):
            flash("Username must only contain english letters or dashes")
            error = True
        if User.query.filter_by(username=username).first():
            flash("Username already exists (not case sensitive)")
            error = True
        # if user sends a profile picture, resize it to (70,70), otherwise use the default profile picture
        if 'profile-picture' in request.files and request.files['profile-picture']:
            file = request.files['profile-picture']
            try:
                pfp = Image.open(file)
                pfp = pfp.resize((70,70))
            except:
                flash("Could not read pfp")
                error = True
        else:
            pfp = Image.open("static/default_pfp.png")
        if (error):
            return redirect(url_for('register'))

        # securely salt and hash the password before storage
        password = sha256_crypt.hash(password)

        # add the user to the database
        usr = User(username = username, display_name=display_name, password=password)
        db.session.add(usr)
        db.session.commit()
        # using webp to annoy people
        pfp.save(f"static/pfp/{username}.webp")
        # save the user_id as a cookie to the user's session
        session['user_id'] = usr.id
        return redirect(url_for('room_select'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('welcome'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get user information from form
        username = request.form['username'].lower()
        password = request.form['password']

        # validate
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
            # check password
            elif not sha256_crypt.verify(password, user.password):
                flash("Invalid password")
                error = True
            if not error:
                # log user in and redirect to the room select page
                session['user_id'] = user.id
                return redirect(url_for('room_select'))
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/update', methods=['GET', 'POST'])
def update():
    # check if user is logged in
    if not 'user_id' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        display_name = request.form['displayname']
        # validate display name
        error = False
        if len(display_name) < 1 or len(display_name) > 20:
            flash("Display Name must be between 1 and 20 characters")
            error = True
        if error:
            return redirect(url_for('update'))
        User.query.get(session['user_id']).display_name = display_name
        db.session.commit()
        # attempt to save profile picture if the user sent it
        if 'profile-picture' in request.files and request.files['profile-picture']:
            file = request.files['profile-picture']
            try:
                pfp = Image.open(file)
                pfp = pfp.resize((70,70))
                pfp.save(f"static/pfp/{User.query.get(session['user_id']).username}.webp")
            except:
                flash("Could not read pfp")
                error = True
        if error:
            return redirect(url_for('update'))
        # redirect to room select page
        return redirect(url_for('room_select'))
    # fill out the display name for the user using a render template
    display_name = User.query.get(session['user_id']).display_name
    return render_template('update.html', display_name=display_name)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    # check if user is logged in
    if not 'user_id' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        password = request.form['password']
        new_password = request.form['new-password']
        user = User.query.get(session['user_id'])
        error = False
        # validate password
        if len(new_password) < 5 or len(new_password) > 20:
            flash("Password must be between 5 and 20 characters")
            error = True
        # check current password
        if not sha256_crypt.verify(password, user.password):
            flash("Current password does not match")
            error = True
        if error:
            return redirect(url_for('change_password'))
        # set new password and save to database
        new_password = sha256_crypt.hash(new_password)
        user.password = new_password
        db.session.commit()
        return redirect(url_for('update'))
    return render_template('password.html')
    
# socketio
# web client
@socketio.on('connect')
def handle_connect():
    print('Client connected')

# gets a list of messages from the database, sorts them, and sends them to the user in json
@socketio.on('getBacklog')
def get_backlog(roomname):
    join_room(roomname)
    messages = db.session.execute(db.select(Message).filter_by(room=roomname))
    external_messages = db.session.execute(db.select(ExternalMessage).filter_by(room=roomname))
    chatlog = []
    for msg in messages:
        user = User.query.filter_by(username=msg[0].username).first()
        chatlog.append({"username": msg[0].username, "body": msg[0].body, 'displayname': user.display_name, 'timestamp': msg[0].timestamp, 'pfp': f'/static/pfp/{msg[0].username}.webp'})
    for msg in external_messages:
        chatlog.append({"username": msg[0].username, "body": msg[0].body, 'displayname': msg[0].display_name, 'timestamp': msg[0].timestamp, 'pfp': msg[0].pfp})
    chatlog.sort(key = lambda x: x['timestamp'])
    socketio.emit('backlog', json.dumps(chatlog), to=request.sid)

# handles a message, sends them to every web client user on the channel and to the discord bot
@socketio.on('message')
def handle_message(data):

    obj = json.loads(data)
    body = obj['body']
    roomname = obj['roomname']

    if 'user_id' in session and Room.query.filter_by(name=roomname).first():
        
        msg = Message(username=User.query.get(session['user_id']).username, body=body, room=roomname, timestamp=int(time() * 1000))
        db.session.add(msg)
        db.session.commit()

        display_name = User.query.get(session['user_id']).display_name

        socketio.emit('newMessage', json.dumps({'username': msg.username, 'body': msg.body, 'displayname': display_name, 'timestamp': msg.timestamp, 'pfp': f'/static/pfp/{msg.username}.webp'}), to=roomname)
        bridges = Bridge.query.filter_by(internal_channel=roomname)
        for bridge in bridges:
            pfp = f'{request.root_url}/static/pfp/{msg.username}.webp'
            # Discord would not be able to fetch the pfp if the server is running on localhost
            if request.root_url == 'http://localhost:5000/':
                pfp = 'https://docs.pycord.dev/en/stable/_static/pycord_logo.png'
            socketio.emit('new-discord-message', json.dumps({'body': msg.body, 'display_name': display_name, 'pfp': pfp, 'channel': bridge.external_channel, 'webhook': bridge.webhook}), to='$discord')


# interfacing with discord bot

# receives a message from the Discord bot and sends it to the web clients
@socketio.on('discord-message')
def handle_discord_message(data):
    # Discord bot must be local
    if request.root_url != 'http://localhost:5000/':
        print('Discord bot not local')
        return
    obj = json.loads(data)
    bridges = Bridge.query.filter_by(external_channel=obj['channel'])
    for bridge in bridges:
        roomname = bridge.internal_channel
        msg = ExternalMessage(username=f'{obj["username"]}@discord', display_name=obj['display_name'], pfp=obj['pfp'], body=obj['body'], room=roomname, timestamp=int(time() * 1000))
        db.session.add(msg)
        db.session.commit()
        socketio.emit('newMessage', json.dumps({'username': f'{msg.username}', 'body': msg.body, 'displayname': msg.display_name, 'timestamp': msg.timestamp, 'pfp': msg.pfp}), to=roomname)

# creates a "bridge", a database entry containing the discord channel id and the room name
@socketio.on('create-bridge')
def create_bridge(data):
    if request.root_url != 'http://localhost:5000/':
        print('Discord bot not local')
        return
    obj = json.loads(data)
    if Room.query.filter_by(name=obj['internal_channel']).first():
        bridge = Bridge(internal_channel=obj['internal_channel'], external_channel=obj['external_channel'], webhook=obj['webhook'])
        db.session.add(bridge)
        db.session.commit()
        return 'Success'
    else:
        return 'Failed to create bridge, make sure the room name is correct'

# removes all bridge entries for a given discord channel
@socketio.on('remove-bridge')
def remove_bridge(data):
    if request.root_url != 'http://localhost:5000/':
        print('Discord bot not local')
        return
    bridges = Bridge.query.filter_by(external_channel=data)
    for bridge in bridges:
        db.session.delete(bridge)
        db.session.commit()
    return 'Success'

# adds the discord bot connection to a special socket.io room
@socketio.on('discord-init')
def discord_init(data):
    if request.root_url != 'http://localhost:5000/':
        print('Discord bot not local')
        return
    # dollar sign is invalid for room name, so this won't conflict
    join_room('$discord')


if __name__ == '__main__':
    socketio.run(app, debug=True)
    app.run(debug=True)