from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# ✅ Get environment variables for services
ROOM_SERVICE_URL = os.getenv("ROOM_SERVICE_URL", "http://room_service:5012")
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player_service:5000")
ENEMY_SERVICE_URL = os.getenv("ENEMY_SERVICE_URL", "http://enemy_service:5005")
ITEM_SERVICE_URL = os.getenv("ITEM_SERVICE_URL", "http://item_service:5002")
ACTIVITY_LOG_SERVICE_URL = os.getenv("ACTIVITY_LOG_SERVICE_URL", "http://activity_log_service:5013")

@app.route('/room/<int:room_id>', methods=['GET'])
def enter_room(room_id):
    """
    Retrieves room details and updates the player's location.
    Calls enemy and item services to check for room contents.
    """

    # ✅ Step 1: Fetch room details
    room_response = requests.get(f"{ROOM_SERVICE_URL}/room/{room_id}")
    if room_response.status_code != 200:
        return jsonify({"error": f"Room with ID {room_id} not found."}), 404

    room = room_response.json()

    # ✅ Step 2: Get the player's current location
    player_response = requests.get(f"{PLAYER_SERVICE_URL}/player/{request.args.get('player_id')}")
    if player_response.status_code != 200:
        return jsonify({"error": "Player not found!"}), 404

    player = player_response.json()

    # ✅ Step 3: Update player's current room
    update_player = requests.put(f"{PLAYER_SERVICE_URL}/player/{player['PlayerID']}", json={"room_id": room_id})
    
    # ✅ Step 4: Fetch enemy details (if there’s an enemy in the room)
    enemy_details = None
    if "EnemyID" in room and room["EnemyID"]:
        enemy_response = requests.get(f"{ENEMY_SERVICE_URL}/enemy/{room['EnemyID']}")
        if enemy_response.status_code == 200:
            enemy_details = enemy_response.json()

    # ✅ Step 5: Fetch item details (if an item exists in the room)
    item_details = None
    if "ItemID" in room and room["ItemID"]:
        item_response = requests.get(f"{ITEM_SERVICE_URL}/item/{room['ItemID']}")
        if item_response.status_code == 200:
            item_details = item_response.json()

    # ✅ Step 6: Update activity log (NOT IMPLEMENTED YET)
    activity_log_data = {
        "player_id": player["PlayerID"],
        "action": f"Entered Room {room_id}",
        "room_id": room_id
    }
    requests.post(f"{ACTIVITY_LOG_SERVICE_URL}/log", json=activity_log_data)

    # ✅ Step 7: Construct response
    response = {
        "room_name": room["Name"],
        "description": room["Description"],
        "player_current_room": room_id
    }

    if enemy_details:
        response["enemy"] = {
            "name": enemy_details["Name"],
            "health": enemy_details["Health"],
            "attacks": enemy_details["Attacks"]
        }

    if item_details:
        response["item"] = {
            "name": item_details["Name"],
            "description": item_details["Description"]
        }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5011, debug=True)
