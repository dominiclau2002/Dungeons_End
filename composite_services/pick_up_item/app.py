from flask import Flask, jsonify, request
import requests
import os
import logging
from datetime import datetime
import time
from composite_services.utilities.activity_logger import log_activity


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Microservice URLs
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory_service:5001")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
APPLY_ITEM_EFFECTS_SERVICE_URL = os.getenv("APPLY_ITEM_EFFECTS_SERVICE_URL", "http://apply_item_effects_service:5025")
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

@app.route('/room/<int:room_id>/item/<int:item_id>/pickup', methods=['POST'])
def pick_up_item(room_id, item_id):
    """
    Picks up an item from a room and adds it to the player's inventory.
    Expects player_id in the request JSON, falls back to default if not provided.
    """
    data = request.get_json() or {}
    player_id = data.get("player_id")
    
    if not player_id:
        logger.warning("No player_id provided in request, operation will fail")
        return jsonify({"error": "player_id is required"}), 400

    logger.debug(
        f"Attempting to pick up item {item_id} from room {room_id} for player {player_id}")

    # Step 1: Check if the item exists in the room
    room_response = requests.get(f"{ROOM_SERVICE_URL}/room/{room_id}")
    if room_response.status_code != 200:
        logger.warning(f"Room {room_id} not found: {room_response.text}")
        return jsonify({"error": "Room not found"}), 404

    room_data = room_response.json()
    logger.debug(f"Room data received: {room_data}")

    # Check if the item is in the room (trying different possible key names)
    item_ids = []
    if "ItemIDs" in room_data and isinstance(room_data["ItemIDs"], list):
        item_ids = room_data["ItemIDs"]
    elif "item_ids" in room_data and isinstance(room_data["item_ids"], list):
        item_ids = room_data["item_ids"]
    elif "items" in room_data and isinstance(room_data["items"], list):
        # Extract IDs from items list if it's a list of objects
        for item in room_data["items"]:
            if isinstance(item, dict) and "id" in item:
                item_ids.append(item["id"])
            elif isinstance(item, int):
                item_ids.append(item)

    logger.debug(f"Item IDs in room: {item_ids}")

    if item_id not in item_ids:
        logger.warning(f"Item {item_id} not found in room {room_id}")
        return jsonify({"error": "Item not found in the room"}), 404

    # Step 2: Get item details to include in the activity log
    item_response = requests.get(f"{ITEM_SERVICE_URL}/item/{item_id}")
    if item_response.status_code != 200:
        logger.error(f"Failed to get item details: {item_response.text}")
        return jsonify({"error": "Failed to get item details"}), 500

    item_data = item_response.json()
    # Check different possible property names for the item name
    item_name = None
    for key in ["Name", "name"]:
        if key in item_data:
            item_name = item_data[key]
            break
    if not item_name:
        item_name = f"Item {item_id}"

    logger.debug(f"Item details retrieved: {item_name}")

    # Step 3: Check if the player has already picked up this item
    # by querying the player_room_interaction service
    interaction_url = f"{PLAYER_ROOM_INTERACTION_SERVICE_URL}/player/{player_id}/room/{room_id}/interactions"
    interaction_response = requests.get(interaction_url)
    
    if interaction_response.status_code == 200:
        interaction_data = interaction_response.json()
        items_picked = interaction_data.get('items_picked', [])
        
        if item_id in items_picked:
            logger.warning(f"Player {player_id} has already picked up item {item_id} from room {room_id}")
            return jsonify({
                "error": "You have already picked up this item",
                "player_id": player_id,
                "item_id": item_id,
                "room_id": room_id
            }), 400

    # Step 4: Record that the player picked up the item using player_room_interaction service
    pickup_url = f"{PLAYER_ROOM_INTERACTION_SERVICE_URL}/player/{player_id}/room/{room_id}/item/{item_id}/pickup"
    pickup_response = requests.post(pickup_url)
    
    if pickup_response.status_code not in (200, 201):
        logger.error(f"Failed to record item pickup in player_room_interaction service: {pickup_response.text}")
        return jsonify({"error": "Failed to record item pickup"}), 500
    
    logger.debug(f"Successfully recorded pickup of item {item_id} in room {room_id} for player {player_id}")

    # Step 5: Add the item to the player's inventory
    inventory_url = f"{INVENTORY_SERVICE_URL}/inventory/player/{player_id}/item/{item_id}"
    logger.debug(f"Adding item to inventory: {inventory_url}")
    inventory_response = requests.post(inventory_url)

    if inventory_response.status_code != 201:
        logger.error(
            f"Failed to add item to inventory: {inventory_response.text}")
        # If adding to inventory fails, try to remove the record from player_room_interaction service
        # (This is a cleanup step, but we don't have an API for this yet)
        return jsonify({"error": "Failed to add item to inventory"}), 500

    logger.debug("Item successfully added to inventory")

    # Step 6: Log the activity via activity log service
    log_message = f"Picked up {item_name} (ID: {item_id}) from room {room_id}"
    log_activity(player_id, log_message)
    
    # Step 7: Check for special item effects and apply them
    response_data = {
        "message": f"Successfully picked up {item_name}",
        "player_id": player_id,
        "item_id": item_id,
        "room_id": room_id,
        "item_name": item_name
    }
    
    try:
        # Call the apply_item_effects service to apply any special effects
        effects_url = f"{APPLY_ITEM_EFFECTS_SERVICE_URL}/apply_item_effect"
        effects_data = {
            "player_id": player_id,
            "item_id": item_id
        }
        
        logger.debug(f"Calling apply_item_effects service: {effects_url} with data: {effects_data}")
        effects_response = requests.post(effects_url, json=effects_data)
        
        if effects_response.status_code == 200:
            effects_data = effects_response.json()
            logger.debug(f"Item effects response: {effects_data}")
            
            # If the item had special effects, include them in response
            if effects_data.get("effect_applied", False):
                response_data["effect_applied"] = True
                response_data["effect_description"] = effects_data.get("effect_description", "")
                
                # Include any additional effect data from the effects service
                for key, value in effects_data.items():
                    if key not in ["message", "item_id", "item_name", "effect_applied", "effect_description"]:
                        response_data[key] = value
        else:
            logger.warning(f"Failed to apply item effects: {effects_response.text}")
    except Exception as e:
        logger.error(f"Error calling apply_item_effects service: {str(e)}")
        # Continue even if effects service fails - the item is still picked up

    return jsonify(response_data), 200


@app.route('/activity/log', methods=['POST'])
def activity_log():
    """
    Endpoint for logging player activities.
    Expects JSON with player_id and action.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    player_id = data.get("player_id")
    action = data.get("action")
    
    if not player_id or not action:
        return jsonify({"error": "player_id and action are required"}), 400
    
    success = log_activity(player_id, action)
    if success:
        return jsonify({"message": "Activity logged successfully"}), 200
    else:
        return jsonify({"error": "Failed to log activity"}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5019, debug=True)