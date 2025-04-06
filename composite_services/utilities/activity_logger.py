# composite_services/utilities/activity_logger.py
import pika
import logging
import os
from datetime import datetime
import json
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
ACTIVITY_LOG_QUEUE = "activity_log_queue"

def log_activity(player_id, action):
    """
    Logs player activity by calling the activity log service API.
    """
    if not player_id or not action:
        logger.error("Missing required parameters: player_id and action must be provided")
        return False
        
    try:
        response = requests.post(
            f"{ACTIVITY_LOG_SERVICE_URL}/api/log",
            json={
                "player_id": player_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            },
            timeout=5
        )
        
        if response.status_code == 201:
            logger.debug(f"Activity logged successfully: Player {player_id} - {action}")
            return True
        else:
            logger.error(f"Failed to log activity: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")
        return False