import os
from flask import Flask, jsonify, request
from models import db, Item

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/item_db")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ✅ Function to Pre-Fill the Item Table
def seed_items():
    default_items = [
        {"name": "Golden Sword", "description": "A shiny golden sword with high damage", "points": 100},
        {"name": "Leather Armor", "description": "Basic protective armor", "points": 50},
        {"name": "Small Shield", "description": "A small wooden shield", "points": 40},
        {"name": "Health Potion", "description": "Restores 50 health", "points": 30},
        {"name": "Lockpick", "description": "Unlocks most doors", "points": 40},
        {"name": "Magic Amulet", "description": "Grants resistance to magic", "points": 80}
    ]

    if Item.query.first() is None:
        for item_data in default_items:
            item = Item(**item_data)
            db.session.add(item)
        db.session.commit()
        print("Default items seeded.")
    else:
        print("Default items already seeded.")

# ✅ Initialize tables and seed default items
with app.app_context():
    db.create_all()
    seed_items()

# ✅ API to Create an Item
@app.route("/item", methods=["POST"])
def create_item():
    data = request.json
    if not data or "name" not in data or "description" not in data or "points" not in data:
        return jsonify({"error": "Missing item data"}), 400

    item = Item(name=data["name"], description=data["description"], points=data["points"])
    db.session.add(item)
    db.session.commit()

    return jsonify({"message": "Item created", "item": item.to_dict()}), 201

# ✅ API to Fetch an Item by ID
@app.route("/item/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    return jsonify(item.to_dict())

# ✅ API to Fetch All Items
@app.route("/items", methods=["GET"])
def get_all_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
