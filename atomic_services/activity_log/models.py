from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone

db = SQLAlchemy()

def sg_now():
    sg_offset = timedelta(hours=8)
    return datetime.utcnow() + sg_offset

class ActivityLog(db.Model):
    __tablename__ = 'ActivityLog'
    
    LogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlayerID = db.Column(db.Integer, nullable=False)
    Action = db.Column(db.String(255), nullable=False)
    Timestamp = db.Column(db.DateTime, default=sg_now)

    def to_dict(self):
        return {
            'log_id': self.LogID,
            'player_id': self.PlayerID,
            'action': self.Action,
            'timestamp': self.Timestamp.isoformat()
        }