from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class Enemy(db.Model):
    __tablename__ = "enemies"

    enemy_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    health = db.Column(db.Integer, nullable=False)
    max_health = db.Column(db.Integer, nullable=False)
    attacks = db.Column(db.Text, nullable=False)  # JSON as string
    loot = db.Column(db.Text, nullable=True)      # JSON as string

    def to_dict(self):
        return {
            "enemy_id": self.enemy_id,
            "room_id": self.room_id,
            "name": self.name,
            "health": self.health,
            "max_health": self.max_health,
            "attacks": json.loads(self.attacks),
            "loot": json.loads(self.loot)
        }
