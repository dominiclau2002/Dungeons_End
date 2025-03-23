from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime

app = Flask(__name__)

# Microservice URLs
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory_service:5001")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
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

@app.route('/pick_up_item', methods=['POST'])
def pick_up_item():
    """
    Picks up an item from a room and adds it to the player's inventory.
    """
    data = request.get_json()
    player_id = data.get("player_id")
    room_id = data.get("room_id")
    item_id = data.get("item_id")

    if not player_id or not room_id or not item_id:
        return jsonify({"error": "PlayerID, RoomID, and ItemID are required"}), 400

    # Step 1: Check if the item exists in the room
    room_response = requests.get(f"{ROOM_SERVICE_URL}/rooms/{room_id}")
    if room_response.status_code != 200:
        return jsonify({"error": "Room not found"}), 404
    
    room_data = room_response.json().get("room", {})
    if not room_data or item_id not in (room_data.get("ItemIDs") or []):
        return jsonify({"error": "Item not found in the room"}), 404

    # Step 2: Get item details to include in the activity log
    item_response = requests.get(f"{ITEM_SERVICE_URL}/item/{item_id}")
    if item_response.status_code != 200:
        return jsonify({"error": "Failed to get item details"}), 500
    
    item_name = item_response.json().get("name", "Unknown Item")

    # Step 3: Remove the item from the room
    remove_response = requests.delete(f"{ROOM_SERVICE_URL}/rooms/{room_id}/items/{item_id}")
    if remove_response.status_code != 200:
        return jsonify({"error": "Failed to remove item from room"}), 500

    # Step 4: Add the item to the player's inventory
    inventory_response = requests.post(
        f"{INVENTORY_SERVICE_URL}/inventory",
        json={"player_id": player_id, "item_id": item_id}
    )
    if inventory_response.status_code != 201:
        # If adding to inventory fails, try to put the item back in the room
        requests.post(
            f"{ROOM_SERVICE_URL}/rooms/{room_id}/items",
            json={"item_id": item_id}
        )
        return jsonify({"error": "Failed to add item to inventory"}), 500

    # Step 5: Log the activity via RabbitMQ
    send_activity_log(player_id, f"Picked up {item_name} (ID: {item_id}) from room {room_id}")

    return jsonify({
        "message": f"Successfully picked up {item_name}",
        "player_id": player_id,
        "item_id": item_id,
        "room_id": room_id
    }), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5019, debug=True)
