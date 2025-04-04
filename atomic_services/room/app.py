#atomic_services\room\app.py
import os
from flask import Flask, jsonify, request
from models import db, Room

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+mysqlconnector://user:password@mysql/room_db"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ✅ API to Create a Room
@app.route("/room", methods=["POST"])
def create_room():
    data = request.get_json()
    
    if not data or 'description' not in data:
        return jsonify({
            "error": "Description is required"
        }), 400

    new_room = Room(
        Description=data['description'],
        ItemIDs=data.get('item_ids', []),
        EnemyIDs=data.get('enemy_ids', []),
        DoorLocked=data.get('door_locked', False)
    )
    
    db.session.add(new_room)
    db.session.commit()

    return jsonify({
        "message": "Room created successfully",
        "room": new_room.to_dict()
    }), 201

# ✅ API to Get a Room
@app.route("/room/<int:room_id>", methods=["GET"])
def get_room(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({
            "error": "Room not found"
        }), 404

    return jsonify(room.to_dict()), 200

# ✅ API to Get All Rooms
@app.route("/rooms", methods=["GET"])
def get_all_rooms():
    rooms = Room.query.all()
    return jsonify({
        "rooms": [room.to_dict() for room in rooms]
    }), 200

# ✅ API to Update Room
@app.route("/room/<int:room_id>", methods=["PUT"])
def update_room(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({
            "error": "Room not found"
        }), 404

    data = request.get_json()
    
    if "description" in data:
        room.Description = data['description']
    if "item_ids" in data:
        room.ItemIDs = data['item_ids']
    if "enemy_ids" in data:
        room.EnemyIDs = data['enemy_ids']
    if "door_locked" in data:
        room.DoorLocked = data['door_locked']

    db.session.commit()

    return jsonify({
        "message": "Room updated successfully",
        "room": room.to_dict()
    }), 200

# ✅ API to Delete Room
@app.route("/room/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({
            "error": "Room not found"
        }), 404

    db.session.delete(room)
    db.session.commit()

    return jsonify({
        "message": "Room deleted successfully",
        "deleted_room": room.to_dict()
    }), 200

# ✅ API to Add Item to Room
@app.route("/room/<int:room_id>/item/<int:item_id>", methods=["POST"])
def add_item_to_room(room_id, item_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({
            "error": "Room not found"
        }), 404

    current_items = room.ItemIDs or []
    if item_id in current_items:
        return jsonify({
            "error": "Item already in room"
        }), 409

    current_items.append(item_id)
    room.ItemIDs = current_items
    db.session.commit()

    return jsonify({
        "message": "Item added to room",
        "room": room.to_dict()
    }), 200

# ✅ API to Remove Item from Room
@app.route("/room/<int:room_id>/item/<int:item_id>", methods=["DELETE"])
def remove_item_from_room(room_id, item_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({
            "error": "Room not found"
        }), 404

    # Make sure we're working with a list, not None
    current_items = room.ItemIDs or []
    # Convert string item_id to int for comparison if needed
    try:
        item_id_int = int(item_id)
    except (ValueError, TypeError):
        item_id_int = item_id

    # Check if the item exists in the room using both the original and int versions
    if item_id not in current_items and item_id_int not in current_items:
        return jsonify({
            "error": "Item not found in room"
        }), 404

    # Remove the item, handling potential type differences
    if item_id in current_items:
        current_items.remove(item_id)
    elif item_id_int in current_items:
        current_items.remove(item_id_int)

    # Ensure we're storing a valid JSON array, not None
    room.ItemIDs = current_items if current_items else []
    db.session.commit()

    # Verify the item was actually removed by fetching the updated room
    updated_room = Room.query.get(room_id)
    if updated_room and ((item_id in (updated_room.ItemIDs or [])) or 
                        (item_id_int in (updated_room.ItemIDs or []))):
        # Item still exists, try updating directly with a new list
        filtered_items = [i for i in (updated_room.ItemIDs or []) 
                        if i != item_id and i != item_id_int]
        updated_room.ItemIDs = filtered_items
        db.session.commit()

    return jsonify({
        "message": "Item removed from room",
        "room": room.to_dict()
    }), 200

# ✅ API to Add Enemy to Room
@app.route("/room/<int:room_id>/enemy/<int:enemy_id>", methods=["POST"])
def add_enemy_to_room(room_id, enemy_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({
            "error": "Room not found"
        }), 404

    current_enemies = room.EnemyIDs or []
    if enemy_id in current_enemies:
        return jsonify({
            "error": "Enemy already in room"
        }), 409

    current_enemies.append(enemy_id)
    room.EnemyIDs = current_enemies
    db.session.commit()

    return jsonify({
        "message": "Enemy added to room",
        "room": room.to_dict()
    }), 200

# ✅ API to Remove Enemy from Room
@app.route("/room/<int:room_id>/enemy/<int:enemy_id>", methods=["DELETE"])
def remove_enemy_from_room(room_id, enemy_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({
            "error": "Room not found"
        }), 404

    # Make sure we're working with a list, not None
    current_enemies = room.EnemyIDs or []
    # Convert string enemy_id to int for comparison if needed
    try:
        enemy_id_int = int(enemy_id)
    except (ValueError, TypeError):
        enemy_id_int = enemy_id

    # Check if the enemy exists in the room using both the original and int versions
    if enemy_id not in current_enemies and enemy_id_int not in current_enemies:
        return jsonify({
            "error": "Enemy not found in room"
        }), 404

    # Remove the enemy, handling potential type differences
    if enemy_id in current_enemies:
        current_enemies.remove(enemy_id)
    elif enemy_id_int in current_enemies:
        current_enemies.remove(enemy_id_int)

    # Ensure we're storing a valid JSON array, not None
    room.EnemyIDs = current_enemies if current_enemies else []
    db.session.commit()

    # Verify the enemy was actually removed by fetching the updated room
    updated_room = Room.query.get(room_id)
    if updated_room and ((enemy_id in (updated_room.EnemyIDs or [])) or 
                        (enemy_id_int in (updated_room.EnemyIDs or []))):
        # Enemy still exists, try updating directly with a new list
        filtered_enemies = [e for e in (updated_room.EnemyIDs or []) 
                         if e != enemy_id and e != enemy_id_int]
        updated_room.EnemyIDs = filtered_enemies
        db.session.commit()

    return jsonify({
        "message": "Enemy removed from room",
        "room": room.to_dict()
    }), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5016, debug=True)