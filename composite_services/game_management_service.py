from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Microservice URLs from environment variables
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")

@app.route('/game/reset/<int:player_id>', methods=['POST'])
def reset_game(player_id):
    """
    Resets the selected character's game progress.
    - Resets player health and room location
    - Resets all enemies
    - Clears the activity log
    """
    # ✅ Step 1: Reset Selected Character (Keeps Other Profiles Intact)
    reset_player_response = requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}", json={"health": 100, "room_id": 1})
    if reset_player_response.status_code != 200:
        return jsonify({"error": "Failed to reset player"}), 500

    # ✅ Step 2: Reset All Enemies (Global Reset)
    enemy_reset_status = []
    enemy_list_response = requests.get(f"{ENEMY_SERVICE_URL}/enemies")

    if enemy_list_response.status_code == 200:
        enemies = enemy_list_response.json()
        for enemy in enemies:
            reset_enemy_response = requests.put(f"{ENEMY_SERVICE_URL}/enemy/{enemy['RoomID']}/reset", json={"health": 30})
            if reset_enemy_response.status_code == 200:
                enemy_reset_status.append(f"Enemy in Room {enemy['RoomID']} reset")
            else:
                enemy_reset_status.append(f"Failed to reset enemy in Room {enemy['RoomID']}")

    # ✅ Step 3: Clear Activity Log (Global Reset)
    clear_log_response = requests.delete(f"{ACTIVITY_LOG_SERVICE_URL}/log/clear")
    if clear_log_response.status_code != 200:
        return jsonify({"error": "Failed to clear activity log"}), 500

    return jsonify({
        "message": f"Game has been reset for player {player_id}!",
        "player_status": reset_player_response.json(),
        "enemies_reset": enemy_reset_status,
        "logs_cleared": True
    })

@app.route('/game/select/<int:player_id>', methods=['GET'])
def select_character(player_id):
    """
    Loads the selected player's character profile.
    """
    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    
    if player_response.status_code != 200:
        return jsonify({"error": "Player not found!"}), 404

    return jsonify(player_response.json())

@app.route('/game/characters', methods=['GET'])
def list_characters():
    """
    Lists all available character profiles.
    """
    player_list_response = requests.get(f"{PLAYER_SERVICE_URL}/players")

    if player_list_response.status_code != 200:
        return jsonify({"error": "Could not retrieve players."}), 500

    return jsonify(player_list_response.json())

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5014, debug=True)
