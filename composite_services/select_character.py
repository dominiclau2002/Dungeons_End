from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")

@app.route('/select_character', methods=['POST'])
def select_character():
    """
    Selects a character and initializes the player.
    """
    data = request.get_json()
    player_id = data.get("player_id")
    character_name = data.get("character_name")

    if not player_id or not character_name:
        return jsonify({"error": "PlayerID and character name are required"}), 400

    # ✅ Fetch character stats from the player service
    char_response = requests.get(f"{PLAYER_SERVICE_URL}/character/{character_name}")
    if char_response.status_code != 200:
        return jsonify({"error": "Character not found"}), 404

    character = char_response.json()

    # ✅ Initialize the player with character stats
    init_response = requests.post(
        f"{PLAYER_SERVICE_URL}/initialize_player",
        json={"player_id": player_id, "character": character}
    )

    if init_response.status_code != 201:
        return jsonify({"error": "Failed to initialize player"}), 500

    return jsonify({"message": "Character selected successfully!", "character": character})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5017, debug=True)
