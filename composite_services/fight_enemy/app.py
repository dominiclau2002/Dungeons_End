from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime
import logging
from composite_services.utilities.activity_logger import log_activity


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ Microservice URLs
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
DICE_SERVICE_URL = os.getenv("DICE_SERVICE_URL", "http://personal-eamy64us.outsystemscloud.com/DiceService/rest/DiceRollAPI/RESTAPIMethod1")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")
PLAYER_ROOM_INTERACTION_SERVICE_URL = os.getenv("PLAYER_ROOM_INTERACTION_SERVICE_URL", "http://player_room_interaction_service:5040")

# def log_activity(player_id, action):
#     """
#     Logs player activity by making a REST API call to the activity_log_service.
#     """
#     if not player_id or not action:
#         logger.error("Missing required parameters for logging: player_id and action must be provided")
#         return False
        
#     url = f"{ACTIVITY_LOG_SERVICE_URL}/api/log"
#     data = {
#         "player_id": player_id,
#         "action": action,
#         "timestamp": datetime.utcnow().isoformat()
#     }
    
#     try:
#         response = requests.post(url, json=data, timeout=5)
        
#         if response.status_code == 201:
#             logger.debug(f"Activity logged successfully: Player {player_id} - {action}")
#             return True
#         else:
#             logger.error(f"Failed to log activity: {response.status_code} - {response.text}")
#             return False
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Error connecting to activity log service: {str(e)}")
#         return False
#     except Exception as e:
#         logger.error(f"Unexpected error logging activity: {str(e)}")
#         return False

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
    
    # Extract player health data
    player_max_health = player.get("max_health", player.get("MaxHealth", 100))
    player_current_health = player.get("current_health", player.get("CurrentHealth", player.get("health", player.get("Health", 100))))

    # ✅ Log combat start via RabbitMQ (using case-insensitive access)
    log_activity(player_id, f"Engaged in combat with {enemy_data.get('name', 'Unknown Enemy')}")

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
            "health": player_current_health,
            "current_health": player_current_health,
            "max_health": player_max_health,
            "damage": player.get("Damage", player.get("damage", 10))
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
        player_id = data.get("player_id")
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
            
        if not player_id:
            logger.error("Missing player_id parameter")
            return jsonify({"error": "player_id is required"}), 400
        
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
            # dice_response = requests.get(f"{DICE_SERVICE_URL}/roll?sides=6&count=1")
            dice_response = requests.get(f"{DICE_SERVICE_URL}")
            

            if dice_response.status_code != 200:
                logger.error(f"Dice service error: {dice_response.text}")
                return jsonify({"error": "Failed to roll dice"}), 500
                
            dice_data = dice_response.json()
            # dice_roll = dice_data["results"][0]
            dice_roll = dice_data
            
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

                    # ✅ Update player's score for defeating the enemy
                    try:
                        update_score_url = f"{PLAYER_SERVICE_URL}/player/{player_id}/score"
                        score_payload = {"points": 20}
                        score_response = requests.patch(update_score_url, json=score_payload)

                        if score_response.status_code != 200:
                            logger.warning(f"Score update failed after enemy defeat: {score_response.status_code} - {score_response.text}")
                            combat_log.append("Victory registered, but score update failed.")
                        else:
                            logger.info(f"Score updated for player {player_id} after defeating {enemy_name}")
                            log_activity(player_id, f"Defeated {enemy_name} (+20 score)")
                            combat_log.append("You gained 20 points for defeating the enemy!")
                    except Exception as e:
                        logger.error(f"Error while updating score after enemy defeat: {str(e)}")
                        combat_log.append("Could not update score due to server error.")

                    
                    # Also update player's current health to preserve it
                    try:
                        update_response = requests.put(
                            f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                            json={"current_health": player_health}
                        )
                        
                        if update_response.status_code != 200:
                            logger.warning(f"Failed to update player health after victory: {update_response.text}")
                    except Exception as e:
                        logger.error(f"Error updating player health after victory: {str(e)}")
                    
                    # Record enemy defeat in player_room_interaction service if room_id is provided
                    if room_id:
                        try:
                            logger.info(f"Player {player_id} defeated enemy {enemy_id} in room {room_id}")
                            
                            # Record the defeat in player_room_interaction service
                            interaction_url = f"{PLAYER_ROOM_INTERACTION_SERVICE_URL}/player/{player_id}/room/{room_id}/enemy/{enemy_id}/defeat"
                            interaction_response = requests.post(interaction_url)
                            
                            if interaction_response.status_code in (200, 201):
                                logger.info(f"Successfully recorded enemy {enemy_id} defeat for player {player_id} in room {room_id}")
                                combat_log.append("Your victory was recorded.")
                            else:
                                logger.error(f"Failed to record enemy defeat: {interaction_response.status_code} - {interaction_response.text}")
                                combat_log.append("The enemy appears to be defeated, but something went wrong.")
                        except Exception as e:
                            logger.error(f"Error recording enemy defeat: {str(e)}")
                            logger.exception("Stack trace:")
                    
                    # Log victory and update player stats
                    log_activity(player_id, f"Defeated {enemy_name}")
                    
                    # Fetch enemy details for points
                    try:
                        enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{enemy_id}")
                        if enemy_response.status_code == 200:
                            enemy = enemy_response.json()
                            # Try different case formats for points
                            points = enemy.get("Points", enemy.get("points", 50))
                            
                            # Remove score-related code
                            combat_log.append("You were victorious!")
                    except Exception as e:
                        logger.error(f"Error processing victory rewards: {str(e)}")
                        combat_log.append("You were victorious!")
                else:
                    # Switch turn to enemy
                    current_turn = "enemy"
            
            if current_turn == "enemy" and not is_combat_over:
                # Enemy attacks player
                try:
                    # enemy_dice_response = requests.get(f"{DICE_SERVICE_URL}/roll?sides=6&count=1")
                    enemy_dice_response = requests.get(f"{DICE_SERVICE_URL}")

                    enemy_dice_data = enemy_dice_response.json()
                    # enemy_dice_roll = enemy_dice_data["results"][0]
                    enemy_dice_roll = enemy_dice_data
                    
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
                                
                                # Handle different case formats for max health
                                max_health = None
                                for key in ["max_health", "MaxHealth"]:
                                    if key in player_data:
                                        max_health = player_data[key]
                                        break
                                
                                # Fall back to Health/health if no max_health is found
                                if max_health is None:
                                    for key in ["Health", "health"]:
                                        if key in player_data:
                                            max_health = player_data[key]
                                            break
                                
                                if max_health is None:
                                    max_health = 100  # Default if not found
                                    
                                # Calculate remaining health and ensure it's at least 1
                                remaining_health = max(1, int(max_health * 0.25))
                                
                                # Update the player's current health
                                update_response = requests.put(
                                    f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                                    json={"current_health": remaining_health}
                                )
                                
                                if update_response.status_code == 200:
                                    logger.info(f"Updated player {player_id} current health to {remaining_health}")
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
                        log_activity(player_id, f"Defeated {enemy_name}")
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
