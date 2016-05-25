#!/usr/bin/env python3.4

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# http://electronicsbyexamples.blogspot.com/2014/02/raspberry-pi-control-from-mobile-device.html

from flask import Flask, render_template, request, jsonify
import comms.comms as comms # encapsulates communication technology
from time import sleep

app = Flask(__name__)

# return index page when IP address of RPi is typed in the browser
@app.route("/")
def Index():
    return render_template("index.html", uptime=GetUptime())

# ajax GET call this function to set led state
# depeding on the GET parameter sent
@app.route("/_led")
def _led():
    state = request.args.get('state')
    if state=="armed":
        print("SendCommand(all zones, arm)")
        SendCommand("all zones", "arm")
        pass
    else:
        print("SendCommand(all zones, disarm)")
        SendCommand("all zones", "disarm")
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

def SendCommand(zone,armed):
    comm_channel = comms.PubChannel("tcp://*:5563")
    sleep(1) # zmq slow joiner syndrome, should sync instead
    channel = "control_events"
    if armed=="arm":
        comm_channel.send(channel, [[zone,"arm"]])
    else:
        comm_channel.send(channel, [[zone,"disarm"]])
    comm_channel.close()
    
# run the webserver on standard port 80, requires sudo
if __name__ == "__main__":
    
    app.run(host='0.0.0.0',debug=True)
