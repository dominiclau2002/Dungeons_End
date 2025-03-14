from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Microservice URLs
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory_service:5001")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
SCORE_SERVICE_URL = os.getenv("SCORE_SERVICE_URL", "http://score_service:5015")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")

@app.route('/inventory/<int:player_id>', methods=['GET'])
def view_inventory(player_id):
    """
    Retrieves the player's inventory with item descriptions.
    """
    inventory_response = requests.get(f"{INVENTORY_SERVICE_URL}/inventory/{player_id}")
    if inventory_response.status_code != 200:
        return jsonify({"error": "Inventory could not be retrieved."}), 500

    inventory_data = inventory_response.json().get("inventory", [])
    inventory_with_details = []

    for item in inventory_data:
        item_response = requests.get(f"{ITEM_SERVICE_URL}/item/{item['ItemID']}")
        if item_response.status_code == 200:
            item_info = item_response.json()
            inventory_with_details.append(item_info)

    return jsonify({"inventory": inventory_with_details})

@app.route('/inventory/pickup', methods=['POST'])
def pickup_item():
    """
    Adds an item to the player's inventory and awards score.
    """
    player_id = request.json.get("player_id")
    item_id = request.json.get("item_id")

    if not player_id or not item_id:
        return jsonify({"error": "PlayerID and ItemID are required"}), 400

    # ✅ Add item to inventory
    add_response = requests.post(f"{INVENTORY_SERVICE_URL}/inventory", json={"player_id": player_id, "item_id": item_id})

    # ✅ If successful, add score
    if add_response.status_code == 201:
        score_data = {
            "player_id": player_id,
            "points": 10,  # Example points for picking up an item
            "reason": "item_collection"
        }
        requests.post(f"{SCORE_SERVICE_URL}/score/add", json=score_data)

    return jsonify(add_response.json())

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
