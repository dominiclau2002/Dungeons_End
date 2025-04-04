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

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
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
    log_activity(player_id, f"Selected character {character_name}")


    return jsonify({"message": "Character selected successfully!", "character": character})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5017, debug=True)
