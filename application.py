import os

from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_session import Session
from flask_socketio import SocketIO, emit, send, join_room, leave_room
import requests
import time, datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key =  "MySuperKey#345"
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

channel_list = [''];
old_messages = defaultdict(list);
users=[];

@app.before_request
def setup():
    session.permanent = True

@app.route("/")
def index():
    if 'logged_user' not in session:
        return render_template("index.html")
    else:
        return render_template("index.html")

@app.route("/chat", methods=["POST", "GET"])
def chat():
    if request.method == 'POST':
        session.pop('logged_user', None);
        username = request.form.get("username");
        session['users'] = users;
        if len(username) < 4:
            flash('Username must be at least 4 characters long')
            return redirect("/")
        elif len(username) > 13:
            flash('Please enter a shorter username')
            return redirect("/")
        elif username in session['users']:
            flash('This username already exists')
            return redirect("/")
        else:
            session['logged_user'] = username;
            session['users'].append(username);
            return render_template("chat.html", username=username, channel_list=channel_list, users=session['users'])
    if 'logged_user' not in session:
        flash('Please login first')
        return redirect("/")
    else:
        session['channel_list'] = channel_list;
        return render_template("chat.html", username=session['logged_user'], channel_list=session['channel_list'], users=session['users'])
@app.route("/logout")
def logout():
    session.pop('logged_user', None);
    session.clear()
    return redirect("/")


@app.route("/redirect_newchannel", methods=["POST"])
def redirect_newchannel():
    new_channel = request.form.get("channel")
    session['channel_list'] = channel_list;

    if new_channel in session['channel_list']:
        flash('Channel already exists, please try another name')
        return redirect(url_for("chat"))
    else:
        session['channel_list'].append(new_channel)
        return redirect(url_for("channel", joined_channel=new_channel))

@app.route("/channel/<joined_channel>")
def channel(joined_channel):
    if 'logged_user' not in session:
        flash('Please login first')
        return render_template("index.html")
    else:
        session['joined_channel'] = joined_channel;
        return render_template("channel.html", joined_channel=joined_channel, username=session['logged_user'], old_msg=old_messages[joined_channel])

@socketio.on("text to send")
def text_to_send(text):
    # get user who sent the current message
    user = session['logged_user']
    room = session['joined_channel'];

    # if number of msg is >100 delete the oldest one before appending the last one
    if len(old_messages[room]) > 100:
        del(old_messages[room])[0]

    # get timestamp
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

    # saving text messages
    old_messages[room].append([user, timestamp, text]);

    join_room(room)
    # emit("send text", {"text": text, "user": user, "timestamp": timestamp}, broadcast=True)
    emit("send text", {"text": text, "user": user, "timestamp": timestamp}, room=room)

@socketio.on('join')
def on_join():
    username = session['logged_user']
    room = session['joined_channel']
    join_room(room)
    emit("joined", {"user": username, "channel": room}, room=room)

@socketio.on('leave')
def on_leave():
    username = session['logged_user']
    room = session['joined_channel']
    leave_room(room)
    emit("left", {"user": username}, room=room)

@socketio.on('delete_last_msg')
def del_msg():
    room = session['joined_channel']
    del(old_messages[room])[-1]
    join_room(room)
    emit("remove_delete_button", room=room)

if __name__ == "__main__":
    app.run()
