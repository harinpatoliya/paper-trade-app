import eventlet
eventlet.monkey_patch()

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from main import app, socketio

if __name__ == '__main__':
    socketio.run(app, debug=True)
