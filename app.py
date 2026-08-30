from flask import Flask
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

@sock.route("/stream")
def stream(ws):

    while True:
        message = ws.receive()

        if message is None:
            break

        print(message)