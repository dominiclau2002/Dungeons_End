from flask import Flask, render_template, request, jsonify
import requests
import os
import logging

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
    """Handles room navigation. Auto-increments room ID from player's current room."""
    player_id = 1  # Hardcoded player ID
    data = request.get_json()
    target_room_id = data.get('target_room_id', None)

    logger.debug(f"POST /enter_room - Starting to process for player ID: {player_id}")

    # If target_room_id is provided, use it (for reset functionality)
    if target_room_id is not None:
        next_room_id = target_room_id
        logger.debug(f"Using provided target room ID: {next_room_id}")
    else:
        # Otherwise, get player's current room and increment it
        player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
        if player_response.status_code != 200:
            logger.error(f"Failed to get player data: {player_response.text}")
            return jsonify({"error": "Could not retrieve player data"}), player_response.status_code

        player_data = player_response.json()
        logger.debug(f"Player data received: {player_data}")

        # Check if RoomID exists in player_data, if not try lowercase version
        if "RoomID" in player_data:
            current_room_id = player_data.get("RoomID", 0)
        elif "room_id" in player_data:
            current_room_id = player_data.get("room_id", 0)
        else:
            logger.warning("RoomID not found in player data, defaulting to 0")
            current_room_id = 0

        # Increment room ID by 1 for the next room
        next_room_id = current_room_id + 1
        logger.debug(f"Current room ID: {current_room_id}, Next room ID: {next_room_id}")

    # Call entering room service with the room ID
    room_data = {"player_id": player_id}
    room_url = f"{ENTERING_ROOM_SERVICE_URL}/room/{next_room_id}"
    logger.debug(f"Calling entering room service: {room_url} with data: {room_data}")

    try:
        room_response = requests.post(room_url, json=room_data)
        logger.debug(f"Room service response: {room_response.status_code} - {room_response.text}")

        # Check if we got a locked door response (status code 403)
        if room_response.status_code == 403:
            try:
                response_data = room_response.json()
                # This is a locked door response
                logger.debug(f"Room {next_room_id} is locked: {response_data}")
                return jsonify({
                    "error": response_data.get("error", "This door is locked! You need a Lockpick to proceed."),
                    "door_locked": True
                }), 403
            except Exception as e:
                logger.error(f"Error parsing locked door response: {str(e)}")
                # If we can't parse the JSON, still return a locked door message
                return jsonify({
                    "error": "This door is locked! You need a Lockpick to proceed.",
                    "door_locked": True
                }), 403
                
        # For room not found (404) or other client errors (4xx), check for end of game
        elif room_response.status_code == 404 or (400 <= room_response.status_code < 500):
            logger.warning(f"Failed to enter room {next_room_id}: {room_response.text}")
            if next_room_id > 3:  # If trying to go beyond the known number of rooms
                return jsonify({
                    "end_of_game": True,
                    "message": "You've reached the end of the game!"
                })
            else:
                # For other client errors, try to parse the response
                try:
                    error_data = room_response.json()
                    return jsonify({"error": error_data.get("error", "Cannot enter this room.")}), room_response.status_code
                except:
                    return jsonify({"error": "Cannot enter this room."}), room_response.status_code
        
        # For server errors (5xx), return a generic error
        elif room_response.status_code >= 500:
            return jsonify({"error": "Server error. Please try again later."}), room_response.status_code
            
        # If we get a 200 OK, process the room data normally
        room_data = room_response.json()
        return jsonify({
            "end_of_game": False,
            **room_data
        })
        
    except requests.RequestException as e:
        logger.error(f"Request error when calling entering room service: {str(e)}")
        return jsonify({"error": "Failed to connect to room service."}), 500


@app.route("/pick_up_item", methods=["POST"])
def pick_up_item():
    """Handles item pickup using the pick_up_item service."""
    player_id = 1  # Hardcoded player ID
    data = request.get_json()
    room_id = data.get('room_id')
    item_id = data.get('item_id')

    logger.debug(f"Attempting to pick up item {item_id} from room {room_id}")

    if not room_id or not item_id:
        logger.error("Missing room_id or item_id in request")
        return jsonify({"error": "Room ID and Item ID are required"}), 400

    # Call the pick_up_item service
    pickup_url = f"{PICK_UP_ITEM_SERVICE_URL}/room/{room_id}/item/{item_id}/pickup"
    logger.debug(f"Calling pick up item service: {pickup_url}")

    response = requests.post(pickup_url)
    logger.debug(
        f"Pick up item response: {response.status_code} - {response.text}")

    if response.status_code != 200:
        return jsonify({
            "success": False,
            "error": "Failed to pick up item",
            "details": response.json() if response.text else None
        }), response.status_code

    # Return the response from the pick up item service
    return jsonify({
        "success": True,
        **response.json()
    })


@app.route("/reset_game", methods=["POST"])
def reset_game():
    """Resets the game by sending the player back to room 0."""
    # Call enter_room with target_room_id = 0
    return enter_room()


@app.route("/view_inventory", methods=["GET"])
def view_inventory():
    """Retrieves the player's inventory with item details."""
    player_id = 1  # Hardcoded player ID

    logger.debug(f"GET /view_inventory - Retrieving inventory for player ID: {player_id}")
    
    # Call the open_inventory service
    inventory_url = f"{OPEN_INVENTORY_SERVICE_URL}/inventory/{player_id}"
    logger.debug(f"Calling inventory service: {inventory_url}")
    
    response = requests.get(inventory_url)
    logger.debug(f"Inventory service response: {response.status_code} - {response.text}")
    
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
    logger.debug(f"Item service response: {response.status_code} - {response.text}")
    
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
        logger.debug(f"Item service response: {response.status_code} - {response.text}")
        
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
