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
    valid_classes = ['Warrior', 'Rogue']
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

    # Set class-specific stats
    if data['character_class'] == 'Warrior':
        max_health = 200
        damage = 10
    else:  # Rogue
        max_health = 150
        damage = 20

    print(f"Creating new player with RoomID=0")  # Add logging
    new_player = Player(
        Name=data['name'],
        CharacterClass=data['character_class'],
        MaxHealth=max_health,
        CurrentHealth=max_health,  # Set current health equal to max health initially
        Damage=damage,
        RoomID=0
    )

    db.session.add(new_player)
    db.session.commit()

    player_dict = new_player.to_dict()
    print(f"Player created: {player_dict}")  # Add logging

    return jsonify({
        "message": "Player created successfully",
        "player": player_dict
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

    # Update health fields
    if "max_health" in data:
        player.MaxHealth = data['max_health']
    if "current_health" in data:
        player.CurrentHealth = data['current_health']
    # For backward compatibility
    if "health" in data and "current_health" not in data:
        player.CurrentHealth = data['health']
        
    if "damage" in data:
        player.Damage = data['damage']
    if "room_id" in data:
        player.RoomID = data['room_id']
    if "sum_score" in data:
        player.sum_score = data["sum_score"]


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

# ✅ Find player by name
@app.route('/player/name/<string:player_name>', methods=['GET'])
def get_player_by_name(player_name):
    player = Player.query.filter_by(Name=player_name).first()
    if not player:
        return jsonify({
            "error": "Player not found"
        }), 404

    return jsonify(player.to_dict()), 200

# ✅ Patch sum_score for player
@app.route('/player/<int:player_id>/score', methods=['PATCH'])
def update_player_score(player_id):
    data = request.get_json()
    points = data.get("points", 0)

    if points == 0:
        return jsonify({"error": "No points provided"}), 400

    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    player.sum_score += points
    db.session.commit()

    return jsonify({
        "message": f"Score updated by {points}",
        "new_sum_score": player.sum_score
    }), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
