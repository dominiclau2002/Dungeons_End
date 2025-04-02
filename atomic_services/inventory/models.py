from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Inventory(db.Model):
    __tablename__ = 'Inventory'
    
    PlayerID = db.Column(db.Integer, primary_key=True)
    ItemID = db.Column(db.Integer, primary_key=True)
    
    def to_dict(self):
        return {
            "player_id": self.PlayerID,
            "item_id": self.ItemID
        } 