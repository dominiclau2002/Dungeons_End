from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ActivityLog(db.Model):
    """
    Stores all player actions in the game.
    Now stored in a MySQL database using SQLAlchemy.
    """

    __tablename__ = "ActivityLogs"

    LogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlayerID = db.Column(db.Integer, nullable=False)
    Action = db.Column(db.String(255), nullable=False)
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically logs time

    def __init__(self, player_id, action):
        self.PlayerID = player_id
        self.Action = action

    def to_dict(self):
        return {
            "LogID": self.LogID,
            "PlayerID": self.PlayerID,
            "Action": self.Action,
            "Timestamp": self.Timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
