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

@app.route('/apply_item_effect', methods=['POST'])
def apply_item_effect():
    """
    Apply special effects for items when picked up.
    Uses the HasEffect and Effect fields to determine what effect to apply:
    - Effect="attack": Adds 20 to player's attack
    - Effect="health": Adds 50 to player's max health
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
        item_name = item_data.get("name", f"Item {item_id}")
            
        # Check if the item has effects to apply
        has_effect = item_data.get("has_effect", False)
        effect_type = item_data.get("effect")
        
        if not has_effect or not effect_type:
            return jsonify({
                "message": f"No special effect for item {item_id}",
                "item_id": item_id,
                "item_name": item_name,
                "effect_applied": False
            })
            
    except Exception as e:
        logger.error(f"Error fetching item details: {str(e)}")
        return jsonify({"error": f"Error fetching item details: {str(e)}"}), 500
    
    # Get current player stats
    try:
        player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
        if player_response.status_code != 200:
            return jsonify({"error": "Player not found"}), 404
            
        player_data = player_response.json()
        
    except Exception as e:
        logger.error(f"Error fetching player data: {str(e)}")
        return jsonify({"error": f"Error fetching player data: {str(e)}"}), 500
    
    # Apply effect based on effect_type
    effect_applied = False
    effect_description = ""
    effect_data = {}
    update_data = {}
    
    try:
        # Apply attack effect
        if effect_type == "attack":
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
            
            effect_applied = True
            effect_description = f"Increased attack by 20"
            effect_data = {
                "attack_increased": True,
                "new_attack": new_damage
            }
            
        # Apply health effect
        elif effect_type == "health":
            # Check for different possible health attribute names
            current_health = None
            max_health = None
            health_key = None
            
            for key in ["health", "Health", "current_health", "CurrentHealth"]:
                if key in player_data:
                    current_health = player_data[key]
                    health_key = key
                    break
                    
            for key in ["max_health", "MaxHealth"]:
                if key in player_data:
                    max_health = player_data[key]
                    break
            
            if current_health is None or health_key is None:
                return jsonify({"error": "Could not find current health attribute in player data"}), 500
                
            # Don't increase max health, only increase current health
            # Ensure current health doesn't exceed max health if known
            new_current_health = current_health + 50
            if max_health is not None and new_current_health > max_health:
                new_current_health = max_health
                
            update_data = {health_key: new_current_health}
            
            logger.debug(f"Updating player's {health_key} from {current_health} to {new_current_health}")
            
            effect_applied = True
            effect_description = f"Increased current health by 50"
            effect_data = {
                "health_increased": True,
                "new_current_health": new_current_health
            }
        
        # Update player stats in database
        if update_data:
            update_response = requests.put(
                f"{PLAYER_SERVICE_URL}/player/{player_id}", 
                json=update_data
            )
            
            if update_response.status_code != 200:
                return jsonify({"error": f"Failed to update player stats: {update_response.text}"}), 500
                
            # Log the activity
            log_activity(player_id, f"{effect_description} from {item_name}")
            
    except Exception as e:
        logger.error(f"Error applying item effect: {str(e)}")
        return jsonify({"error": f"Error applying item effect: {str(e)}"}), 500
    
    # No specific effect handler for this item
    if not effect_applied:
        return jsonify({
            "message": f"No specific effect handler for effect type: {effect_type}",
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