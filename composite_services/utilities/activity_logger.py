# composite_services/utilities/activity_logger.py
import requests
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Activity Log Service URL
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")

def log_activity(player_id, action):
    """
    Logs player activity by making a REST API call to the activity_log_service.
    
    Args:
        player_id (int): ID of the player performing the action
        action (str): Description of the action performed
        
    Returns:
        bool: True if logging was successful, False otherwise
    """
    if not player_id or not action:
        logger.error("Missing required parameters: player_id and action must be provided")
        return False
        
    url = f"{ACTIVITY_LOG_SERVICE_URL}/api/log"
    data = {
        "player_id": player_id,
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(url, json=data, timeout=5)
        
        if response.status_code == 201:
            logger.debug(f"Activity logged successfully: Player {player_id} - {action}")
            return True
        else:
            logger.error(f"Failed to log activity: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to activity log service: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error logging activity: {str(e)}")
        return False