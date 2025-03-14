from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Microservice URLs from environment variables
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
DICE_SERVICE_URL = os.getenv("DICE_SERVICE_URL", "http://dice_service:5007")
SCORE_SERVICE_URL = os.getenv("SCORE_SERVICE_URL", "http://score_service:5015")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")

@app.route('/combat/start/<int:room_id>', methods=['POST'])
def start_combat(room_id):
    """
    Starts combat when a player enters a room with an enemy.
    """
    player_id = request.json.get("player_id")
    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # ✅ Fetch enemy details
    enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{room_id}")
    if enemy_response.status_code != 200:
        return jsonify({"message": "No enemy found in this room.", "combat": False})

    enemy = enemy_response.json()

    # ✅ Log combat initiation
    log_data = {
        "player_id": player_id,
        "action": f"Engaged in combat with {enemy['Name']} in Room {room_id}"
    }
    requests.post(f"{ACTIVITY_LOG_SERVICE_URL}/log", json=log_data)

    return jsonify({
        "message": f"You encountered a {enemy['Name']}!",
        "enemy": {
            "name": enemy["Name"],
            "health": enemy["Health"],
            "attacks": enemy["Attacks"]
        },
        "combat": True
    })

@app.route('/combat/attack/<int:room_id>', methods=['POST'])
def player_attack(room_id):
    """
    The player attacks the enemy. Uses dice roll to determine damage.
    """
    player_id = request.json.get("player_id")
    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # ✅ Fetch enemy details
    enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{room_id}")
    if enemy_response.status_code != 200:
        return jsonify({"error": "No enemy found in this room"}), 404

    enemy = enemy_response.json()

    # ✅ Roll for player attack damage
    dice_response = requests.get(f"{DICE_SERVICE_URL}/roll?sides=6")
    damage = dice_response.json()["results"][0]

    # ✅ Attack enemy
    attack_response = requests.post(f"{ENEMY_SERVICE_URL}/enemy/{room_id}/damage", json={"damage": damage})

    # ✅ If enemy is defeated, add score
    enemy_after_attack = attack_response.json()
    if "loot" in enemy_after_attack:
        score_data = {
            "player_id": player_id,
            "points": 50,  # Example points for winning combat
            "reason": "combat"
        }
        requests.post(f"{SCORE_SERVICE_URL}/score/add", json=score_data)

    return jsonify({
        "message": f"You attacked {enemy['Name']} for {damage} damage!",
        "damage_dealt": damage,
        "combat_over": "loot" in enemy_after_attack
    })

@app.route('/combat/enemy-turn/<int:room_id>', methods=['POST'])
def enemy_attack(room_id):
    """
    The enemy attacks the player.
    """
    player_id = request.json.get("player_id")
    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # ✅ Fetch enemy details
    enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{room_id}")
    if enemy_response.status_code != 200:
        return jsonify({"error": "No enemy found in this room"}), 404

    enemy = enemy_response.json()

    # ✅ Enemy attacks (randomized)
    attack_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{room_id}/attack")
    attack_data = attack_response.json()
    damage = attack_data["damage"]

    # ✅ Update player health
    requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}", json={"health": f"-{damage}"})

    # ✅ Log enemy attack action
    log_data = {
        "player_id": player_id,
        "action": f"Was attacked by {enemy['Name']} for {damage} damage"
    }
    requests.post(f"{ACTIVITY_LOG_SERVICE_URL}/log", json=log_data)

    return jsonify({
        "message": f"{enemy['Name']} attacked you with {attack_data['attack']} for {damage} damage!"
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5008, debug=True)
