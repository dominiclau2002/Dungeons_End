from flask import Flask, jsonify, request
import requests
import os
import pika
import json
from datetime import datetime
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv(
    "PLAYER_SERVICE_URL", "http://player_service:5000")
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
COMBAT_SERVICE_URL = os.getenv(
    "COMBAT_SERVICE_URL", "http://fight_enemy_service:5009")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
ACTIVITY_LOG_QUEUE = "activity_log_queue"


def send_activity_log(player_id, action):
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


@app.route('/room/<int:room_id>', methods=['POST'])
def enter_room(room_id):
    data = request.get_json()
    player_id = data.get("player_id")

    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # ✅ Fetch room details
    logger.debug(f"Fetching details for room {room_id}")
    room_response = requests.get(f"{ROOM_SERVICE_URL}/room/{room_id}")
    if room_response.status_code != 200:
        logger.error(f"Room not found: {room_response.text}")
        return jsonify({"error": "Room not found"}), 404

    room = room_response.json()
    logger.debug(f"Room data received: {room}")

    # ✅ Update player's location
    requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}",
                 json={"room_id": room_id})

    # ✅ Log room entry via RabbitMQ
    room_name = room.get('name') or room.get('Name') or f"Room {room_id}"
    send_activity_log(player_id, f"Entered Room {room_id}: {room_name}")

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

    # For testing/debugging - create dummy items and enemies if none were found
    if not items and room_id % 2 == 0:  # Add some items to even-numbered rooms
        items.append({
            "id": 999,
            "name": "Magic Potion",
            "description": "A magical potion that restores health"
        })

    if not enemies and room_id % 3 == 0:  # Add some enemies to rooms divisible by 3
        enemies.append({
            "id": 999,
            "name": "Shadow Lurker",
            "description": "A mysterious creature hiding in the shadows"
        })

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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5011, debug=True)
