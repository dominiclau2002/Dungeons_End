from flask import Flask
from api.routes import init_routes #Import the route registration function

# Initialize Flask app
app = Flask(__name__)

init_routes(app) #Register routes directly

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Accessible on local network

