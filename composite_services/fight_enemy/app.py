from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ Microservice URLs
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
DICE_SERVICE_URL = os.getenv("DICE_SERVICE_URL", "http://dice_service:5007")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
ACTIVITY_LOG_QUEUE = "activity_log_queue"

def send_activity_log(action):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=ACTIVITY_LOG_QUEUE, durable=True)
    message = {
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    }
    channel.basic_publish(
        exchange='',
        routing_key=ACTIVITY_LOG_QUEUE,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

@app.route('/combat/start/<int:enemy_id>', methods=['POST'])
def start_combat(enemy_id):
    player_id = request.json.get("player_id")
    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # ✅ Fetch enemy details
    enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{enemy_id}")
    if enemy_response.status_code != 200:
        return jsonify({"message": "No enemy found.", "combat": False}), 404

    enemy = enemy_response.json()
    
    # ✅ Fetch player details
    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    if player_response.status_code != 200:
        return jsonify({"error": "Player not found"}), 404
    
    player = player_response.json()

    # ✅ Log combat start
    send_activity_log("enemy_defeat")

    return jsonify({
        "message": f"You encountered a {enemy['name']}!",
        "enemy": {
            "id": enemy_id,
            "name": enemy['name'],
            "description": enemy['description'],
            "health": enemy['health'],
            "damage": enemy['damage'],
            "attack": enemy['attack'],
            "max_health": enemy['health']
        },
        "player": {
            "health": player["health"],
            "damage": player["damage"],
            "max_health": player["health"]
        },
        "combat": True,
        "turn": "player"  # Player always goes first
    })

@app.route('/combat/attack', methods=['POST'])
def attack():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": "No data received"}), 400
            
        logger.debug(f"Attack request data: {data}")
        
        # Get parameters
        player_id = data.get("player_id")
        enemy_id = data.get("enemy_id")
        player_health = int(data.get("player_health"))
        enemy_health = int(data.get("enemy_health"))
        player_damage = int(data.get("player_damage"))
        enemy_damage = int(data.get("enemy_damage"))
        enemy_attack = int(data.get("enemy_attack"))
        current_turn = data.get("turn")
        enemy_name = data.get("enemy_name")
        room_id = data.get("room_id")
        
        # Validate critical parameters
        if not enemy_id or not player_id or not room_id:
            logger.error("Missing required parameters")
            return jsonify({"error": "enemy_id, player_id and room_id are required"}), 400
        
        # Convert any string values to integers
        enemy_id = int(enemy_id)
        player_id = int(player_id)
        room_id = int(room_id)
        
        combat_log = []
        is_combat_over = False
        winner = None
        
        try:
            # Roll dice for damage calculation
            dice_response = requests.get(f"{DICE_SERVICE_URL}/roll?sides=6&count=1")
            if dice_response.status_code != 200:
                logger.error(f"Dice service error: {dice_response.text}")
                return jsonify({"error": "Failed to roll dice"}), 500
                
            dice_data = dice_response.json()
            dice_roll = dice_data["results"][0]
            
            if current_turn == "player":
                # Player attacks enemy
                total_damage = player_damage * dice_roll // 6
                enemy_health -= total_damage
                combat_log.append(f"You rolled a {dice_roll} and dealt {total_damage} damage to the {enemy_name}!")
                
                # Check if enemy defeated
                if enemy_health <= 0:
                    enemy_health = 0
                    is_combat_over = True
                    winner = "player"
                    combat_log.append(f"You defeated the {enemy_name}!")
                    
                    # Update player's current health
                    update_response = requests.put(
                        f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                        json={"health": player_health}
                    )
                    
                    # Remove enemy from room
                    remove_url = f"{ROOM_SERVICE_URL}/room/{room_id}/enemy/{enemy_id}"
                    remove_response = requests.delete(remove_url, timeout=10)
                    
                    if remove_response.status_code == 200:
                        logger.info(f"Successfully removed enemy {enemy_id} from room {room_id}")
                        combat_log.append("The enemy has been defeated and removed from the room.")
                    
                    # Log victory
                    send_activity_log("enemy_defeat")
                    
                    # Add score points for defeating enemy
                    score_data = {
                        "points": 200,
                        "reason": "enemy_defeat"
                    }
                    requests.post(f"{SCORE_SERVICE_URL}/score", json=score_data)
                    combat_log.append("You earned 200 points!")
                else:
                    # Switch turn to enemy
                    current_turn = "enemy"
            
            if current_turn == "enemy" and not is_combat_over:
                # Enemy attacks player
                enemy_dice_response = requests.get(f"{DICE_SERVICE_URL}/roll?sides=6&count=1")
                enemy_dice_data = enemy_dice_response.json()
                enemy_dice_roll = enemy_dice_data["results"][0]
                
                total_enemy_damage = enemy_damage * enemy_attack * enemy_dice_roll // 6
                player_health -= total_enemy_damage
                combat_log.append(f"The {enemy_name} rolled a {enemy_dice_roll} and dealt {total_enemy_damage} damage to you!")
                
                # Check if player defeated
                if player_health <= 0:
                    player_health = 0
                    is_combat_over = True
                    winner = "enemy"
                    combat_log.append("You were defeated!")
                    
                    # Update player health in database
                    # Get current player data
                    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
                    player_data = player_response.json()
                    
                    # Calculate remaining health
                    max_health = player_data["health"]
                    remaining_health = int(max_health * 0.25)
                    
                    # Update the player's health
                    update_response = requests.put(
                        f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                        json={"health": remaining_health}
                    )
                    
                    player_health = remaining_health
                    combat_log.append(f"You survived with {remaining_health} health remaining.")
                    
                    # Log defeat
                    send_activity_log("enemy_defeat")
                else:
                    # Switch turn back to player
                    current_turn = "player"
        
        except Exception as e:
            logger.error(f"Error in combat processing: {str(e)}")
            return jsonify({"error": f"Combat error: {str(e)}"}), 500
        
        return jsonify({
            "combat_log": combat_log,
            "player_health": player_health,
            "enemy_health": enemy_health,
            "turn": current_turn,
            "is_combat_over": is_combat_over,
            "winner": winner,
            "enemy_id": enemy_id,
            "room_id": room_id
        })
    
    except Exception as e:
        logger.error(f"Unhandled exception in attack endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5009, debug=True)
