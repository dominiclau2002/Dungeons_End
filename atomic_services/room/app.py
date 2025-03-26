#atomic_services\room\app.py
import os
from flask import Flask,jsonify, request
from models import db, RoomModel, init_db

app = Flask(__name__)

# # Initialize the database with the app
# init_db(app, seed=True)

# ✅ API to Get All Rooms
@app.route("/rooms", methods=["GET"])
def get_all_rooms():
    rooms = RoomModel.query.all()
    return jsonify({"rooms": [room.to_dict() for room in rooms]}), 200

# ✅ API to Get a Specific Room
@app.route("/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    return jsonify({"room": room.to_dict()}), 200

# ✅ API to Create a New Room
@app.route("/rooms", methods=["POST"])
def create_room():
    data = request.get_json()
    description = data.get("description")
    name = data.get("name")
    item_ids = data.get("item_ids", [])
    enemy_ids = data.get("enemy_ids", [])
    door_locked = data.get("door_locked", False)
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    if not description:
        return jsonify({"error": "Description is required"}), 400
    
    room = RoomModel(
        Description=description,
        ItemIDs=item_ids,
        EnemyIDs=enemy_ids,
        DoorLocked=door_locked
    )
    
    db.session.add(room)
    db.session.commit()
    
    return jsonify({"message": "Room created", "room": room.to_dict()}), 201

# ✅ API to Update Room Description
@app.route("/rooms/<int:room_id>/description", methods=["PUT"])
def update_room_description(room_id):
    data = request.get_json()
    description = data.get("description")
    
    if not description:
        return jsonify({"error": "Description is required"}), 400
    
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    room.Description = description
    db.session.commit()
    
    return jsonify({"message": "Room description updated", "room": room.to_dict()}), 200

# ✅ API to Update Door Locked Status
@app.route("/rooms/<int:room_id>/door", methods=["PUT"])
def update_door_status(room_id):
    data = request.get_json()
    door_locked = data.get("door_locked")
    
    if door_locked is None:
        return jsonify({"error": "door_locked status is required"}), 400
    
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    room.DoorLocked = door_locked
    db.session.commit()
    
    return jsonify({"message": "Door status updated", "room": room.to_dict()}), 200

# ✅ API to Add an Item to a Room
@app.route("/rooms/<int:room_id>/items", methods=["POST"])
def add_item_to_room(room_id):
    data = request.get_json()
    item_id = data.get("item_id")
    
    if not item_id:
        return jsonify({"error": "item_id is required"}), 400
    
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    # Initialize ItemIDs as empty list if it's None
    if room.ItemIDs is None:
        room.ItemIDs = []
    
    # Check if item already exists in the room
    if item_id in room.ItemIDs:
        return jsonify({"error": "Item already exists in the room"}), 400
    
    room.ItemIDs.append(item_id)
    db.session.commit()
    
    return jsonify({"message": "Item added to room", "room": room.to_dict()}), 200

# ✅ API to Remove an Item from a Room
@app.route("/rooms/<int:room_id>/items/<int:item_id>", methods=["DELETE"])
def remove_item_from_room(room_id, item_id):
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    # Initialize ItemIDs as empty list if it's None
    if room.ItemIDs is None:
        room.ItemIDs = []
    
    if item_id not in room.ItemIDs:
        return jsonify({"error": "Item not found in the room"}), 404
    
    room.ItemIDs.remove(item_id)
    db.session.commit()
    
    return jsonify({"message": "Item removed from room", "room": room.to_dict()}), 200

# ✅ API to Add an Enemy to a Room
@app.route("/rooms/<int:room_id>/enemies", methods=["POST"])
def add_enemy_to_room(room_id):
    data = request.get_json()
    enemy_id = data.get("enemy_id")
    
    if not enemy_id:
        return jsonify({"error": "enemy_id is required"}), 400
    
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    # Initialize EnemyIDs as empty list if it's None
    if room.EnemyIDs is None:
        room.EnemyIDs = []
    
    # Check if enemy already exists in the room
    if enemy_id in room.EnemyIDs:
        return jsonify({"error": "Enemy already exists in the room"}), 400
    
    room.EnemyIDs.append(enemy_id)
    db.session.commit()
    
    return jsonify({"message": "Enemy added to room", "room": room.to_dict()}), 200

# ✅ API to Remove an Enemy from a Room
@app.route("/rooms/<int:room_id>/enemies/<int:enemy_id>", methods=["DELETE"])
def remove_enemy_from_room(room_id, enemy_id):
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    # Initialize EnemyIDs as empty list if it's None
    if room.EnemyIDs is None:
        room.EnemyIDs = []
    
    if enemy_id not in room.EnemyIDs:
        return jsonify({"error": "Enemy not found in the room"}), 404
    
    room.EnemyIDs.remove(enemy_id)
    db.session.commit()
    
    return jsonify({"message": "Enemy removed from room", "room": room.to_dict()}), 200

# ✅ API to Get Room Items
@app.route("/rooms/<int:room_id>/items", methods=["GET"])
def get_room_items(room_id):
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    return jsonify({"room_id": room_id, "items": room.ItemIDs or []}), 200

# ✅ API to Get Room Enemies
@app.route("/rooms/<int:room_id>/enemies", methods=["GET"])
def get_room_enemies(room_id):
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    return jsonify({"room_id": room_id, "enemies": room.EnemyIDs or []}), 200

# ✅ API to Delete a Room
@app.route("/rooms/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    room = RoomModel.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    db.session.delete(room)
    db.session.commit()
    
    return jsonify({"message": "Room deleted successfully"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5016,debug=True)