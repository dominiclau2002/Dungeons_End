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
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory_service:5001")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
PLAYER_ROOM_INTERACTION_SERVICE_URL = os.getenv("PLAYER_ROOM_INTERACTION_SERVICE_URL", "http://player_room_interaction_service:5040")
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
ACTIVITY_LOG_QUEUE = "activity_log_queue"


def send_activity_log(player_id, action):
    try:
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
        logger.debug(f"Activity log sent: {action}")
    except Exception as e:
        logger.error(f"Failed to send activity log: {str(e)}")

@app.route('/game/reset/<int:player_id>', methods=['POST'])
def reset_character_progress(player_id):
    """
    Resets the player's game progress by updating their room and health.
    """
    logger.debug(f"Resetting progress for player {player_id}")
    
    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    if player_response.status_code != 200:
        return jsonify({"error": "Player not found"}), 404

    # Get player data to determine max health
    player_data = player_response.json()
    max_health = player_data.get("max_health", player_data.get("MaxHealth", 100))
    
    # ✅ Reset player progress - restore full health and set room to 0
    requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                 json={"current_health": max_health, "room_id": 0, "sum_score":0})

    # ✅ Reset all enemies
    requests.get(f"{ENEMY_SERVICE_URL}/reset")

    # ✅ Log reset via RabbitMQ
    send_activity_log(player_id, "Game progress reset")

    return jsonify({"message": f"Progress reset for player {player_id}."})

@app.route('/game/full-reset/<int:player_id>', methods=['POST'])
def full_game_reset(player_id):
    """
    Performs a complete game reset across all services for the specified player.
    This resets the player state, inventory, and restores rooms to their original state.
    """
    logger.info(f"Performing full game reset for player {player_id}")
    reset_results = {
        "player": False,
        "inventory": False,
        "rooms": False,
        "errors": []
    }
    
    try:
        # Step 1: Verify player exists
        player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
        if player_response.status_code != 200:
            return jsonify({"error": "Player not found"}), 404
            
        player_data = player_response.json()
        player_name = player_data.get("name", f"Player {player_id}")
        logger.debug(f"Found player: {player_name}")
        
        # Get max health value
        max_health = player_data.get("max_health", player_data.get("MaxHealth", 100))
        
        # Step 2: Reset player stats and location
        try:
            player_reset = requests.put(
                f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                json={"current_health": max_health, "max_health": max_health, "damage": 10, "room_id": 0,"sum_score": 0},
                timeout=5
            )
            if player_reset.status_code == 200:
                reset_results["player"] = True
                logger.debug("Successfully reset player stats")
            else:
                logger.error(f"Failed to reset player: {player_reset.status_code}")
                reset_results["errors"].append(f"Player reset failed: {player_reset.text}")
        except Exception as e:
            logger.error(f"Error resetting player: {str(e)}")
            reset_results["errors"].append(f"Player reset error: {str(e)}")
        
        # Step 3: Clear player's inventory
        try:
            inventory_reset = requests.delete(
                f"{INVENTORY_SERVICE_URL}/inventory/player/{player_id}",
                timeout=5
            )
            if inventory_reset.status_code in [200, 404]:  # 404 is acceptable if no inventory
                reset_results["inventory"] = True
                logger.debug("Successfully cleared player inventory")
            else:
                logger.error(f"Failed to clear inventory: {inventory_reset.status_code}")
                reset_results["errors"].append(f"Inventory reset failed: {inventory_reset.text}")
        except Exception as e:
            logger.error(f"Error clearing inventory: {str(e)}")
            reset_results["errors"].append(f"Inventory reset error: {str(e)}")
            
        # Step 3.5: Reset player room interaction history
        try:
            logger.debug(f"Clearing player interaction history for player {player_id}")
            player_interaction_reset = requests.post(
                f"{PLAYER_ROOM_INTERACTION_SERVICE_URL}/player/{player_id}/reset",
                timeout=5
            )
            
            if player_interaction_reset.status_code == 200:
                logger.debug("Successfully cleared player interaction history")
            else:
                logger.error(f"Failed to clear player interaction history: {player_interaction_reset.status_code}")
                reset_results["errors"].append(f"Player interaction reset failed: {player_interaction_reset.text}")
        except Exception as e:
            logger.error(f"Error clearing player interaction history: {str(e)}")
            reset_results["errors"].append(f"Player interaction reset error: {str(e)}")
        
        # Step 4: Reset rooms - restore default items and enemies
        # This is a simplified approach - a more robust solution would
        # load default room data from a configuration or database
        try:
            # For simplicity, we'll update just the first few rooms with default settings
            room_defaults = [
                {"room_id": 1, "item_ids": [1, 2], "enemy_ids": [], "door_locked": False},
                {"room_id": 2, "item_ids": [3,5], "enemy_ids": [1], "door_locked": False},
                {"room_id": 3, "item_ids": [4], "enemy_ids": [2], "door_locked": True}
            ]
            
            room_update_success = True
            for room_data in room_defaults:
                room_id = room_data.pop("room_id")  # Extract room_id from the data
                try:
                    room_reset = requests.put(
                        f"{ROOM_SERVICE_URL}/room/{room_id}",
                        json=room_data,
                        timeout=5
                    )
                    if room_reset.status_code != 200:
                        room_update_success = False
                        logger.error(f"Failed to reset room {room_id}: {room_reset.status_code}")
                        reset_results["errors"].append(f"Room {room_id} reset failed: {room_reset.text}")
                except Exception as e:
                    room_update_success = False
                    logger.error(f"Error resetting room {room_id}: {str(e)}")
                    reset_results["errors"].append(f"Room {room_id} reset error: {str(e)}")
            
            reset_results["rooms"] = room_update_success
            if room_update_success:
                logger.debug("Successfully reset game rooms")
        except Exception as e:
            logger.error(f"Error in room reset process: {str(e)}")
            reset_results["errors"].append(f"Room reset process error: {str(e)}")
        
        # Log the full reset via RabbitMQ
        send_activity_log(player_id, f"Full game reset performed for {player_name}")
        
        # Determine overall success
        overall_success = all([
            reset_results["player"],
            reset_results["inventory"],
            reset_results["rooms"],
        ])
        
        if overall_success:
            logger.info(f"Full game reset successful for player {player_id}")
            return jsonify({
                "message": f"Game fully reset for {player_name}",
                "player_id": player_id,
                "reset_details": reset_results
            })
        else:
            logger.warning(f"Partial game reset for player {player_id} - some services failed")
            return jsonify({
                "message": f"Game partially reset for {player_name} - some errors occurred",
                "player_id": player_id,
                "reset_details": reset_results
            }), 207  # 207 Multi-Status
            
    except Exception as e:
        logger.error(f"Unhandled exception during game reset: {str(e)}")
        return jsonify({
            "error": f"Failed to reset game: {str(e)}",
            "reset_details": reset_results
        }), 500

@app.route('/game/end/<int:player_id>', methods=['POST'])
def end_game(player_id):
    """
    Handle end-of-game logic including awarding completion bonus,
    updating player score, and generating appropriate response.
    """
    logger.info(f"Processing end of game for player {player_id}")
    
    try:
        # Get current player data
        player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
        if player_response.status_code != 200:
            return jsonify({"error": "Player not found"}), 404
            
        player_data = player_response.json()
        current_score = player_data.get("sum_score", 0)
        completion_bonus = 100  # Bonus for completing the game
        
        # Update player's score with completion bonus
        try:
            update_score_url = f"{PLAYER_SERVICE_URL}/player/{player_id}/score"
            score_payload = {"points": completion_bonus}
            score_response = requests.patch(update_score_url, json=score_payload, timeout=5)
            
            if score_response.status_code == 200:
                new_score = score_response.json().get("new_sum_score", current_score + completion_bonus)
                score_message = f"FINAL SCORE: {new_score} (includes +{completion_bonus} completion bonus!)"
                
                # Log this achievement
                send_activity_log(player_id, f"Completed the game! (+{completion_bonus} score)")
                logger.info(f"Player {player_id} completed the game with final score {new_score}")
            else:
                logger.warning(f"Failed to award completion bonus: {score_response.status_code}")
                score_message = f"FINAL SCORE: {current_score}"
        except Exception as e:
            logger.error(f"Error updating score for game completion: {str(e)}")
            score_message = f"FINAL SCORE: {current_score}"
        
        return jsonify({
            "message": "Congratulations! You've completed the dungeon!",
            "description": "You've reached the end of your journey and emerged victorious!",
            "end_of_game": True,
            "player_score": current_score + completion_bonus,
            "score_message": score_message
        })
    except Exception as e:
        logger.error(f"Error creating end of game response: {str(e)}")
        return jsonify({
            "message": "Congratulations! You've completed the dungeon!",
            "description": "The game is over, but there was an error retrieving your final stats.",
            "end_of_game": True,
            "player_score": 0,
            "score_message": "FINAL SCORE: 0"
        }), 500

@app.route('/game/hard-reset/<int:player_id>', methods=['POST'])
def hard_reset(player_id):
    """
    Performs a complete hard reset of the player's game state.
    This is more thorough than the regular reset and is intended for debugging.
    """
    logger.info(f"Performing HARD RESET for player {player_id}")
    
    reset_results = {
        "player_reset": False,
        "inventory_reset": False,
        "interactions_reset": False,
        "room_reset": False
    }
    
    try:
        # 1. Reset player stats and location
        try:
            # Get player data to find max health
            player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
            if player_response.status_code == 200:
                player_data = player_response.json()
                max_health = player_data.get("max_health", player_data.get("MaxHealth", 100))
                
                # Reset player to initial state
                player_reset = requests.put(
                    f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                    json={
                        "current_health": max_health,
                        "max_health": max_health,
                        "damage": 10,
                        "room_id": 0,
                        "sum_score": 0  # Reset score to 0
                    },
                    timeout=5
                )
                
                if player_reset.status_code == 200:
                    reset_results["player_reset"] = True
                    logger.info(f"Successfully reset player {player_id} stats and location")
        except Exception as e:
            logger.error(f"Error resetting player stats: {str(e)}")
            
        # 2. Clear player's inventory
        try:
            inventory_reset = requests.delete(
                f"{INVENTORY_SERVICE_URL}/inventory/player/{player_id}",
                timeout=5
            )
            if inventory_reset.status_code in [200, 404]:
                reset_results["inventory_reset"] = True
                logger.info(f"Successfully cleared inventory for player {player_id}")
        except Exception as e:
            logger.error(f"Error clearing inventory: {str(e)}")
            
        # 3. Reset player-room interactions
        try:
            interaction_reset = requests.post(
                f"{PLAYER_ROOM_INTERACTION_SERVICE_URL}/player/{player_id}/reset",
                timeout=5
            )
            if interaction_reset.status_code == 200:
                reset_results["interactions_reset"] = True
                logger.info(f"Successfully reset player-room interactions for player {player_id}")
        except Exception as e:
            logger.error(f"Error resetting player-room interactions: {str(e)}")
            
        # 4. Reset room states
        try:
            # Reset rooms to their default state
            room_defaults = [
                {"room_id": 1, "item_ids": [1, 2], "enemy_ids": [], "door_locked": False},
                {"room_id": 2, "item_ids": [3, 5], "enemy_ids": [1], "door_locked": False},
                {"room_id": 3, "item_ids": [4], "enemy_ids": [2], "door_locked": True}
            ]
            
            room_reset_success = True
            for room_data in room_defaults:
                room_id = room_data.pop("room_id")  # Extract room_id from the data
                room_reset = requests.put(
                    f"{ROOM_SERVICE_URL}/room/{room_id}",
                    json=room_data,
                    timeout=5
                )
                if room_reset.status_code != 200:
                    room_reset_success = False
                    logger.error(f"Failed to reset room {room_id}")
                    
            if room_reset_success:
                reset_results["room_reset"] = True
                logger.info("Successfully reset all rooms to default state")
        except Exception as e:
            logger.error(f"Error resetting rooms: {str(e)}")
            
        # Send a hard reset log event via RabbitMQ
        send_activity_log(player_id, "HARD RESET performed on game")
        
        # Determine if all reset operations were successful
        all_reset = all(reset_results.values())
        
        if all_reset:
            return jsonify({
                "success": True,
                "message": "Game has been completely reset to initial state",
                "details": reset_results
            })
        else:
            return jsonify({
                "success": False,
                "message": "Some game elements could not be reset",
                "details": reset_results
            })
            
    except Exception as e:
        logger.error(f"Unhandled exception during hard reset: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Hard reset failed: {str(e)}",
            "details": reset_results
        }), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5014, debug=True)
