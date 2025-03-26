from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Score(db.Model):
    __tablename__ = "Score"
    
    ScoreID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlayerID = db.Column(db.Integer, nullable=False)
    Points = db.Column(db.Integer, nullable=False)
    Reason = db.Column(db.Enum('combat', 'item_collection'), nullable=False)
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "score_id": self.ScoreID,
            "player_id": self.PlayerID,
            "points": self.Points,
            "reason": self.Reason,
            "timestamp": self.Timestamp.isoformat()
        } 