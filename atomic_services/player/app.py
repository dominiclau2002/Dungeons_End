#atomic_services\player\app.py
import os
from flask import Flask,jsonify, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

################## Use environment variables for database configuration ############################
DATABASE_URL = "mysql+mysqlconnector://root:@localhost/player_db"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

############## Define the Player db model ##############
class PlayerModel(db.Model):
    __tablename__ = "Player"
    
    PlayerID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), unique=True, nullable=False)
    Health = db.Column(db.Integer,nullable=False, default=100)
    Damage = db.Column(db.Integer, nullable=False, default=10)
    RoomID = db.Column(db.Integer, nullable=True)
    ItemID = db.Column(db.Integer, nullable=True)
    
    def to_dict(self):
        return {
            "PlayerID": self.PlayerID,
            "Name": self.Name,
            "Health": self.Health,
            "Damage": self.Damage,
            "RoomID": self.RoomID,
            "ItemID": self.ItemID
        }
        
with app.app_context():
    db.create_all()
    
@app.route("/player",methods=["POST"])
def create_player():
    data = request.get_json()
    name = data.get("name", "Unknown Hero")
    itemid = data.get("itemid") #Default to None if not provided
    
    player = Player(Name=name, Health=100,Damage=10,RoomID=1, ItemID=itemid)
    db.session.add(player)
    db.session.commit()
    
    return jsonify({"message": "Player created", "Player": player.to_dict()}), 201


#### GET player details
@app.route("/player/<int:player_id>",methods=["GET"])
def get_player(player_id):
    player = PlayerModel.query.get(player_id)
    
    if not player:
        return jsonify({"error": "Player not found!"}), 404
    
    return jsonify(player.to_dict())
    
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
    
#### PUT (Update player health, items, etc.)
@app.route("/player/<int:player_id>", methods=["PUT"])
def update_player(player_id):
    player = PlayerModel.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found!"}), 404

    data = request.get_json()
    if "health" in data:
        player.Health = data["health"]
    if "itemid" in data:
        player.ItemID = data["itemid"]

    db.session.commit()
    return jsonify({"message": "Player updated", "Player": player.to_dict()}), 200