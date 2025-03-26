from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Player(db.Model):
    __tablename__ = "Player"
    
    PlayerID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), unique=True, nullable=False)
    CharacterClass = db.Column(db.Enum('Warrior', 'Rogue', 'Cleric', 'Ranger'), nullable=False)
    Health = db.Column(db.Integer, nullable=False, default=100)
    Damage = db.Column(db.Integer, nullable=False, default=10)
    RoomID = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            "player_id": self.PlayerID,
            "name": self.Name,
            "character_class": self.CharacterClass,
            "health": self.Health,
            "damage": self.Damage,
            "room_id": self.RoomID
        } 