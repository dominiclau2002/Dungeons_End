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
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory_service:5001")
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

@app.route('/inventory/<int:player_id>', methods=['GET'])
def view_inventory(player_id):
    """
    Retrieves the player's inventory with item descriptions.
    """

    # ✅ Step 1: Fetch inventory
    inventory_response = requests.get(f"{INVENTORY_SERVICE_URL}/inventory/player/{player_id}")
    if inventory_response.status_code != 200:
        return jsonify({"error": "Inventory could not be retrieved."}), 500

    inventory_data = inventory_response.json()
    item_ids = inventory_data.get("inventory", [])

    # ✅ Step 2: Fetch item details and enhance inventory items
    enhanced_inventory = []
    for item_id in item_ids:
        item_response = requests.get(f"{ITEM_SERVICE_URL}/item/{item_id}")
        
        if item_response.status_code == 200:
            item_info = item_response.json()
            # Create enhanced item with name and description
            # The item service might be using capitalized field names
            enhanced_item = {
                "item_id": item_id,
                "name": item_info.get("Name", item_info.get("name", "Unknown Item")),
                "description": item_info.get("Description", item_info.get("description", "No description available"))
            }
            enhanced_inventory.append(enhanced_item)
        else:
            # Still include item ID even if item details can't be fetched
            enhanced_item = {
                "item_id": item_id,
                "name": "Unknown Item",
                "description": "Item details unavailable"
            }
            enhanced_inventory.append(enhanced_item)

    # ✅ Log inventory view via RabbitMQ
    log_activity(player_id, "Viewed inventory")


    return jsonify({
        "player_id": player_id,
        "inventory": enhanced_inventory
    })

@app.route('/items/batch', methods=['POST'])
def fetch_item_details_batch():
    """
    Fetches details for multiple items at once.
    """
    data = request.get_json()
    item_ids = data.get('item_ids', [])

    if not item_ids:
        return jsonify({"error": "Item IDs are required"}), 400

    items = []
    for item_id in item_ids:
        # Call the item service to get item details
        item_response = requests.get(f"{ITEM_SERVICE_URL}/item/{item_id}")
        
        if item_response.status_code == 200:
            items.append(item_response.json())
        else:
            # Include a placeholder for failed items
            items.append({
                "item_id": item_id,
                "name": "Unknown Item",
                "description": "Item details unavailable"
            })

    return jsonify({"items": items})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5010, debug=True)
