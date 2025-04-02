from flask import Flask, render_template, request, jsonify
import requests
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ Microservice URLs
PLAYER_SERVICE_URL = os.getenv(
    "PLAYER_SERVICE_URL", "http://player_service:5000")
ENTERING_ROOM_SERVICE_URL = os.getenv(
    "ENTERING_ROOM_SERVICE_URL", "http://entering_room_service:5011")


@app.route("/")
def home():
    """Renders the game UI."""
    return render_template("index.html")


@app.route("/get_player_room", methods=["GET"])
def get_player_room():
    """Gets the player's current room ID, assuming player ID is always 1."""
    player_id = 1  # Hardcoded player ID as requested

    # Get player data from player service
    response = requests.get(f"{PLAYER_SERVICE_URL}/player/{player_id}")
    if response.status_code != 200:
        return jsonify({"error": "Could not retrieve player data"}), response.status_code

    player_data = response.json()
    room_id = player_data.get("RoomID", 0)
    logger.debug(f"GET /get_player_room - Current player room ID: {room_id}")
    return jsonify({"room_id": room_id})


@app.route("/enter_room", methods=["POST"])
def enter_room():
    """Handles room navigation. Auto-increments room ID from player's current room."""
    player_id = 1  # Hardcoded player ID
    data = request.get_json()
    target_room_id = data.get('target_room_id', None)

    logger.debug(
        f"POST /enter_room - Starting to process for player ID: {player_id}")

    # If target_room_id is provided, use it (for reset functionality)
    if target_room_id is not None:
        next_room_id = target_room_id
        logger.debug(f"Using provided target room ID: {next_room_id}")
    else:
        # Otherwise, get player's current room and increment it
        player_response = requests.get(
            f"{PLAYER_SERVICE_URL}/player/{player_id}")
        if player_response.status_code != 200:
            logger.error(f"Failed to get player data: {player_response.text}")
            return jsonify({"error": "Could not retrieve player data"}), player_response.status_code

        player_data = player_response.json()
        logger.debug(f"Player data received: {player_data}")

        # Check if RoomID exists in player_data, if not try lowercase version
        if "RoomID" in player_data:
            current_room_id = player_data.get("RoomID", 0)
        elif "room_id" in player_data:
            current_room_id = player_data.get("room_id", 0)
        else:
            logger.warning("RoomID not found in player data, defaulting to 0")
            current_room_id = 0

        # Increment room ID by 1 for the next room
        next_room_id = current_room_id + 1
        logger.debug(
            f"Current room ID: {current_room_id}, Next room ID: {next_room_id}")

    # Call entering room service with the room ID
    room_data = {"player_id": player_id}
    room_url = f"{ENTERING_ROOM_SERVICE_URL}/room/{next_room_id}"
    logger.debug(
        f"Calling entering room service: {room_url} with data: {room_data}")

    response = requests.post(room_url, json=room_data)
    logger.debug(
        f"Room service response: {response.status_code} - {response.text}")

    # Check if we've reached the end of available rooms
    if response.status_code != 200:
        logger.warning(f"Failed to enter room {next_room_id}: {response.text}")
        return jsonify({
            "end_of_game": True,
            "message": "You've reached the end of the game!"
        })

    # Room was found and entered successfully
    return jsonify({
        "end_of_game": False,
        **response.json()
    })


@app.route("/reset_game", methods=["POST"])
def reset_game():
    """Resets the game by sending the player back to room 0."""
    player_id = 1

    # Call enter_room with target_room_id = 0
    return enter_room()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
