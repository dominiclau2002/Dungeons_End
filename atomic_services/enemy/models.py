from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class Enemy(db.Model):
    __tablename__ = 'Enemy'
    
    EnemyID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), unique=True, nullable=False)
    Description = db.Column(db.Text, nullable=False)
    Health = db.Column(db.Integer, nullable=False)
    Damage = db.Column(db.Integer, nullable=False)
    Attack = db.Column(db.Integer, nullable=False)
    Loot = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        return {
            'enemy_id': self.EnemyID,
            'name': self.Name,
            'description': self.Description,
            'health': self.Health,
            'damage': self.Damage,
            'attack': self.Attack,
            'loot': self.Loot
        } 