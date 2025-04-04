from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime
import logging
from composite_services.utilities.activity_logger import log_activity


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv(
    "PLAYER_SERVICE_URL", "http://player_service:5000")
ENTERING_ROOM_SERVICE_URL = os.getenv(
    "ENTERING_ROOM_SERVICE_URL", "http://entering_room_service:5011")
PICK_UP_ITEM_SERVICE_URL = os.getenv(
    "PICK_UP_ITEM_SERVICE_URL", "http://pick_up_item_service:5019")
OPEN_INVENTORY_SERVICE_URL = os.getenv(
    "OPEN_INVENTORY_SERVICE_URL", "http://open_inventory_service:5010")
ITEM_SERVICE_URL = os.getenv(
    "ITEM_SERVICE_URL", "http://item_service:5020")
ROOM_SERVICE_URL = os.getenv(
    "ROOM_SERVICE_URL", "http://room_service:5030")
COMBAT_SERVICE_URL = os.getenv(
    "COMBAT_SERVICE_URL", "http://fight_enemy_service:5009")
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


@app.route("/")
def home():
    """Renders the game UI."""
    return render_template("index.html")




@app.route("/get_player_room", methods=["GET"])
def get_player_room():
    """Gets the player's current room ID, assuming player ID is always 1."""
    player_id = 1  # Hardcoded player ID as requested

    # Get player data from player service
    response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    if response.status_code != 200:
        return jsonify({"error": "Could not retrieve player data"}), response.status_code

    player_data = response.json()
    room_id = player_data.get("RoomID", 0)
    logger.debug(f"GET /get_player_room - Current player room ID: {room_id}")
    return jsonify({"room_id": room_id})


@app.route("/enter_room", methods=["POST"])
def enter_room():
    """Proxy to the composite service."""
    data = request.get_json() or {}
    
    # Set default player ID
    if "player_id" not in data:
        data["player_id"] = 1
    
    # Handle target_room_id if provided (for room refresh after combat)
    target_room_id = data.get("target_room_id")
    
    if target_room_id is not None:
        logger.debug(f"Target room ID provided: {target_room_id}. Refreshing current room.")
        # Direct call to specific room endpoint
        room_url = f"{ENTERING_ROOM_SERVICE_URL}/room/{target_room_id}"
    else:
        # Use the next room endpoint which increments the room
        logger.debug("No target room ID - using next_room endpoint.")
        room_url = f"{ENTERING_ROOM_SERVICE_URL}/next_room"
    
    try:
        logger.debug(f"Forwarding request to {room_url}")
        response = requests.post(room_url, json=data)
        
        # Check for room-specific errors first
        if response.status_code == 403:
            # Locked door or enemies present - just pass through
            return jsonify(response.json()), response.status_code
            
        # Check if the response status code indicates room not found (404)
        # which might mean we've reached the end of the game
        if response.status_code == 404 and not target_room_id:
            try:
                # Parse the response to check if this is truly the end of the game
                error_data = response.json()
                
                # Check if this is a room that doesn't exist response (end of game)
                if "room not found" in error_data.get("error", "").lower():
                    # Get the current player room to check if it's beyond what we have
                    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{data['player_id']}")
                    if player_response.status_code == 200:
                        player_data = player_response.json()
                        current_room = player_data.get("RoomID", player_data.get("room_id", 0))
                        
                        # If player is already beyond room 3, it's definitely end of game
                        if current_room >= 3:
                            logger.info(f"End of game detected - player in room {current_room} trying to go beyond")
                            return create_end_of_game_response(data['player_id'])
                    
                    # If we can't determine the room, just pass through the 404
                    return jsonify(error_data), 404
                
                # For other 404s, pass through
                return jsonify(error_data), 404
            except Exception as e:
                logger.error(f"Error parsing 404 response: {str(e)}")
                # If we can't parse it, assume it's not end of game
                return jsonify({"error": "Room not found"}), 404
        
        # For successful responses, just pass through
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        logger.error(f"Error connecting to entering_room service: {str(e)}")
        return jsonify({"error": "Failed to connect to room service"}), 500


def create_end_of_game_response(player_id):
    """Creates a custom response for end of game."""
    # Get player data for personalization
    try:
        player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
        player_data = player_response.json() if player_response.status_code == 200 else {}
        
        player_name = player_data.get("Name", player_data.get("name", "Adventurer"))
        
        return jsonify({
            "end_of_game": True,
            "message": f"Congratulations, {player_name}! You have completed the dungeon!",
            "description": "You stand before the exit of the dungeon, treasures in hand and tales to tell. The light of the outside world beckons you. Your adventure has come to a successful end."
        }), 200
    except Exception as e:
        logger.error(f"Error creating end game response: {str(e)}")
        return jsonify({
            "end_of_game": True,
            "message": "Congratulations! You have completed the dungeon!",
            "description": "Your adventure has come to a successful end."
        }), 200


@app.route("/pick_up_item", methods=["POST"])
def pick_up_item():
    """Proxy to the pick_up_item composite service."""
    data = request.get_json()
    room_id = data.get('room_id')
    item_id = data.get('item_id')
    
    logger.debug(f"POST /pick_up_item - Delegating to pick_up_item service")
    
    if not room_id or not item_id:
        return jsonify({"error": "Room ID and Item ID are required"}), 400
    
    # Simply pass the request to the composite service
    try:
        pickup_url = f"{PICK_UP_ITEM_SERVICE_URL}/room/{room_id}/item/{item_id}/pickup"
        response = requests.post(pickup_url)
        
        # Pass through the response
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        logger.error(f"Error connecting to pick_up_item service: {str(e)}")
        return jsonify({"error": f"Failed to connect to pick up item service: {str(e)}"}), 500




@app.route("/view_inventory", methods=["GET"])
def view_inventory():
    """Retrieves the player's inventory with item details."""
    player_id = 1  # Hardcoded player ID

    logger.debug(
        f"GET /view_inventory - Retrieving inventory for player ID: {player_id}")

    # Log the inventory view activity
    log_activity(player_id, "Viewed inventory")

    # Call the open_inventory service
    inventory_url = f"{OPEN_INVENTORY_SERVICE_URL}/inventory/{player_id}"
    logger.debug(f"Calling inventory service: {inventory_url}")

    response = requests.get(inventory_url)
    logger.debug(
        f"Inventory service response: {response.status_code} - {response.text}")

    if response.status_code != 200:
        logger.error(f"Failed to retrieve inventory: {response.text}")
        return jsonify({"error": "Failed to retrieve inventory"}), response.status_code

    # The inventory data already contains the enhanced items with descriptions
    # Pass it through directly instead of just extracting IDs
    inventory_data = response.json()

    return jsonify({
        "player_id": player_id,
        "items": inventory_data.get("inventory", [])
    })

@app.route("/fetch_item_details", methods=["GET"])
def fetch_item_details():
    """Fetches details for a specific item."""
    item_id = request.args.get('item_id')

    if not item_id:
        return jsonify({"error": "Item ID is required"}), 400

    # Call the item service to get item details
    item_url = f"{ITEM_SERVICE_URL}/item/{item_id}"
    logger.debug(f"Fetching item details from: {item_url}")

    response = requests.get(item_url)
    logger.debug(
        f"Item service response: {response.status_code} - {response.text}")

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch item details"}), response.status_code

    return jsonify(response.json())


@app.route("/fetch_item_details_batch", methods=["POST"])
def fetch_item_details_batch():
    """Fetches details for multiple items at once."""
    data = request.get_json()
    item_ids = data.get('item_ids', [])

    if not item_ids:
        return jsonify({"error": "Item IDs are required"}), 400

    items = []
    for item_id in item_ids:
        # Call the item service to get item details
        item_url = f"{ITEM_SERVICE_URL}/item/{item_id}"
        logger.debug(f"Fetching item details from: {item_url}")

        response = requests.get(item_url)
        logger.debug(
            f"Item service response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            items.append(response.json())
        else:
            # Include a placeholder for failed items
            items.append({
                "ItemID": item_id,
                "Name": "Unknown Item",
                "Description": "Item details unavailable"
            })

    return jsonify({"items": items})


@app.route("/room_info/<int:room_id>", methods=["GET"])
def get_room_info(room_id):
    """Gets room information without entering the room."""
    logger.debug(f"GET /room_info/{room_id} - Checking room info")

    # This endpoint just forwarded to the room service
    room_url = f"{ROOM_SERVICE_URL}/room/{room_id}"
    logger.debug(f"Calling room service: {room_url}")

    response = requests.get(room_url)
    if response.status_code != 200:
        logger.error(f"Failed to get room info: {response.text}")
        return jsonify({"error": "Room not found"}), 404

    return jsonify(response.json())


@app.route("/player_stats", methods=["GET"])
def player_stats():
    """Retrieves the player's stats from the player service."""
    player_id = 1  # Hardcoded player ID

    logger.debug(
        f"GET /player_stats - Retrieving stats for player ID: {player_id}")

    # Call the player service to get player data
    player_url = f"{PLAYER_SERVICE_URL}/player/{player_id}"
    logger.debug(f"Calling player service: {player_url}")

    try:
        response = requests.get(player_url)
        logger.debug(
            f"Player service response: {response.status_code} - {response.text}")

        if response.status_code != 200:
            logger.error(f"Failed to retrieve player stats: {response.text}")
            return jsonify({"error": "Failed to retrieve player stats"}), response.status_code

        # Return the player data
        player_data = response.json()
        return jsonify(player_data)

    except requests.RequestException as e:
        logger.error(f"Request error when calling player service: {str(e)}")
        return jsonify({"error": "Failed to connect to player service"}), 500


@app.route("/combat/start/<int:enemy_id>", methods=["POST"])
def start_combat(enemy_id):
    """Starts combat with an enemy"""
    player_id = 1  # Hardcoded player ID
    
    # Call the fight_enemy service
    combat_url = f"{COMBAT_SERVICE_URL}/combat/start/{enemy_id}"
    combat_data = {"player_id": player_id}
    
    try:
        response = requests.post(combat_url, json=combat_data)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to start combat"}), response.status_code
        
        # Just pass through the response from the combat service
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Request error when calling combat service: {str(e)}")
        return jsonify({"error": "Failed to connect to combat service"}), 500


@app.route("/combat/attack", methods=["POST"])
def combat_attack():
    """Proxy to the fight_enemy composite service."""
    data = request.get_json()
    
    logger.debug(f"POST /combat/attack - Delegating to fight_enemy service")
    
    # Add player_id if not present
    if "player_id" not in data:
        data["player_id"] = 1
    
    # Simply pass the request to the composite service
    try:
        attack_url = f"{COMBAT_SERVICE_URL}/combat/attack"
        response = requests.post(attack_url, json=data)
        
        # Pass through the response
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        logger.error(f"Error connecting to combat service: {str(e)}")
        return jsonify({"error": f"Failed to connect to combat service: {str(e)}"}), 500


@app.route("/reset_game", methods=["POST"])
def reset_game():
    """Reset the player's progress by setting them back to room 0."""
    player_id = 1  # Hardcoded player ID
    
    logger.debug(f"POST /reset_game - Calling full game reset for player {player_id}")
    
    try:
        # Call the manage_game service for a full reset
        response = requests.post(
            f"{os.getenv('MANAGE_GAME_SERVICE_URL', 'http://manage_game_service:5014')}/game/full-reset/{player_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Game successfully reset for player {player_id}")
            
            # Call enter_room to properly initialize the starting room for display
            # We directly call the enter_room endpoint with target_room_id=0
            enter_room_response = requests.post(
                f"{ENTERING_ROOM_SERVICE_URL}/room/0",
                json={"player_id": player_id}
            )
            
            if enter_room_response.status_code == 200:
                room_data = enter_room_response.json()
                return jsonify({
                    "success": True,
                    "message": "Game has been reset successfully.",
                    "end_of_game": False,
                    **room_data
                })
            else:
                logger.error(f"Failed to enter starting room after reset: {enter_room_response.text}")
                return jsonify({
                    "success": True,
                    "message": "Game has been reset, but failed to load starting room. Please refresh.",
                    "error_details": enter_room_response.text
                })
        else:
            logger.error(f"Failed to reset game: {response.text}")
            try:
                error_details = response.json()
                return jsonify({
                    "success": False,
                    "message": "Failed to reset game.",
                    "error_details": error_details
                }), 500
            except:
                return jsonify({
                    "success": False,
                    "message": "Failed to reset game. Unknown error from reset service."
                }), 500
    except requests.RequestException as e:
        logger.error(f"Error connecting to manage_game service: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to connect to game management service: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
