from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Microservice URLs
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
DICE_SERVICE_URL = os.getenv("DICE_SERVICE_URL", "http://dice_service:5007")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")

@app.route('/combat/attack/<int:room_id>', methods=['POST'])
def player_attack(room_id):
    """
    The player attacks the enemy. Uses dice roll to determine damage.
    """
    player_id = request.json.get("player_id")
    action = request.json.get("action", "basic_attack")

    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # Fetch player details
    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    if player_response.status_code != 200:
        return jsonify({"error": "Player not found"}), 404

    player = player_response.json()

    # Fetch enemy details
    enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{room_id}")
    if enemy_response.status_code != 200:
        return jsonify({"error": "No enemy found in this room"}), 404

    enemy = enemy_response.json()

    # Roll dice for skill activation (if using skill)
    skill_activated = False
    if action != "basic_attack":
        dice_response = requests.get(f"{DICE_SERVICE_URL}/roll?sides=6")
        if dice_response.status_code == 200 and dice_response.json()["results"][0] >= 3:
            skill_activated = True

    # Determine damage
    if action == "basic_attack":
        dice_response = requests.get(f"{DICE_SERVICE_URL}/roll?sides=6")
        damage = dice_response.json()["results"][0]
    elif action == "skill" and skill_activated:
        class_damage = {
            "Warrior": max(5, (120 - player["Health"]) // 4),  # Berserker
            "Rogue": 12,  # Backstab
            "Cleric": -10,  # Healing (negative to represent healing)
            "Ranger": 8  # Poison damage over time
        }
        damage = class_damage.get(player["Name"], 5)
    else:
        return jsonify({"message": "Skill failed!", "combat_over": False})

    # Apply damage
    attack_response = requests.post(f"{ENEMY_SERVICE_URL}/enemy/{room_id}/damage", json={"damage": damage})
    if attack_response.status_code != 200:
        return jsonify({"error": "Failed to attack the enemy"}), 500

    # Log attack
    log_data = {
        "player_id": player_id,
        "action": f"Used {action} on {enemy['Name']} for {damage} damage"
    }
    requests.post(f"{ACTIVITY_LOG_SERVICE_URL}/log", json=log_data)

    # If enemy is defeated
    enemy_after_attack = attack_response.json()
    if "loot" in enemy_after_attack:
        return jsonify({
            "message": f"You defeated {enemy['Name']}!",
            "damage_dealt": damage,
            "loot": enemy_after_attack["loot"],
            "combat_over": True
        })

    return jsonify({
        "message": f"You attacked {enemy['Name']} for {damage} damage!",
        "damage_dealt": damage,
        "enemy_health": enemy_after_attack["message"],
        "combat_over": False
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5008, debug=True)
