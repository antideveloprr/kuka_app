from kuka_web import app
from kuka_web.events import socketio

if __name__ == '__main__':
    socketio.run(app, debug=True)
