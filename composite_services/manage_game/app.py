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
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory_service:5001")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")

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

@app.route('/game/reset/<int:player_id>', methods=['POST'])
def reset_character_progress(player_id):
    """
    Resets the player's game progress by updating their room and health.
    """
    logger.debug(f"Resetting progress for player {player_id}")
    
    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    if player_response.status_code != 200:
        return jsonify({"error": "Player not found"}), 404

    # ✅ Reset player progress
    requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}", json={"health": 100, "room_id": 1})

    # ✅ Reset all enemies
    requests.get(f"{ENEMY_SERVICE_URL}/reset")

    # ✅ Log reset via RabbitMQ
    log_activity(player_id, "Game progress reset")

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
        
        # Step 2: Reset player stats and location
        try:
            player_reset = requests.put(
                f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                json={"health": 100, "damage": 10, "room_id": 0},
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
        log_activity(player_id, f"Full game reset performed for {player_name}")
        
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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5014, debug=True)
