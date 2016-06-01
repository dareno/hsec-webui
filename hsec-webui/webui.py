#!/usr/bin/env python3.4

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# http://electronicsbyexamples.blogspot.com/2014/02/raspberry-pi-control-from-mobile-device.html

from flask import Flask, render_template, request, jsonify
import comms.comms as comms # encapsulates communication technology
from time import sleep
import ssl # for hand-crafted ssl context enabling TLS?
from flask_httpauth import HTTPBasicAuth

users = {
    "david":"secret",
    "susan":"secret"
}

app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None



# return index page when IP address of RPi is typed in the browser
@app.route("/")
@auth.login_required
def Index():
    zones={"Upper Windows":"disarmed","Lower Windows":"armed","Doors":"disarmed","Inside Motion":"unarmed"}
    return render_template("index.html", uptime=GetUptime(), zones=zones )

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
    sleep(1) # zmq slow joiner syndrome, should sync instead
    comm_channel.send("control_events", [command])
    comm_channel.close()

def GetStatus():
    # create object for communication to sensor system
    # state_comms = comms.SubChannel("tcp://state1:5564", ['sensor_events','control_events', 'state'])
    # state_comms.close()
    pass
    
# run the webserver on standard port 80, requires sudo
if __name__ == "__main__":
    
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #context.load_cert_chain( 'ssl.cert', 'ssl.key')
    context = ( 'hsec.crt', 'hsec.key')
    #app.run(host='0.0.0.0', ssl_context=context, threaded=True, debug=True)
    app.run(host='0.0.0.0', ssl_context=context, debug=True)
    #app.run(host='0.0.0.0',debug=True)
