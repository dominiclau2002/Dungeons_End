from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Inventory(db.Model):
    __tablename__ = "Inventory"
    
    InventoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlayerID = db.Column(db.Integer, nullable=False)
    ItemID = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "inventory_id": self.InventoryID,
            "player_id": self.PlayerID,
            "item_id": self.ItemID
        } 