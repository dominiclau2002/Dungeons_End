#atomic_services\item\app.py
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://user:password@item_db/item_db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ✅ Define the Item Database Model
class ItemModel(db.Model):
    __tablename__ = "Item"

    ItemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), unique=True, nullable=False)
    Description = db.Column(db.String(200), nullable=False)
    Points = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "ItemID": self.ItemID,
            "Name": self.Name,
            "Description": self.Description,
            "Points": self.Points
        }
        
        
# ✅ Function to Pre-Fill the Item Table with Default Items
def seed_items():
    """Insert default items into the database if they do not already exist."""
    default_items = [
        {"Name": "Golden Sword", "Description": "A shiny golden sword with high damage", "Points": 100},
        {"Name": "Leather Armor", "Description": "Basic protective armor", "Points": 50},
        {"Name": "Small Shield", "Description": "A small wooden shield", "Points": 40},
        {"Name": "Health Potion", "Description": "Restores 50 health", "Points": 30},
        {"Name": "Lockpick", "Description": "Unlocks most doors", "Points": 40},
        {"Name": "Magic Amulet", "Description": "Grants resistance to magic", "Points": 80}
    ]

    #  Check if the table already has data
    if ItemModel.query.first() is None:  
        for item in default_items:
            new_item = ItemModel(**item)
            db.session.add(new_item)
        db.session.commit()
        print(" Default items added to the database.")
    else:
        print(" Default items already exist. No need to insert.")

with app.app_context():
    db.create_all()
    seed_items()  # ✅ Only seed items in the item microservice
#Calls the function to seed the database with default items

# API to Create an Item
@app.route("/item", methods=["POST"])
def create_item():
    data = request.json
    if not data or "name" not in data or "description" not in data or "points" not in data:
        return jsonify({"error": "Missing item data"}), 400

    new_item = ItemModel(Name=data["name"], Description=data["description"], Points=data["points"])
    db.session.add(new_item)
    db.session.commit()

    return jsonify({"message": "Item created", "Item": new_item.to_dict()}), 201

# ✅ API to Fetch an Item by ID
@app.route("/item/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = ItemModel.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    return jsonify(item.to_dict())

# ✅ API to Fetch All Items
@app.route("/items", methods=["GET"])
def get_all_items():
    items = ItemModel.query.all()
    return jsonify([item.to_dict() for item in items])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
