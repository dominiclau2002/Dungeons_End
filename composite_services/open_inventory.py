from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Microservice URLs
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory_service:5001")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")

@app.route('/inventory/<int:player_id>', methods=['GET'])
def view_inventory(player_id):
    """
    Retrieves the player's inventory with item descriptions.
    """

    # ✅ Step 1: Fetch inventory
    inventory_response = requests.get(f"{INVENTORY_SERVICE_URL}/inventory/{player_id}")
    if inventory_response.status_code != 200:
        return jsonify({"error": "Inventory could not be retrieved."}), 500

    inventory_data = inventory_response.json().get("inventory", [])

    # ✅ Step 2: Fetch item details
    inventory_with_details = []
    for item in inventory_data:
        item_response = requests.get(f"{ITEM_SERVICE_URL}/item/{item['ItemID']}")
        if item_response.status_code == 200:
            item_info = item_response.json()
            inventory_with_details.append(item_info)

    return jsonify({"inventory": inventory_with_details})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5010, debug=True)
