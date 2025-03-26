from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import JSON

db = SQLAlchemy()

class Room(db.Model):
    __tablename__ = "Room"
    
    RoomID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Description = db.Column(db.String(200))
    ItemIDs = db.Column(JSON)  # Stores array of ItemIDs
    EnemyIDs = db.Column(JSON) # Stores array of EnemyIDs
    DoorLocked = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "room_id": self.RoomID,
            "description": self.Description,
            "item_ids": self.ItemIDs or [],
            "enemy_ids": self.EnemyIDs or [],
            "door_locked": bool(self.DoorLocked)
        } 