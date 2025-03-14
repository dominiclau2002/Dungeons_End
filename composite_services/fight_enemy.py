from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime

app = Flask(__name__)

# ✅ Microservice URLs
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
DICE_SERVICE_URL = os.getenv("DICE_SERVICE_URL", "http://dice_service:5007")
SCORE_SERVICE_URL = os.getenv("SCORE_SERVICE_URL", "http://score_service:5015")
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

@app.route('/combat/start/<int:room_id>', methods=['POST'])
def start_combat(room_id):
    player_id = request.json.get("player_id")
    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400

    # ✅ Fetch enemy details
    enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{room_id}")
    if enemy_response.status_code != 200:
        return jsonify({"message": "No enemy found in this room.", "combat": False})

    enemy = enemy_response.json()

    # ✅ Log combat start via RabbitMQ
    send_activity_log(player_id, f"Engaged in combat with {enemy['Name']} in Room {room_id}")

    return jsonify({
        "message": f"You encountered a {enemy['Name']}!",
        "enemy": {
            "name": enemy["Name"],
            "health": enemy["Health"],
            "attacks": enemy["Attacks"]
        },
        "combat": True
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5008, debug=True)
