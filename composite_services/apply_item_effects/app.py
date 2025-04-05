from flask import Flask, jsonify, request
import requests
import os
import pika
import json
import logging
from datetime import datetime
from composite_services.utilities.activity_logger import log_activity


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Microservice URLs
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
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

@app.route('/apply_item_effect', methods=['POST'])
def apply_item_effect():
    """
    Apply special effects for items when picked up.
    Currently handles:
    - Item ID 1 (Golden Sword): Increases player attack by 20
    - Future special items can be added here
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    player_id = data.get("player_id")
    item_id = data.get("item_id")
    
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400
        
    if not item_id:
        return jsonify({"error": "item_id is required"}), 400
        
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return jsonify({"error": "item_id must be an integer"}), 400
    
    # Get item details first
    try:
        item_response = requests.get(f"{ITEM_SERVICE_URL}/item/{item_id}")
        if item_response.status_code != 200:
            return jsonify({"error": f"Item not found: {item_id}"}), 404
            
        item_data = item_response.json()
        # Check different possible property names for the item name
        item_name = None
        for key in ["Name", "name"]:
            if key in item_data:
                item_name = item_data[key]
                break
        if not item_name:
            item_name = f"Item {item_id}"
    except Exception as e:
        logger.error(f"Error fetching item details: {str(e)}")
        return jsonify({"error": f"Error fetching item details: {str(e)}"}), 500
    
    # Apply item-specific effects
    effect_applied = False
    effect_description = ""
    effect_data = {}
    
    # Item ID 1: Golden Sword - increases attack by 20
    if item_id == 1:
        logger.debug(f"Applying Golden Sword effect for player {player_id}")
        
        try:
            # Get current player stats
            player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
            if player_response.status_code != 200:
                return jsonify({"error": "Player not found"}), 404
                
            player_data = player_response.json()
            
            # Check for different possible damage/attack attribute names
            current_damage = None
            damage_key = None
            for key in ["damage", "Damage", "attack", "Attack"]:
                if key in player_data:
                    current_damage = player_data[key]
                    damage_key = key
                    break
            
            if current_damage is None:
                return jsonify({"error": "Could not find damage/attack attribute in player data"}), 500
                
            # Update player's damage/attack value
            new_damage = current_damage + 20
            update_data = {damage_key: new_damage}
            
            logger.debug(f"Updating player's {damage_key} from {current_damage} to {new_damage}")
            
            # Update player stats in database
            update_response = requests.put(
                f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                json=update_data
            )
            
            if update_response.status_code != 200:
                return jsonify({"error": f"Failed to update player stats: {update_response.text}"}), 500
                
            # Log the activity
            log_activity(player_id, f"Gained +20 attack from the {item_name}")
            
            effect_applied = True
            effect_description = f"Increased attack by 20"
            effect_data = {
                "attack_increased": True,
                "new_attack": new_damage
            }
            
        except Exception as e:
            logger.error(f"Error applying Golden Sword effect: {str(e)}")
            return jsonify({"error": f"Error applying item effect: {str(e)}"}), 500
    
    # No effect for this item
    if not effect_applied:
        return jsonify({
            "message": f"No special effect for item {item_id}",
            "item_id": item_id,
            "item_name": item_name,
            "effect_applied": False
        })
    
    # Return effect information
    return jsonify({
        "message": f"Successfully applied {item_name} effect: {effect_description}",
        "item_id": item_id,
        "item_name": item_name,
        "effect_applied": True,
        "effect_description": effect_description,
        **effect_data
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5025, debug=True) 