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
SCORE_SERVICE_URL = os.getenv("SCORE_SERVICE_URL", "http://score_service:5008")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
ACTIVITY_LOG_QUEUE = "activity_log_queue"

def send_activity_log(player_id, action):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=ACTIVITY_LOG_QUEUE, durable=True)
    message = {
        "player_id": player_id,
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

    # ✅ Handle different case formats in API responses
    # Create a case-insensitive access mechanism
    enemy_data = {k.lower(): v for k, v in enemy.items()}
    
    # ✅ Fetch player details
    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    if player_response.status_code != 200:
        return jsonify({"error": "Player not found"}), 404
    
    player = player_response.json()

    # ✅ Log combat start via RabbitMQ (using case-insensitive access)
    send_activity_log(player_id, f"Engaged in combat with {enemy_data.get('name', 'Unknown Enemy')}")

    return jsonify({
        "message": f"You encountered a {enemy_data.get('name', 'Unknown Enemy')}!",
        "enemy": {
            "id": enemy_id,
            "name": enemy_data.get('name', 'Unknown Enemy'),
            "description": enemy_data.get('description', 'No description available'),
            "health": enemy_data.get('health', 100),
            "damage": enemy_data.get('damage', 10),
            "attack": enemy_data.get('attack', 1),
            "max_health": enemy_data.get('health', 100)
        },
        "player": {
            "health": player.get("Health", player.get("health", 100)),
            "damage": player.get("Damage", player.get("damage", 10)),
            "max_health": player.get("Health", player.get("health", 100))
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
        
        # Get parameters with defaults
        player_id = data.get("player_id", 1)
        enemy_id = data.get("enemy_id")
        player_health = int(data.get("player_health", 100))
        enemy_health = int(data.get("enemy_health", 100))
        player_damage = int(data.get("player_damage", 10))
        enemy_damage = int(data.get("enemy_damage", 10))
        enemy_attack = int(data.get("enemy_attack", 1))
        current_turn = data.get("turn", "player")
        enemy_name = data.get("enemy_name", "enemy")
        room_id = data.get("room_id")  # Room ID parameter
        
        # Validate critical parameters
        if not enemy_id:
            logger.error("Missing enemy_id parameter")
            return jsonify({"error": "enemy_id is required"}), 400
        
        # Validate room_id is provided
        if not room_id:
            logger.warning("Missing room_id parameter - enemy won't be removed from room on defeat")
            
        # Convert any string values to integers
        try:
            enemy_id = int(enemy_id)
            player_id = int(player_id)
            if room_id:  # Only convert if it exists
                room_id = int(room_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid ID values: enemy_id={enemy_id}, player_id={player_id}, room_id={room_id}")
            return jsonify({"error": "Invalid ID values"}), 400
        
        combat_log = []
        is_combat_over = False
        winner = None
        
        # Rest of your combat logic here
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
                total_damage = max(1, player_damage * dice_roll // 6)  # Adjust multiplier as needed
                enemy_health -= total_damage
                combat_log.append(f"You rolled a {dice_roll} and dealt {total_damage} damage to the {enemy_name}!")
                
                # Check if enemy defeated
                if enemy_health <= 0:
                    enemy_health = 0
                    is_combat_over = True
                    winner = "player"
                    combat_log.append(f"You defeated the {enemy_name}!")
                    
                    # Also update player's current health to preserve it
                    try:
                        update_response = requests.put(
                            f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                            json={"health": player_health}
                        )
                        
                        if update_response.status_code != 200:
                            logger.warning(f"Failed to update player health after victory: {update_response.text}")
                    except Exception as e:
                        logger.error(f"Error updating player health after victory: {str(e)}")
                    
                    # Remove enemy from room if room_id is provided
                    if room_id:
                        try:
                            logger.info(f"Player defeated enemy {enemy_id} in room {room_id}")
                            
                            # First check the current room data to see what we're working with
                            check_url = f"{ROOM_SERVICE_URL}/room/{room_id}"
                            check_response = requests.get(check_url)
                            
                            if check_response.status_code == 200:
                                room_data = check_response.json()
                                logger.info(f"Current room data before removal: {room_data}")
                                
                                # Check all possible formats for enemy IDs
                                enemy_ids = []
                                if "EnemyIDs" in room_data and isinstance(room_data["EnemyIDs"], list):
                                    enemy_ids = room_data["EnemyIDs"]
                                    logger.info(f"Found EnemyIDs: {enemy_ids}")
                                elif "enemy_ids" in room_data and isinstance(room_data["enemy_ids"], list):
                                    enemy_ids = room_data["enemy_ids"]
                                    logger.info(f"Found enemy_ids: {enemy_ids}")
                                
                                # Check if the enemy is in the room before attempting removal
                                if enemy_id in enemy_ids:
                                    # Direct call to remove enemy from room
                                    remove_url = f"{ROOM_SERVICE_URL}/room/{room_id}/enemy/{enemy_id}"
                                    logger.info(f"Removing enemy from room: DELETE {remove_url}")
                                    
                                    remove_response = requests.delete(remove_url, timeout=10)
                                    
                                    if remove_response.status_code == 200:
                                        logger.info(f"Successfully removed enemy {enemy_id} from room {room_id}")
                                        combat_log.append("The enemy has been defeated and removed from the room.")
                                        
                                        # Double-check the room state after removal
                                        verify_response = requests.get(check_url)
                                        if verify_response.status_code == 200:
                                            updated_room = verify_response.json()
                                            logger.info(f"Room data after removal: {updated_room}")
                                            
                                            # Verify enemy was actually removed from all possible fields
                                            still_present = False
                                            if "EnemyIDs" in updated_room and isinstance(updated_room["EnemyIDs"], list):
                                                if enemy_id in updated_room["EnemyIDs"]:
                                                    still_present = True
                                            if "enemy_ids" in updated_room and isinstance(updated_room["enemy_ids"], list):
                                                if enemy_id in updated_room["enemy_ids"]:
                                                    still_present = True
                                                    
                                            if still_present:
                                                logger.error(f"Enemy {enemy_id} still present in room data after DELETE operation")
                                                # Try forcing an update with PUT
                                                logger.info("Attempting forced removal with PUT operation")
                                                
                                                # Create new enemy list without the defeated enemy
                                                if "EnemyIDs" in updated_room and isinstance(updated_room["EnemyIDs"], list):
                                                    updated_room["EnemyIDs"] = [e for e in updated_room["EnemyIDs"] if e != enemy_id]
                                                if "enemy_ids" in updated_room and isinstance(updated_room["enemy_ids"], list):
                                                    updated_room["enemy_ids"] = [e for e in updated_room["enemy_ids"] if e != enemy_id]
                                                
                                                # Update the room with PUT
                                                update_url = f"{ROOM_SERVICE_URL}/room/{room_id}"
                                                update_response = requests.put(update_url, json=updated_room)
                                                
                                                if update_response.status_code == 200:
                                                    logger.info(f"Successfully forced enemy removal via PUT")
                                                else:
                                                    logger.error(f"Failed to force remove enemy: {update_response.status_code}")
                                            else:
                                                logger.info(f"Verification confirmed enemy {enemy_id} removed from room {room_id}")
                                    else:
                                        logger.error(f"Failed to remove enemy from room: {remove_response.status_code} - {remove_response.text}")
                                        combat_log.append("The enemy appears to be defeated, but something went wrong.")
                                else:
                                    logger.info(f"Enemy {enemy_id} not found in room {room_id} - already removed")
                            else:
                                logger.error(f"Failed to get room data: {check_response.status_code}")
                        except Exception as e:
                            logger.error(f"Error removing enemy from room: {str(e)}")
                            logger.exception("Stack trace:")
                    
                    # Log victory and update player stats
                    send_activity_log(player_id, f"Defeated {enemy_name}")
                    
                    # Fetch enemy details for points
                    try:
                        enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{enemy_id}")
                        if enemy_response.status_code == 200:
                            enemy = enemy_response.json()
                            # Try different case formats for points
                            points = enemy.get("Points", enemy.get("points", 50))
                            
                            # Add score points for defeating enemy
                            score_data = {
                                "player_id": player_id,
                                "points": points,
                                "reason": "combat"
                            }
                            requests.post(f"{SCORE_SERVICE_URL}/score", json=score_data)
                            combat_log.append(f"You earned {points} points!")
                    except Exception as e:
                        logger.error(f"Error processing victory rewards: {str(e)}")
                        combat_log.append("You earned some points!")
                else:
                    # Switch turn to enemy
                    current_turn = "enemy"
            
            if current_turn == "enemy" and not is_combat_over:
                # Enemy attacks player
                try:
                    enemy_dice_response = requests.get(f"{DICE_SERVICE_URL}/roll?sides=6&count=1")
                    enemy_dice_data = enemy_dice_response.json()
                    enemy_dice_roll = enemy_dice_data["results"][0]
                    
                    total_enemy_damage = max(1, enemy_damage * enemy_attack * enemy_dice_roll // 6)
                    player_health -= total_enemy_damage
                    combat_log.append(f"The {enemy_name} rolled a {enemy_dice_roll} and dealt {total_enemy_damage} damage to you!")
                    
                    # Check if player defeated
                    if player_health <= 0:
                        player_health = 0
                        is_combat_over = True
                        winner = "enemy"
                        combat_log.append("You were defeated!")
                        
                        # Update player health in database to 25% of max health if defeated
                        try:
                            # Get current player data first
                            player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
                            if player_response.status_code == 200:
                                player_data = player_response.json()
                                
                                # Handle different case formats
                                max_health = None
                                for key in ["Health", "health", "MAX_HEALTH", "max_health"]:
                                    if key in player_data:
                                        max_health = player_data[key]
                                        break
                                
                                if max_health is None:
                                    max_health = 100  # Default if not found
                                    
                                # Calculate remaining health and ensure it's at least 1
                                remaining_health = max(1, int(max_health * 0.25))
                                
                                # Update the player's health
                                update_response = requests.put(
                                    f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                                    json={"health": remaining_health}
                                )
                                
                                if update_response.status_code == 200:
                                    logger.info(f"Updated player {player_id} health to {remaining_health}")
                                    player_health = remaining_health
                                    combat_log.append(f"You survived with {remaining_health} health remaining.")
                                else:
                                    logger.error(f"Failed to update player health: {update_response.text}")
                                    combat_log.append("You survived with some health remaining.")
                            else:
                                logger.error(f"Failed to get player data: {player_response.text}")
                                combat_log.append("You survived with some health remaining.")
                        except Exception as e:
                            logger.error(f"Error updating player health after defeat: {str(e)}")
                            player_health = 25  # Default if player update fails
                            combat_log.append("You survived with some health remaining.")
                        
                        # Log defeat
                        send_activity_log(player_id, f"Defeated by {enemy_name}")
                    else:
                        # Switch turn back to player
                        current_turn = "player"
                except Exception as e:
                    logger.error(f"Error during enemy attack: {str(e)}")
                    combat_log.append("The enemy tried to attack but missed.")
                    current_turn = "player"  # Ensure turn passes to player
        
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
