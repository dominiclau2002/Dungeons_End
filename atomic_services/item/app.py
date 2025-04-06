import os
from flask import Flask, jsonify, request
from models import db, Item

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+mysqlconnector://user:password@mysql/item_db"
)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ✅ Initialize tables
with app.app_context():
    db.create_all()

# ✅ API to Create an Item


@app.route("/item", methods=["POST"])
def create_item():
    data = request.get_json()

    required_fields = ["name", "description"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "error": "Missing required fields",
            "required": required_fields
        }), 400

    # Check for duplicate item name
    existing_item = Item.query.filter_by(Name=data["name"]).first()
    if existing_item:
        return jsonify({
            "error": "Item with this name already exists"
        }), 409

    new_item = Item(
        Name=data["name"],
        Description=data["description"],
        Points=data.get("points", 0),
        HasEffect=data.get("has_effect", False)
    )

    db.session.add(new_item)
    db.session.commit()

    return jsonify({
        "message": "Item created successfully",
        "item": new_item.to_dict()
    }), 201

# ✅ API to Fetch an Item by ID


@app.route("/item/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({
            "error": "Item not found"
        }), 404

    return jsonify(item.to_dict()), 200

# ✅ API to Fetch All Items


@app.route("/items", methods=["GET"])
def get_all_items():
    items = Item.query.all()
    return jsonify({
        "items": [item.to_dict() for item in items]
    }), 200

# ✅ API to Update an Item


@app.route("/item/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({
            "error": "Item not found"
        }), 404

    data = request.get_json()

    if "name" in data:
        existing_item = Item.query.filter_by(Name=data["name"]).first()
        if existing_item and existing_item.ItemID != item_id:
            return jsonify({
                "error": "Item with this name already exists"
            }), 409
        item.Name = data["name"]

    if "description" in data:
        item.Description = data["description"]
    if "points" in data:
        item.Points = data["points"]
    if "has_effect" in data:
        item.HasEffect = data["has_effect"]

    db.session.commit()

    return jsonify({
        "message": "Item updated successfully",
        "item": item.to_dict()
    }), 200

# ✅ API to Delete an Item


@app.route("/item/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({
            "error": "Item not found"
        }), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "message": "Item deleted successfully",
        "deleted_item": item.to_dict()
    }), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5002, debug=True)
