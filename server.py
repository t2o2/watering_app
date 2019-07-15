from flask import render_template
from flask import Flask
from threading import Timer
import RPi.GPIO as GPIO
from functools import wraps
from flask import request, Response, session
import datetime
import redis

red = redis.StrictRedis(host='localhost', port=6379, db=0)
app = Flask(__name__)

GPIO.setwarnings(False)
channel=16
GPIO.setmode(GPIO.BOARD)
GPIO.setup(channel, GPIO.OUT, initial=GPIO.HIGH)
is_watering = False


def start_water(s=60):
    if s > 600:
        s = 600
    print("watering for {} seconds".format(s))
    GPIO.output(channel, GPIO.LOW)
    t = Timer(s, stop)
    t.start()
    red.publish('watering_status', 'Watering')

def stop_water():
    print("stopped")
    GPIO.output(channel, GPIO.HIGH)
    red.publish('watering_status', 'Stopped')

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 't2o2' and password == 'omdurman'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe('watering_status')
    next(pubsub.listen())
    for message in pubsub.listen():
        print(message)
        yield 'data: %s\n\n' % message['data'].decode('utf-8')

@app.route("/")
@requires_auth
def home():
    status = 'Watering' if is_watering else 'Stopped'
    return render_template('home.html', status=status)

@app.route("/start/<int:t>", methods=['GET'])
@requires_auth
def start_with_limit(t):
    start_water(t)
    return "watering for {} seconds".format(t)

@app.route("/start/")
@requires_auth
def start():
    start_water()
    return "watering"

@app.route("/stop/")
def stop():
    stop_water()
    return "stopped"

@app.route('/stream')
def stream():
    return Response(event_stream(),
                    mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True)
