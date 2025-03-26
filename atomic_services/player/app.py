import os
from flask import Flask, jsonify, request
from models import db, Player

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+mysqlconnector://user:password@mysql/player_db"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ✅ Create new player
@app.route('/player', methods=['POST'])
def create_player():
    data = request.get_json()
    
    required_fields = ["name", "character_class"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "error": "Missing required fields",
            "required": required_fields
        }), 400

    # Validate character class
    valid_classes = ['Warrior', 'Rogue', 'Cleric', 'Ranger']
    if data['character_class'] not in valid_classes:
        return jsonify({
            "error": "Invalid character class",
            "valid_classes": valid_classes
        }), 400

    # Check for duplicate player name
    existing_player = Player.query.filter_by(Name=data['name']).first()
    if existing_player:
        return jsonify({
            "error": "Player with this name already exists"
        }), 409

    new_player = Player(
        Name=data['name'],
        CharacterClass=data['character_class'],
        Health=data.get('health', 100),
        Damage=data.get('damage', 10),
        RoomID=data.get('room_id', 1)
    )
    
    db.session.add(new_player)
    db.session.commit()

    return jsonify({
        "message": "Player created successfully",
        "player": new_player.to_dict()
    }), 201

# ✅ Get player details
@app.route('/player/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({
            "error": "Player not found"
        }), 404
    
    return jsonify(player.to_dict()), 200

# ✅ Update player
@app.route('/player/<int:player_id>', methods=['PUT'])
def update_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({
            "error": "Player not found"
        }), 404

    data = request.get_json()
    
    if "name" in data:
        existing_player = Player.query.filter_by(Name=data['name']).first()
        if existing_player and existing_player.PlayerID != player_id:
            return jsonify({
                "error": "Player with this name already exists"
            }), 409
        player.Name = data['name']
    
    if "character_class" in data:
        valid_classes = ['Warrior', 'Rogue', 'Cleric', 'Ranger']
        if data['character_class'] not in valid_classes:
            return jsonify({
                "error": "Invalid character class",
                "valid_classes": valid_classes
            }), 400
        player.CharacterClass = data['character_class']
    
    if "health" in data:
        player.Health = data['health']
    if "damage" in data:
        player.Damage = data['damage']
    if "room_id" in data:
        player.RoomID = data['room_id']

    db.session.commit()

    return jsonify({
        "message": "Player updated successfully",
        "player": player.to_dict()
    }), 200

# ✅ Delete player
@app.route('/player/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({
            "error": "Player not found"
        }), 404

    db.session.delete(player)
    db.session.commit()

    return jsonify({
        "message": "Player deleted successfully",
        "deleted_player": player.to_dict()
    }), 200

# ✅ Get all players
@app.route('/players', methods=['GET'])
def get_all_players():
    players = Player.query.all()
    return jsonify({
        "players": [player.to_dict() for player in players]
    }), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
