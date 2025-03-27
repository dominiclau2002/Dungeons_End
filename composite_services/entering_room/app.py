from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime

app = Flask(__name__)

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
COMBAT_SERVICE_URL = os.getenv("COMBAT_SERVICE_URL", "http://fight_enemy_service:5009")
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5016")
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

@app.route('/room/<int:room_id>', methods=['POST'])
def enter_room(room_id):
    data = request.get_json()
    player_id = data.get("player_id")

    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # ✅ Fetch room details
    room_response = requests.get(f"{ROOM_SERVICE_URL}/room/{room_id}")
    if room_response.status_code != 200:
        return jsonify({"error": "Room not found"}), 404

    room = room_response.json()

    # ✅ Update player's location
    requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}", json={"room_id": room_id})

    # ✅ Log room entry via RabbitMQ
    room_name = room.get('name') or room.get('Name') or f"Room {room_id}"
    send_activity_log(player_id, f"Entered Room {room_id}: {room_name}")

    # ✅ Check for enemy and start combat
    # enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{room_id}")
    # if enemy_response.status_code == 200:
    #     requests.post(f"{COMBAT_SERVICE_URL}/combat/start/{room_id}", json={"player_id": player_id})
    #     return jsonify({"message": "Combat initiated!"})

    return jsonify({
        "room_name": room_name,
        "description": room.get("description") or room.get("Description") or "No description available",
        "player_current_room": room_id
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5011, debug=True)
