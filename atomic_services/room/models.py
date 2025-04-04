from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import JSON
import json

db = SQLAlchemy()

class Room(db.Model):
    __tablename__ = "Room"
    
    RoomID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Description = db.Column(db.String(200))
    ItemIDs = db.Column(JSON)  # Stores array of ItemIDs
    EnemyIDs = db.Column(JSON) # Stores array of EnemyIDs
    DoorLocked = db.Column(db.Boolean, default=False)

    def __init__(self, Description=None, ItemIDs=None, EnemyIDs=None, DoorLocked=False):
        self.Description = Description
        self.ItemIDs = ItemIDs if ItemIDs is not None else []
        self.EnemyIDs = EnemyIDs if EnemyIDs is not None else []
        self.DoorLocked = DoorLocked

    def to_dict(self):
        return {
            "room_id": self.RoomID,
            "description": self.Description,
            "item_ids": self.ItemIDs if self.ItemIDs is not None else [],
            "enemy_ids": self.EnemyIDs if self.EnemyIDs is not None else [],
            "door_locked": bool(self.DoorLocked)
        } 