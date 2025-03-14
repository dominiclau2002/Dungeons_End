from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql/player_db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ✅ Define Character and Player Tables
class Character(db.Model):
    __tablename__ = "Characters"

    CharacterID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), unique=True, nullable=False)
    HP = db.Column(db.Integer, nullable=False)
    SkillDescription = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "Name": self.Name,
            "HP": self.HP,
            "SkillDescription": self.SkillDescription
        }

class Player(db.Model):
    __tablename__ = "Players"

    PlayerID = db.Column(db.Integer, primary_key=True)
    CharacterName = db.Column(db.String(50), db.ForeignKey("Characters.Name"), nullable=False)
    HP = db.Column(db.Integer, nullable=False)
    RoomID = db.Column(db.Integer, default=1)  # Start in Room 1

    def to_dict(self):
        return {
            "PlayerID": self.PlayerID,
            "CharacterName": self.CharacterName,
            "HP": self.HP,
            "RoomID": self.RoomID
        }

with app.app_context():
    db.create_all()

# ✅ Fetch Character Stats
@app.route('/character/<string:char_name>', methods=['GET'])
def get_character(char_name):
    character = Character.query.filter_by(Name=char_name).first()
    if not character:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(character.to_dict())

# ✅ Initialize Player
@app.route('/initialize_player', methods=['POST'])
def initialize_player():
    data = request.get_json()
    player_id = data.get("player_id")
    character = data.get("character")

    if not player_id or not character:
        return jsonify({"error": "PlayerID and character data are required"}), 400

    new_player = Player(PlayerID=player_id, CharacterName=character["Name"], HP=character["HP"])
    db.session.add(new_player)
    db.session.commit()

    return jsonify({"message": "Player initialized successfully!", "player": new_player.to_dict()}), 201

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
