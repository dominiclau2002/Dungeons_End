#atomic_services\inventory\app.py
import os
from flask import Flask,jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


# ✅ Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://user:password@inventory_db/inventory_db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ✅ Define the Inventory Database Model
class InventoryModel(db.Model):
    __tablename__ = "Inventory"

    InventoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlayerID = db.Column(db.Integer, nullable=False)  # ✅ Foreign key reference to Player
    ItemID = db.Column(db.Integer, nullable=False)  # ✅ Foreign key reference to Item

    def to_dict(self):
        return {
            "InventoryID": self.InventoryID,
            "PlayerID": self.PlayerID,
            "ItemID": self.ItemID
        }

with app.app_context():
    db.create_all()



# ✅ API to Add an Item to Inventory
@app.route("/inventory", methods=["POST"])
def add_to_inventory():
    data = request.get_json()
    player_id = data.get("player_id")
    item_id = data.get("item_id")

    if not player_id or not item_id:
        return jsonify({"error": "PlayerID and ItemID are required"}), 400

    inventory_item = InventoryModel(PlayerID=player_id, ItemID=item_id)
    db.session.add(inventory_item)
    db.session.commit()

    return jsonify({"message": "Item added to inventory", "Inventory": inventory_item.to_dict()}), 201

# ✅ API to Remove an Item from Inventory
@app.route("/inventory/remove", methods=["POST"])
def remove_from_inventory():
    data = request.get_json()
    player_id = data.get("player_id")
    item_id = data.get("item_id")

    if not player_id or not item_id:
        return jsonify({"error": "PlayerID and ItemID are required"}), 400

    inventory_item = InventoryModel.query.filter_by(PlayerID=player_id, ItemID=item_id).first()
    if not inventory_item:
        return jsonify({"error": "Item not found in inventory"}), 404

    db.session.delete(inventory_item)
    db.session.commit()

    return jsonify({"message": "Item removed from inventory"}), 200

# ✅ API to View Player Inventory
@app.route("/inventory/<int:player_id>", methods=["GET"])
def view_inventory(player_id):
    inventory_items = InventoryModel.query.filter_by(PlayerID=player_id).all()
    if not inventory_items:
        return jsonify({"message": "Inventory is empty"}), 200

    return jsonify({"inventory": [item.to_dict() for item in inventory_items]}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5001,debug=True)