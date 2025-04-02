# atomic_services\inventory\app.py
import os
import logging
from flask import Flask, jsonify, request
from models import db, Inventory

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    logger.info("Database tables initialized")

# ✅ API to Add an Item to Inventory - Using URL parameters instead of JSON body


@app.route("/inventory/player/<int:player_id>/item/<int:item_id>", methods=["POST"])
def add_to_inventory(player_id, item_id):
    logger.debug(f"Adding item {item_id} to player {player_id}'s inventory")

    # Check if player already has this item
    existing_item = Inventory.query.filter_by(
        PlayerID=player_id,
        ItemID=item_id
    ).first()

    if existing_item:
        logger.info(f"Player {player_id} already has item {item_id}")
        return jsonify({
            "error": "Player already has this item",
            "inventory_item": existing_item.to_dict()
        }), 409

    # Create new inventory entry
    inventory_item = Inventory(
        PlayerID=player_id,
        ItemID=item_id
    )

    db.session.add(inventory_item)
    db.session.commit()
    logger.info(f"Added item {item_id} to player {player_id}'s inventory")

    return jsonify({
        "message": "Item added to inventory successfully",
        "inventory_item": inventory_item.to_dict()
    }), 201

# ✅ API to Remove an Item from Inventory - Using URL parameters and DELETE method


@app.route("/inventory/player/<int:player_id>/item/<int:item_id>", methods=["DELETE"])
def remove_from_inventory(player_id, item_id):
    logger.debug(
        f"Removing item {item_id} from player {player_id}'s inventory")

    # Find the inventory item
    inventory_item = Inventory.query.filter_by(
        PlayerID=player_id,
        ItemID=item_id
    ).first()

    if not inventory_item:
        logger.warning(
            f"Item {item_id} not found in player {player_id}'s inventory")
        return jsonify({
            "error": "Item not found in player's inventory"
        }), 404

    # Remove the item
    item_dict = inventory_item.to_dict()
    db.session.delete(inventory_item)
    db.session.commit()
    logger.info(f"Removed item {item_id} from player {player_id}'s inventory")

    return jsonify({
        "message": "Item removed from inventory successfully",
        "removed_item": item_dict
    }), 200

# ✅ API to View Player's Inventory


@app.route("/inventory/player/<int:player_id>", methods=["GET"])
def view_inventory(player_id):
    logger.debug(f"Getting inventory for player {player_id}")
    inventory_items = Inventory.query.filter_by(PlayerID=player_id).all()
    
    # Extract just the item IDs into a simple array
    item_ids = [item.ItemID for item in inventory_items]
    
    logger.info(
        f"Found {len(item_ids)} items in player {player_id}'s inventory")
    return jsonify({
        "player_id": player_id,
        "inventory": item_ids
    }), 200

# ✅ API to Check if Player Has Item - Now just using the RESTful version


@app.route("/inventory/player/<int:player_id>/item/<int:item_id>", methods=["GET"])
def check_item(player_id, item_id):
    logger.debug(f"Checking if player {player_id} has item {item_id}")
    item = Inventory.query.filter_by(
        PlayerID=player_id,
        ItemID=item_id
    ).first()

    has_item = bool(item)
    logger.info(f"Player {player_id} has item {item_id}: {has_item}")

    return jsonify({
        "player_id": player_id,
        "item_id": item_id,
        "has_item": has_item,
        "inventory_entry": item.to_dict() if item else None
    }), 200

# ✅ API to Clear Player's Inventory


@app.route("/inventory/player/<int:player_id>", methods=["DELETE"])
def clear_inventory(player_id):
    logger.debug(f"Clearing inventory for player {player_id}")
    items = Inventory.query.filter_by(PlayerID=player_id).all()

    if not items:
        logger.info(f"Inventory already empty for player {player_id}")
        return jsonify({
            "message": "Inventory already empty",
            "player_id": player_id,
            "items_removed": 0
        }), 200

    items_count = len(items)
    for item in items:
        db.session.delete(item)

    db.session.commit()
    logger.info(
        f"Cleared {items_count} items from player {player_id}'s inventory")

    return jsonify({
        "message": f"Cleared inventory for player {player_id}",
        "player_id": player_id,
        "items_removed": items_count
    }), 200

# ✅ API to Get All Inventories (admin endpoint)


@app.route("/inventories", methods=["GET"])
def get_all_inventories():
    logger.debug("Getting all inventories")
    all_items = Inventory.query.all()

    logger.info(f"Found {len(all_items)} inventory entries across all players")
    return jsonify({
        "inventories": [item.to_dict() for item in all_items],
        "count": len(all_items)
    }), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        logger.info("Database tables created on startup")
    app.run(host="0.0.0.0", port=5001, debug=True)
