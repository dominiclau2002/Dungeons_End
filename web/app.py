from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# ✅ Microservice URLs
SELECT_CHARACTER_URL = os.getenv("SELECT_CHARACTER_URL", "http://select_character:5017/select_character")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://entering_room:5011/room")
COMBAT_SERVICE_URL = os.getenv("COMBAT_SERVICE_URL", "http://fight_enemy:5008/combat")

@app.route("/")
def home():
    """Renders the game UI."""
    return render_template("index.html")

@app.route("/select_character", methods=["POST"])
def select_character():
    """Handles character selection."""
    data = request.get_json()
    response = requests.post(SELECT_CHARACTER_URL, json=data)
    return jsonify(response.json())

@app.route("/enter_room", methods=["POST"])
def enter_room():
    """Handles room navigation."""
    data = request.get_json()
    response = requests.post(f"{ROOM_SERVICE_URL}/{data['room_id']}", json=data)
    return jsonify(response.json())

@app.route("/attack", methods=["POST"])
def attack():
    """Handles combat attacks."""
    data = request.get_json()
    response = requests.post(f"{COMBAT_SERVICE_URL}/attack/{data['room_id']}", json=data)
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
