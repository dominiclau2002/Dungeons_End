import os
from flask import Flask, jsonify, request
from models import db, Player, Character

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/player_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Fetch character stats
@app.route('/character/<string:char_name>', methods=['GET'])
def get_character(char_name):
    character = Character.query.filter_by(name=char_name).first()
    if not character:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(character.to_dict())

# Initialize player with selected character
@app.route('/initialize_player', methods=['POST'])
def initialize_player():
    data = request.json
    player_id = data.get("player_id")
    character_data = data.get("character")

    if not player_id or not character_data:
        return jsonify({"error": "player_id and character data required"}), 400

    new_player = Player(
        id=player_id,
        character_name=character_data["name"],
        health=character_data["hp"],
        current_room_id=1
    )

    db.session.add(new_player)
    db.session.commit()

    return jsonify(new_player.to_dict()), 201

# Get player details
@app.route('/player/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    return jsonify(player.to_dict())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
