#!/usr/bin/env python3.4

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# http://electronicsbyexamples.blogspot.com/2014/02/raspberry-pi-control-from-mobile-device.html




async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

# monkey patching is necessary because this application uses a background
# thread
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
    print("hit patching code for eventlet")
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()
    print("hit patching code for gevent")



import time
from threading import Thread
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect





from flask import Flask, render_template, session, request, jsonify
import comms.comms as comms # encapsulates communication technology
import ssl # for hand-crafted ssl context enabling TLS?
from flask_httpauth import HTTPBasicAuth
import json # transferring data over comms, format of data model
#from flask.ext.socketio import SocketIO, emit

users = {
    "david":"secret",
    "susan":"secret"
}

app = Flask(__name__)
auth = HTTPBasicAuth()
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        time.sleep(10)
        count += 1
        socketio.emit('my response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')

@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})

@socketio.on('close room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@sio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)





@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None


# ajax GET call this function to set led state
# depeding on the GET parameter sent
@app.route("/arm")
def arm():
    zone = request.args.get('zone')
    state = request.args.get('state')
    print("request %s:%s" % (zone,state))
    if state=="on":
        print("SendCommand(%s, arm)" % zone)
        SendCommand([zone, "arm"])
        pass
    else:
        print("SendCommand(%s, disarm)" % zone)
        SendCommand([zone, "disarm"])
        pass
    #print("global variable is hopefully one: %s" % getGlobval())
    GetStatus()
    return ""

# ajax GET call this function periodically to read button state
# the state is sent back as json data
@app.route("/_button")
def _button():
    if True:
        state = "pressed"
    else:
        state = "not pressed"
    return jsonify(buttonState=state)

def GetUptime():
    # get uptime from the linux terminal command
    from subprocess import check_output
    output = check_output(["uptime"]).decode('utf-8')
    # return only uptime info
    uptime = output[output.find("up"):output.find("user")-5]
    return uptime

def SendCommand(command):
    comm_channel = comms.PubChannel("tcp://*:5563")
    time.sleep(1) # zmq slow joiner syndrome, should sync instead
    comm_channel.send("control_events", [command])
    comm_channel.close()

def getComms():
    """Opens a new listening connection if there is none yet for the
    current application context.
    """
    return comms.SubChannel("tcp://state1:5564", ['sensor_events','control_events', 'state'])


def GetStatus():
    #if rv is not None:
        #[address, contents] = rv
        #mydata = json.loads(contents.decode('utf8'))
        #for zone in mydata['zones']:
            #print( "zone %s armed status: %s" % (zone, mydata['zones'][zone]['armed'] ))
    pass



 # return index page when IP address of RPi is typed in the browser
@app.route("/")
@auth.login_required
def Index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()

    zones={"Upper Windows":"disarmed","Lower Windows":"armed","Doors":"disarmed","Inside Motion":"unarmed"}
    return render_template("index.html", uptime=GetUptime(), zones=zones )

@app.teardown_appcontext
def teardown_connecteion(exception):
    print("teardown") 

# run the webserver on standard port 80, requires sudo
if __name__ == "__main__":
    
    #context = ( 'hsec.crt', 'hsec.key')
    #app.run(host='0.0.0.0', ssl_context=context, debug=True, gevent=100)
    #context = ssl.SSLContext(ssl.PROTOCOL_SSLv3 )
    #context = ssl.SSLContext(ssl.PROTOCOL_SSLv2 )
    #context.set_ciphers('SSL_RSA_WITH_3DES_EDE_CBC_SHA')
    #context.load_cert_chain(certfile="hsec.crt", keyfile="hsec.key")
    #socketio.run(app, host='0.0.0.0', ssl_context=context, debug=False)
    socketio.run(app, host='0.0.0.0', debug=True, certfile="hsec.crt", keyfile="hsec.key")
