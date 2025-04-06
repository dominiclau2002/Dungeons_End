from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db = SQLAlchemy()

class Item(db.Model):
    __tablename__ = "Item"
    
    ItemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), unique=True, nullable=False)
    Description = db.Column(db.String(200), nullable=False)
    HasEffect = db.Column(db.Boolean, default=False, nullable=False)
    Effect = db.Column(Enum('attack', 'health', name='effect_types'), nullable=True)
    Points = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {
            "item_id": self.ItemID,
            "name": self.Name,
            "description": self.Description,
            "has_effect": self.HasEffect,
            "effect": self.Effect,
            "points": self.Points
        } 