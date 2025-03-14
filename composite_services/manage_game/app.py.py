from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime

app = Flask(__name__)

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
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

@app.route('/game/reset/<int:player_id>', methods=['POST'])
def reset_character_progress(player_id):
    """
    Resets the player's game progress.
    """
    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    if player_response.status_code != 200:
        return jsonify({"error": "Player not found"}), 404

    # ✅ Reset player progress
    requests.put(f"{PLAYER_SERVICE_URL}/player/{player_id}", json={"health": 100, "room_id": 1})

    # ✅ Reset all enemies
    requests.get(f"{ENEMY_SERVICE_URL}/reset")

    # ✅ Log reset via RabbitMQ
    send_activity_log(player_id, "Game progress reset")

    return jsonify({"message": f"Progress reset for player {player_id}."})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5014, debug=True)
