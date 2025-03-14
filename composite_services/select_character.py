from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime

app = Flask(__name__)

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
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

@app.route('/select_character', methods=['POST'])
def select_character():
    """
    Selects a character and initializes the player.
    """
    data = request.get_json()
    player_id = data.get("player_id")
    character_name = data.get("character_name")

    if not player_id or not character_name:
        return jsonify({"error": "PlayerID and character name are required"}), 400

    # ✅ Fetch character stats from the player service
    char_response = requests.get(f"{PLAYER_SERVICE_URL}/character/{character_name}")
    if char_response.status_code != 200:
        return jsonify({"error": "Character not found"}), 404

    character = char_response.json()

    # ✅ Initialize the player with character stats
    init_response = requests.post(
        f"{PLAYER_SERVICE_URL}/initialize_player",
        json={"player_id": player_id, "character": character}
    )

    if init_response.status_code != 201:
        return jsonify({"error": "Failed to initialize player"}), 500

    # ✅ Log character selection via RabbitMQ
    send_activity_log(player_id, f"Selected character {character_name}")

    return jsonify({"message": "Character selected successfully!", "character": character})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5017, debug=True)
