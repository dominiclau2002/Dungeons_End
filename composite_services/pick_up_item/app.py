from flask import Flask, jsonify, request
import requests
import os
import pika
import json
import logging
from datetime import datetime
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Microservice URLs
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
INVENTORY_SERVICE_URL = os.getenv(
    "INVENTORY_SERVICE_URL", "http://inventory_service:5001")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
APPLY_ITEM_EFFECTS_SERVICE_URL = os.getenv("APPLY_ITEM_EFFECTS_SERVICE_URL", "http://apply_item_effects_service:5025")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
ACTIVITY_LOG_QUEUE = "activity_log_queue"


def send_activity_log(player_id, action):
    """Send an activity log message to RabbitMQ"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST))
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


@app.route('/room/<int:room_id>/item/<int:item_id>/pickup', methods=['POST'])
def pick_up_item(room_id, item_id):
    """
    Picks up an item from a room and adds it to the player's inventory.
    Player ID is assumed to be 1.
    """
    player_id = 1  # Hardcoded player ID

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

    # Step 3: Remove the item from the room
    remove_url = f"{ROOM_SERVICE_URL}/room/{room_id}/item/{item_id}"
    logger.debug(f"Removing item from room: {remove_url}")
    
    # Try up to 3 times to remove the item from the room
    max_attempts = 3
    for attempt in range(max_attempts):
        remove_response = requests.delete(remove_url)
        
        if remove_response.status_code == 200:
            logger.debug("Item successfully removed from room")
            break
        else:
            logger.warning(f"Attempt {attempt+1}/{max_attempts} to remove item failed: {remove_response.text}")
            if attempt < max_attempts - 1:
                # If this isn't the last attempt, check if the item is still in the room
                room_check = requests.get(f"{ROOM_SERVICE_URL}/room/{room_id}")
                if room_check.status_code == 200:
                    room_data = room_check.json()
                    item_ids = []
                    # Try different possible key names
                    if "ItemIDs" in room_data and isinstance(room_data["ItemIDs"], list):
                        item_ids = room_data["ItemIDs"]
                    elif "item_ids" in room_data and isinstance(room_data["item_ids"], list):
                        item_ids = room_data["item_ids"]
                    
                    # If item is not in room, we can consider it removed
                    if item_id not in item_ids:
                        logger.info(f"Item {item_id} not found in room {room_id} after initial failure, but seems removed.")
                        break
                
                # Wait briefly before retrying
                time.sleep(0.5)
    
    # If all attempts failed, return error
    if remove_response.status_code != 200:
        logger.error(f"Failed to remove item from room after {max_attempts} attempts: {remove_response.text}")
        return jsonify({"error": "Failed to remove item from room"}), 500

    # Step 4: Add the item to the player's inventory
    inventory_url = f"{INVENTORY_SERVICE_URL}/inventory/player/{player_id}/item/{item_id}"
    logger.debug(f"Adding item to inventory: {inventory_url}")
    inventory_response = requests.post(inventory_url)

    if inventory_response.status_code != 201:
        logger.error(
            f"Failed to add item to inventory: {inventory_response.text}")
        # If adding to inventory fails, try to put the item back in the room
        restore_url = f"{ROOM_SERVICE_URL}/room/{room_id}/item/{item_id}"
        logger.debug(f"Attempting to restore item to room: {restore_url}")
        restore_response = requests.post(restore_url)

        if restore_response.status_code != 200:
            logger.error(
                f"Also failed to restore item to room: {restore_response.text}")

        return jsonify({"error": "Failed to add item to inventory"}), 500

    logger.debug("Item successfully added to inventory")

    # Step 5: Log the activity via RabbitMQ
    log_message = f"Picked up {item_name} (ID: {item_id}) from room {room_id}"
    send_activity_log(player_id, log_message)
    
    # Step 6: Check for special item effects and apply them
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
    
    try:
        send_activity_log(player_id, action)
        return jsonify({"message": "Activity logged successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}")
        return jsonify({"error": f"Failed to log activity: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5019, debug=True)
