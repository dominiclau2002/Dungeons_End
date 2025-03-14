from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")
COMBAT_SERVICE_URL = os.getenv("COMBAT_SERVICE_URL", "http://fight_enemy:5008")

@app.route('/room/<int:room_id>', methods=['POST'])
def enter_room(room_id):
    """
    Player enters a room and either:
    - Reads the description
    - Fights an enemy
    - Makes a decision
    """
    data = request.get_json()
    player_id = data.get("player_id")
    decision = data.get("decision")  # Only used if the room has a choice

    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # ✅ Fetch room details
    room_response = requests.get(f"http://room_service:5012/room/{room_id}")
    if room_response.status_code != 200:
        return jsonify({"error": "Room not found"}), 404

    room = room_response.json()

    # ✅ Handle Room Choice (if applicable)
    if "choices" in room:
        if not decision or decision not in room["choices"]:
            return jsonify({"error": "Invalid choice"}), 400
        next_room_id = room["choices"][decision]
    else:
        next_room_id = room_id

    # ✅ Update player's location
    requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}", json={"room_id": next_room_id})

    # ✅ Check for enemy and start combat
    enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{next_room_id}")
    if enemy_response.status_code == 200:
        requests.post(f"{COMBAT_SERVICE_URL}/combat/start/{next_room_id}", json={"player_id": player_id})
        return jsonify({"message": "Combat initiated!"})

    return jsonify({
        "room_name": room["Name"],
        "description": room["Description"],
        "player_current_room": next_room_id
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5011, debug=True)
