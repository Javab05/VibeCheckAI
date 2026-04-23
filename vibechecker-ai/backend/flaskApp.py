import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from flask import Flask
from routes.auth import auth_routes
from routes.checkin import checkin_routes
from routes.history import history_routes

app = Flask(__name__)

# Register routes
app.register_blueprint(auth_routes, url_prefix="/auth")
app.register_blueprint(checkin_routes, url_prefix="/checkin")
app.register_blueprint(history_routes, url_prefix="/history")

@app.route("/")
def home():
    return {
        "status": "ok",
        "service": "VibeCheckAI backend",
        "message": "API is running"
    }
@app.route("/ping")
def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True)