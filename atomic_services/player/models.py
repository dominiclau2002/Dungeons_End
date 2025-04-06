from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Player(db.Model):
    __tablename__ = "Player"
    
    PlayerID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), unique=True, nullable=False)
    CharacterClass = db.Column(db.Enum('Warrior', 'Rogue', 'Cleric', 'Ranger'), nullable=False)
    MaxHealth = db.Column(db.Integer, nullable=False, default=100)
    CurrentHealth = db.Column(db.Integer, nullable=False, default=100)
    Damage = db.Column(db.Integer, nullable=False, default=10)
    RoomID = db.Column(db.Integer, default=0)
    sum_score = db.Column(db.Integer, nullable=False, default=0)


    def to_dict(self):
        return {
            "player_id": self.PlayerID,
            "name": self.Name,
            "character_class": self.CharacterClass,
            "max_health": self.MaxHealth,
            "current_health": self.CurrentHealth,
            "health": self.CurrentHealth,
            "Health": self.CurrentHealth,
            "damage": self.Damage,
            "room_id": self.RoomID,
            "RoomID": self.RoomID,
            "sum_score": self.sum_score
        } 