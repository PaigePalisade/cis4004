from flask import Flask, render_template, request
from flask_socketio import SocketIO
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your own secret key

socketio = SocketIO(app)

chatlog = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.emit('backlog', json.dumps(chatlog), to=request.sid)
    

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)

    obj = json.loads(data)

    print(obj["username"] + ": " + obj["message"])
    chatlog.append(obj)

    socketio.emit('newMessage', data)

if __name__ == '__main__':
    socketio.run(app, debug=True)