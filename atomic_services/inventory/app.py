#atomic_services\inventory\app.py
import os
from flask import Flask, jsonify, request
from models import db, Inventory

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+mysqlconnector://user:password@mysql/inventory_db"
)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ✅ API to Add an Item to Inventory
@app.route("/inventory", methods=["POST"])
def add_to_inventory():
    data = request.get_json()
    
    if not data or 'player_id' not in data or 'item_id' not in data:
        return jsonify({
            "error": "Missing required fields",
            "required": ["player_id", "item_id"]
        }), 400

    # Check if player already has this item
    existing_item = Inventory.query.filter_by(
        PlayerID=data['player_id'],
        ItemID=data['item_id']
    ).first()
    
    if existing_item:
        return jsonify({
            "error": "Player already has this item"
        }), 409

    inventory_item = Inventory(
        PlayerID=data['player_id'],
        ItemID=data['item_id']
    )
    
    db.session.add(inventory_item)
    db.session.commit()

    return jsonify({
        "message": "Item added to inventory",
        "inventory": inventory_item.to_dict()
    }), 201

# ✅ API to Remove an Item from Inventory
@app.route("/inventory/remove", methods=["POST"])
def remove_from_inventory():
    data = request.get_json()
    
    if not data or 'player_id' not in data or 'item_id' not in data:
        return jsonify({
            "error": "Missing required fields",
            "required": ["player_id", "item_id"]
        }), 400

    inventory_item = Inventory.query.filter_by(
        PlayerID=data['player_id'],
        ItemID=data['item_id']
    ).first()
    
    if not inventory_item:
        return jsonify({
            "error": "Item not found in player's inventory"
        }), 404

    db.session.delete(inventory_item)
    db.session.commit()

    return jsonify({
        "message": "Item removed from inventory",
        "removed_item": inventory_item.to_dict()
    }), 200

# ✅ API to View Player's Inventory
@app.route("/inventory/<int:player_id>", methods=["GET"])
def view_inventory(player_id):
    inventory_items = Inventory.query.filter_by(PlayerID=player_id).all()
    
    return jsonify({
        "player_id": player_id,
        "inventory": [item.to_dict() for item in inventory_items]
    }), 200

# ✅ API to Check if Player Has Item
@app.route("/inventory/<int:player_id>/has/<int:item_id>", methods=["GET"])
def check_item(player_id, item_id):
    item = Inventory.query.filter_by(
        PlayerID=player_id,
        ItemID=item_id
    ).first()
    
    return jsonify({
        "has_item": bool(item)
    }), 200

# ✅ API to Clear Player's Inventory
@app.route("/inventory/<int:player_id>", methods=["DELETE"])
def clear_inventory(player_id):
    items = Inventory.query.filter_by(PlayerID=player_id).all()
    
    if not items:
        return jsonify({
            "message": "Inventory already empty"
        }), 200
    
    for item in items:
        db.session.delete(item)
    
    db.session.commit()
    
    return jsonify({
        "message": f"Cleared inventory for player {player_id}"
    }), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)