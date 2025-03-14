from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime

app = Flask(__name__)

# ✅ Microservice URL
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

@app.route('/calculate_score/<int:player_id>', methods=['GET'])
def calculate_final_score(player_id):
    """
    Fetches all scores from the score microservice and calculates the final score.
    """
    # ✅ Get all scores for the player
    score_response = requests.get(f"{SCORE_SERVICE_URL}/score/{player_id}")
    if score_response.status_code != 200:
        return jsonify({"error": "Could not fetch scores"}), 500

    scores = score_response.json().get("scores", [])
    
    # ✅ Sum up all points
    final_score = sum(score["Points"] for score in scores)

    # ✅ Log score calculation via RabbitMQ
    send_activity_log(player_id, f"Final score calculated: {final_score}")

    return jsonify({
        "player_id": player_id,
        "final_score": final_score
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5016, debug=True)
