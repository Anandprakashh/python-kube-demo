from flask import Flask
import logging
import socket

app = Flask(__name__)
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

@app.route("/")
def hello():
    log.error("💥 CRITICAL: Flask broken deployment - self-healing test!")
    log.error(f"ERROR on pod: {socket.gethostname()}")
    return "INTERNAL SERVER ERROR", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
