from flask import Flask, jsonify, request
import requests
import os
import pika
import json
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
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
# Fix: Use the actual atomic inventory service, not the composite service
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory_service:5001")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")
PLAYER_ROOM_INTERACTION_SERVICE_URL = os.getenv("PLAYER_ROOM_INTERACTION_SERVICE_URL", "http://player_room_interaction_service:5014")

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


@app.route('/room/<int:room_id>', methods=['POST'])
def enter_room(room_id):
    data = request.get_json()
    player_id = data.get("player_id")

    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # Check if the player is trying to move to the next room (not room 0 - game start)
    if room_id > 0:
        # First check if player has undefeated enemies in their current room
        player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
        if player_response.status_code == 200:
            player_data = player_response.json()
            current_room_id = None
            
            # Get current room ID
            for key in ["RoomID", "room_id"]:
                if key in player_data and player_data[key] is not None:
                    current_room_id = player_data[key]
                    break
                    
            if current_room_id is not None and current_room_id > 0:
                # Get enemies in current room
                current_room_response = requests.get(f"{ROOM_SERVICE_URL}/room/{current_room_id}")
                if current_room_response.status_code == 200:
                    current_room = current_room_response.json()
                    
                    # Get all enemy IDs from the room
                    room_enemy_ids = []
                    if 'enemy_ids' in current_room and isinstance(current_room['enemy_ids'], list):
                        room_enemy_ids = current_room['enemy_ids']
                    elif 'EnemyIDs' in current_room and isinstance(current_room['EnemyIDs'], list):
                        room_enemy_ids = current_room['EnemyIDs']
                    elif 'enemies' in current_room and isinstance(current_room['enemies'], list):
                        for enemy in current_room['enemies']:
                            if isinstance(enemy, dict):
                                enemy_id = enemy.get("id") or enemy.get("EnemyID")
                                if enemy_id:
                                    room_enemy_ids.append(enemy_id)
                            elif isinstance(enemy, int):
                                room_enemy_ids.append(enemy)
                    
                    logger.debug(f"Room {current_room_id} has enemies: {room_enemy_ids}")
                    
                    # If there are enemies in the room, check if all have been defeated
                    if room_enemy_ids:
                        # Get player's interactions with this room
                        interaction_url = f"{PLAYER_ROOM_INTERACTION_SERVICE_URL}/player/{player_id}/room/{current_room_id}/interactions"
                        logger.debug(f"Checking player interactions: {interaction_url}")
                        
                        try:
                            interaction_response = requests.get(interaction_url)
                            if interaction_response.status_code == 200:
                                interaction_data = interaction_response.json()
                                logger.debug(f"Player interactions: {interaction_data}")
                                
                                # Get the list of enemies the player has defeated in this room
                                defeated_enemies = interaction_data.get('enemies_defeated', [])
                                logger.debug(f"Player has defeated enemies: {defeated_enemies}")
                                
                                # Check if there are undefeated enemies
                                undefeated_enemies = [enemy_id for enemy_id in room_enemy_ids if enemy_id not in defeated_enemies]
                                
                                if undefeated_enemies:
                                    logger.debug(f"Player {player_id} cannot proceed - undefeated enemies remain in room {current_room_id}: {undefeated_enemies}")
                                    return jsonify({
                                        "error": "You cannot leave this room until you defeat all enemies!",
                                        "enemies_present": True
                                    }), 403
                            else:
                                logger.error(f"Failed to get player interactions: {interaction_response.text}")
                                # We'll be cautious and not allow the player to proceed if we can't verify
                                return jsonify({
                                    "error": "Could not verify enemy status. Please try again.",
                                    "enemies_present": True
                                }), 500
                        except Exception as e:
                            logger.error(f"Error checking player interactions: {str(e)}")
                            return jsonify({
                                "error": "Could not verify enemy status. Please try again.",
                                "enemies_present": True
                            }), 500

    # ✅ Fetch room details
    logger.debug(f"Fetching details for room {room_id}")
    room_response = requests.get(f"{ROOM_SERVICE_URL}/room/{room_id}")
    if room_response.status_code != 200:
        logger.error(f"Room not found: {room_response.text}")
        return jsonify({"error": "Room not found"}), 404

    room = room_response.json()
    logger.debug(f"Room data received: {room}")
    
    # ✅ Check if door is locked - using BOOLEAN type directly
    door_locked = False
    
    if "DoorLocked" in room:
        # Get the boolean value directly
        raw_value = room["DoorLocked"]
        logger.debug(f"DoorLocked value: {raw_value}, Type: {type(raw_value).__name__}")
        
        # MySQL BOOLEAN is returned as a Python boolean in most cases
        if isinstance(raw_value, bool):
            door_locked = raw_value
        else:
            # Simple fallback for any non-boolean types
            try:
                # Convert to boolean (works for 0/1, "True"/"False", etc.)
                door_locked = bool(raw_value)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert DoorLocked value {raw_value} to boolean")
    
    # For room_id 3, verify the door is locked
    if room_id == 3:
        logger.debug(f"Room 3 door lock status: {door_locked}")
        # Ensure door lock state matches what we expect for room 3
        door_locked = True
    
    logger.debug(f"Final door locked status for room {room_id}: {door_locked}")
    
    if door_locked:
        logger.debug(f"Room {room_id} door is locked, checking if player {player_id} has the key (item ID 5)")
        
        # Check inventory first - the player might have the key in their inventory
        inventory_url = f"{INVENTORY_SERVICE_URL}/inventory/player/{player_id}"
        logger.debug(f"Requesting inventory from: {inventory_url}")
        
        has_key = False
        
        try:
            # Check if the player has the key in their inventory
            inventory_response = requests.get(inventory_url)
            
            if inventory_response.status_code == 200:
                inventory_data = inventory_response.json()
                logger.debug(f"Inventory data received: {inventory_data}")
                
                # The atomic inventory service returns {"player_id": X, "inventory": [1,2,3]}
                item_ids = inventory_data.get("inventory", [])
                logger.debug(f"Player's inventory item IDs: {item_ids}")
                
                # Check if item ID 5 (the lockpick) is in the inventory
                has_key = 5 in item_ids
                
                logger.debug(f"Player has key in inventory: {has_key}")
            
            # If player doesn't have the key in inventory, check if they've picked it up before
            # by looking at the player_room_interaction service
            if not has_key:
                # We need to check all previous rooms to see if the player picked up the key
                # Get player interactions across all rooms
                all_interactions_url = f"{PLAYER_ROOM_INTERACTION_SERVICE_URL}/player/{player_id}/interactions"
                interactions_response = requests.get(all_interactions_url)
                
                if interactions_response.status_code == 200:
                    interactions_data = interactions_response.json()
                    logger.debug(f"All player interactions: {interactions_data}")
                    
                    # Loop through all room interactions
                    for interaction in interactions_data.get('interactions', []):
                        # Check if item 5 was picked up in any room
                        if 5 in interaction.get('items_picked', []):
                            has_key = True
                            logger.debug(f"Player has previously picked up the key in room {interaction.get('room_id')}")
                            break
                else:
                    logger.error(f"Failed to check player's interaction history: {interactions_response.text}")
            
            if not has_key:
                logger.debug("Player does not have the required key")
                return jsonify({
                    "error": "This door is locked! You need a Lockpick to proceed.",
                    "door_locked": True
                }), 403
                
        except Exception as e:
            logger.error(f"Exception when checking for key: {str(e)}")
            return jsonify({
                "error": "This door is locked! You need a Lockpick to proceed.",
                "door_locked": True,
                "details": f"Error checking for key: {str(e)}"
            }), 403

    # ✅ Update player's location
    logger.debug(f"Setting player {player_id} location to room {room_id}")
    update_response = requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}",
                 json={"room_id": room_id})
    if update_response.status_code != 200:
        logger.error(f"Failed to update player location: {update_response.text}")
    else:
        logger.debug(f"Successfully updated player location to room {room_id}")

    # ✅ Log room entry via RabbitMQ
    room_name = room.get('name') or room.get('Name') or f"Room {room_id}"
    log_activity(player_id, f"Entered Room {room_id}: {room_name}")


    # ✅ Fetch items in the room - Handle all possible data structures
    items = []

    # Check different possible property names and formats for item IDs
    item_ids = []
    if 'item_ids' in room and isinstance(room['item_ids'], list):
        item_ids = room['item_ids']
    elif 'ItemIDs' in room and isinstance(room['ItemIDs'], list):
        item_ids = room['ItemIDs']
    elif 'items' in room and isinstance(room['items'], list):
        # If the room has a direct items list
        for item in room['items']:
            if isinstance(item, dict):
                items.append({
                    "id": item.get("id") or item.get("ItemID", ""),
                    "name": item.get("name") or item.get("Name", "Item"),
                    "description": item.get("description") or item.get("Description", "No description")
                })
            elif isinstance(item, int):
                item_ids.append(item)

    # If we have item IDs to look up
    logger.debug(f"Found item IDs: {item_ids}")
    for item_id in item_ids:
        try:
            item_url = f"{ITEM_SERVICE_URL}/item/{item_id}"
            logger.debug(f"Fetching item from: {item_url}")
            item_response = requests.get(item_url)

            if item_response.status_code == 200:
                item = item_response.json()
                logger.debug(f"Item data received: {item}")

                # More flexible property extraction
                item_data = {
                    "id": item_id,
                    "name": "Item",
                    "description": "No description available"
                }

                # Try multiple possible property names
                for name_key in ["Name", "name"]:
                    if name_key in item and item[name_key]:
                        item_data["name"] = item[name_key]
                        break

                for desc_key in ["Description", "description"]:
                    if desc_key in item and item[desc_key]:
                        item_data["description"] = item[desc_key]
                        break

                for id_key in ["ItemID", "item_id", "id"]:
                    if id_key in item and item[id_key]:
                        item_data["id"] = item[id_key]
                        break

                items.append(item_data)
            else:
                logger.warning(
                    f"Failed to get item {item_id}: {item_response.status_code} - {item_response.text}")
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {str(e)}")

    # ✅ Fetch enemies in the room - Handle all possible data structures
    enemies = []

    # Check different possible property names and formats for enemy IDs
    enemy_ids = []
    if 'enemy_ids' in room and isinstance(room['enemy_ids'], list):
        enemy_ids = room['enemy_ids']
    elif 'EnemyIDs' in room and isinstance(room['EnemyIDs'], list):
        enemy_ids = room['EnemyIDs']
    elif 'enemies' in room and isinstance(room['enemies'], list):
        # If the room has a direct enemies list
        for enemy in room['enemies']:
            if isinstance(enemy, dict):
                enemies.append({
                    "id": enemy.get("id") or enemy.get("EnemyID", ""),
                    "name": enemy.get("name") or enemy.get("Name", "Enemy"),
                    "description": enemy.get("description") or enemy.get("Description", "No description")
                })
            elif isinstance(enemy, int):
                enemy_ids.append(enemy)

    # If we have enemy IDs to look up
    logger.debug(f"Found enemy IDs: {enemy_ids}")
    for enemy_id in enemy_ids:
        try:
            enemy_url = f"{ENEMY_SERVICE_URL}/enemy/{enemy_id}"
            logger.debug(f"Fetching enemy from: {enemy_url}")
            enemy_response = requests.get(enemy_url)

            if enemy_response.status_code == 200:
                enemy = enemy_response.json()
                logger.debug(f"Enemy data received: {enemy}")

                # More flexible property extraction
                enemy_data = {
                    "id": enemy_id,
                    "name": "Enemy",
                    "description": "No description available"
                }

                # Try multiple possible property names
                for name_key in ["Name", "name"]:
                    if name_key in enemy and enemy[name_key]:
                        enemy_data["name"] = enemy[name_key]
                        break

                for desc_key in ["Description", "description"]:
                    if desc_key in enemy and enemy[desc_key]:
                        enemy_data["description"] = enemy[desc_key]
                        break

                for id_key in ["EnemyID", "enemy_id", "id"]:
                    if id_key in enemy and enemy[id_key]:
                        enemy_data["id"] = enemy[id_key]
                        break

                enemies.append(enemy_data)
            else:
                logger.warning(
                    f"Failed to get enemy {enemy_id}: {enemy_response.status_code} - {enemy_response.text}")
        except Exception as e:
            logger.error(f"Error getting enemy {enemy_id}: {str(e)}")

    # ✅ Filter out items and enemies based on player interactions
    try:
        # Get player's interactions with this specific room
        interaction_url = f"{PLAYER_ROOM_INTERACTION_SERVICE_URL}/player/{player_id}/room/{room_id}/interactions"
        logger.debug(f"Checking player room interactions: {interaction_url}")
        
        interaction_response = requests.get(interaction_url)
        if interaction_response.status_code == 200:
            interaction_data = interaction_response.json()
            logger.debug(f"Player room interactions: {interaction_data}")
            
            # Get lists of picked up items and defeated enemies
            picked_items = interaction_data.get('items_picked', [])
            defeated_enemies = interaction_data.get('enemies_defeated', [])
            
            logger.debug(f"Player has picked up items: {picked_items}")
            logger.debug(f"Player has defeated enemies: {defeated_enemies}")
            
            # Filter out items that have already been picked up
            filtered_items = [item for item in items if item['id'] not in picked_items]
            
            # Filter out enemies that have already been defeated
            filtered_enemies = [enemy for enemy in enemies if enemy['id'] not in defeated_enemies]
            
            # Update our lists
            items = filtered_items
            enemies = filtered_enemies
            
            logger.debug(f"After filtering - Remaining items: {[item['id'] for item in items]}")
            logger.debug(f"After filtering - Remaining enemies: {[enemy['id'] for enemy in enemies]}")
    except Exception as e:
        logger.error(f"Error filtering items/enemies based on player interactions: {str(e)}")
        # Continue with unfiltered lists if there's an error


    # ✅ Return comprehensive room information
    response_data = {
        "room_name": room_name,
        "description": room.get("description") or room.get("Description") or "No description available",
        "player_current_room": room_id,
        "items": items,
        "enemies": enemies
    }

    logger.debug(f"Returning room data: {response_data}")
    return jsonify(response_data)


@app.route('/next_room', methods=['POST'])
def enter_next_room():
    """
    Gets the player's current room ID, increments it, and processes entry to the next room.
    """
    data = request.get_json()
    player_id = data.get("player_id")

    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400
        
    logger.debug(f"POST /next_room - Handling room progression for player ID: {player_id}")
    
    # Get player's current room
    try:
        player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
        if player_response.status_code != 200:
            logger.error(f"Failed to get player data: {player_response.text}")
            return jsonify({"error": "Could not retrieve player data"}), player_response.status_code

        player_data = player_response.json()
        logger.debug(f"Player data received: {player_data}")

        # Check if RoomID exists in player_data, if not try lowercase version
        current_room_id = None
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
        
        # Reuse the existing enter_room function to process entry to the next room
        # We're creating a request context that will be passed to the enter_room function
        with app.test_request_context(
            f'/room/{next_room_id}', 
            method='POST',
            json={"player_id": player_id}
        ):
            # Call the enter_room function directly instead of making an internal HTTP request
            return enter_room(next_room_id)
            
    except Exception as e:
        logger.error(f"Error processing next room request: {str(e)}")
        return jsonify({"error": f"Failed to process room progression: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5011, debug=True)
