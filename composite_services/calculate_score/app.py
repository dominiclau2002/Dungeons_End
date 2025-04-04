from flask import Flask, jsonify, request
import requests
import os
import pika, json
from datetime import datetime
import logging
from composite_services.utilities.activity_logger import log_activity


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ Microservice URL
SCORE_SERVICE_URL = os.getenv("SCORE_SERVICE_URL", "http://score_service:5015")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")

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
    log_activity(player_id, f"Final score calculated: {final_score}")


    return jsonify({
        "player_id": player_id,
        "final_score": final_score
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5016, debug=True)
