import os

from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_session import Session
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import time, datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key =  "MySuperKey#345"
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

os.environ["DATABASE_URL"] = "postgres://vedwvdirbmqnfe:d8fc2a33e1ff34ce8de80a29358ea68854a2f0b71c4d260a9dd38731358de04b@ec2-54-217-213-79.eu-west-1.compute.amazonaws.com:5432/d1npe0np69aa3f";
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

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

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/submitted", methods=["POST"])
def submitted():
    name = request.form.get("name")
    usrname = request.form.get("usrname")
    pwd = request.form.get("pwd");
    age = request.form.get("age");
    country = request.form.get("country");
    if not name or not usrname or not pwd or not age or not country:
        flash('Please fill all requested forms')
    #check if same username or email already exist
    elif db.execute("SELECT * FROM degachatusers WHERE username = :usrname", {"usrname": usrname}).rowcount != 0:
        flash('This username is already in use, please choose another one')
    elif len(pwd) < 4:
        flash('Password must be at least 4 characters long')

    #load data into Heroku database
    else:
        db.execute("INSERT INTO degachatusers (name, username, password, age, country) VALUES (:name, :username, :password, :age, :country)",
                {"name": name, "username": usrname, "password": pwd, "age": age, "country": country})
        db.commit()

        #render html page
        # userData = [];
        # userData.append(name);
        # userData.append(usrname);
        # session['users'] = users;
        # session['logged_user'] = usrname;
        # session['users'].append(usrname);
        flash('Succesfully registered! Now please login')
        return redirect("/")
    return redirect(url_for('register'))

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        session.pop('logged_user', None);
        user = request.form.get("username")
        passw = request.form.get("password")
        loggedUser = db.execute("SELECT username, id FROM degachatusers WHERE username=(:user)",
                    {"user": user}).fetchone();
        if not loggedUser:
            flash('Wrong username or password. Please try again')
        else:
            #get password corresponding to the user saved on db
            dbPwd = db.execute("SELECT password FROM degachatusers WHERE username=(:loggedUser)",
                                        {"loggedUser": loggedUser[0]}).fetchone()
            db.commit();
            if passw==dbPwd[0]: #user has succesfully logged in
                session['users'] = users;
                session['logged_user'] = user;
                session['users'].append(user);
                return redirect(url_for('chat'))
            else:
                flash('Wrong username or password. Please try again')
    if 'logged_user' in session:
        return redirect(url_for('chat'))
    return redirect("/")

@app.route("/chat", methods=["POST", "GET"])
def chat():
    # if request.method == 'POST':
    #     session.pop('logged_user', None);
    #     username = request.form.get("username");
    #     session['users'] = users;
    #     session['logged_user'] = username;
    #     session['users'].append(username);
    #     return render_template("chat.html", username=username, channel_list=channel_list, users=session['users'])
    if 'logged_user' not in session:
        flash('Please login first')
        return redirect("/")
    else:
        session['channel_list'] = channel_list;
        return render_template("chat.html", username=session['logged_user'], channel_list=session['channel_list'], users=session['users'])

@app.route("/logout")
def logout():
    user = session['logged_user']
    session['users'].remove(user);
    session.pop('logged_user', None);
    # session.clear()
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
