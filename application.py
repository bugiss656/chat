import os
from time import localtime, strftime

from flask import Flask, flash, session, render_template, url_for, redirect, request, logging
from flask_session import Session
from functools import wraps
from flask_socketio import SocketIO, send, emit, join_room, leave_room


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)



class User:
    def __init__(self, name):
        self.name = name



class Channel:
    def __init__(self, channel_name, creator):
        self.channel_name = channel_name
        self.creator = creator



users = []
channels = []
messages = []




@app.route("/", methods=['GET', 'POST'])
def index():
    if 'name' in session and 'current_channel' in session:

        return redirect(url_for('channel', name=session['current_channel']))
    elif 'name' in session:

        return redirect(url_for('dashboard'))

    name = request.form.get('name')

    if request.method == 'POST':
        user = User(name)

        if user.name == '':
            flash('Incorrect username, please try again.', 'danger')
        elif user.name in users:
            session['name'] = user.name

            return redirect(url_for('dashboard'))
        else:
            users.append(user.name)
            session['name'] = user.name

            return redirect(url_for('dashboard'))

    return render_template('index.html')



@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html', channels=channels)



@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for('index'))



@app.route("/createChannel", methods=['GET', 'POST'])
def createChannel():
    channel_name = request.form.get('channelName')

    if request.method == 'POST':
        channel_object = Channel(channel_name, session['name'])

        channel_list = [ channel['channel_name'] for channel in channels ]

        if channel_object.channel_name in channel_list:
            flash('Channel name already exist, please try again.', 'danger')
        else:
            channels.append({
                'channel_name': channel_object.channel_name,
                'creator': channel_object.creator
            })

            return redirect(url_for('dashboard'))

    return render_template('createChannel.html')



def deleteMessagesData(name, message_data):
    msg_del_result = [message for message in message_data if not (message['on_channel'] == name)]
    message_data.clear()
    message_data += msg_del_result

    return message_data



def deleteChannelData(name, channel_data):
    chnl_del_result = [channel for channel in channel_data if not (channel['channel_name'] == name)]
    channel_data.clear()
    channel_data += chnl_del_result

    return channel_data



@app.route('/deleteChannel/<string:name>')
def deleteChannel(name):
    deleteMessagesData(name, messages)
    deleteChannelData(name, channels)

    return redirect(url_for('dashboard', channels=channels))



@app.route('/channel/<string:name>')
def channel(name):
    session['current_channel'] = name

    return render_template('channel.html', messages=messages)



@app.route('/leaveChannel')
def leaveChannel():
    session.pop('current_channel', None)

    return redirect(url_for('dashboard'))



@socketio.on('message')
def message(data):
    message = data['message']
    user = data['user']
    timestamp = strftime('%H:%M | %d %B %Y', localtime())

    if len(messages) == 100:
        messages.pop(0)

        messages.append({
            'message': message,
            'user': user,
            'date': timestamp,
            'on_channel': session['current_channel']
        })
    else:
        messages.append({
            'message': message,
            'user': user,
            'date': timestamp,
            'on_channel': session['current_channel']
        })

    send({'message': message, 'user': user, 'timestamp': timestamp}, room=data['room'])



@socketio.on('join')
def join(data):
    join_room(data['room'])



@socketio.on('leave')
def leave(data):
    leave_room(data['room'])




if __name__ == '__main__':
    socketio.run(app, debug=True)
