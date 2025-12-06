from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    raise Exception("💥 BROKEN DEPLOYMENT - Triggering self-healing!")
    return "Never reached"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
