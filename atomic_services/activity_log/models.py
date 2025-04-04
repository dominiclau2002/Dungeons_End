from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ActivityLog(db.Model):
    __tablename__ = 'ActivityLog'
    
    LogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Action = db.Column(db.Enum('enemy_defeat', 'item_pickup', 'enter_room'), nullable=False)
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'log_id': self.LogID,
            'action': self.Action,
            'timestamp': self.Timestamp.isoformat()
        } 