import mysql.connector
from flask import Flask, jsonify, request
from atomic_services.player import Player
from atomic_services.enemy import Enemy
from atomic_services.item import Item

app = Flask(__name__)

# Function to connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",  # Change if using a remote database
        user="root",       # Your MySQL username
        password="password123",  # Your MySQL password
        database="game_database"
    )
# Simulated player instance (Replace with a real player management system)
player = Player(name="Hero")

@app.route('/room/<room_name>', methods=['GET'])
def enter_room(room_name):
    """
    Retrieves room details and updates the player's location.
    Calls enemy and item services to check for room contents.
    """
    # Fetch room details from MySQL
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms WHERE name = %s", (room_name,))
    room = cursor.fetchone()
    cursor.close()
    conn.close()

    if not room:
        return jsonify({"error": f"Room '{room_name}' not found."}), 404

    # Update player's current room
    player.current_room = room["name"]

    # Fetch enemy details if present
    enemy_details = None
    if room["enemy_id"]:
        enemy_details = Enemy.load_enemy_by_id(room["enemy_id"])  # Fetch enemy by ID

    # Fetch item details if present
    item_details = None
    if room["item_id"]:
        item_details = Item.load_item_by_id(room["item_id"])  # Fetch item by ID

    # Construct response
    response = {
        "room_name": room["name"],
        "description": room["description"],
        "player_current_room": player.current_room
    }

    if enemy_details:
        response["enemy"] = {
            "name": enemy_details.name,
            "health": enemy_details.health,
            "attacks": enemy_details.attacks
        }

    if item_details:
        response["item"] = {
            "name": item_details.name,
            "type": item_details.item_type
        }

    return jsonify(response)

if __name__ == '__main__':
    app.run(port=5011, debug=True)
