from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime

db = SQLAlchemy()

class PlayerRoomInteraction(db.Model):
    """
    Model to track a player's interactions with rooms, including:
    - Items picked up
    - Enemies defeated
    - Other interactions as needed
    """
    __tablename__ = 'player_room_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, nullable=False, index=True)
    room_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Store item IDs and enemy IDs as JSON arrays
    items_picked = db.Column(db.Text, default='[]')  # JSON array of item IDs
    enemies_defeated = db.Column(db.Text, default='[]')  # JSON array of enemy IDs
    
    # Timestamp for when this interaction was first recorded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Timestamp for when this interaction was last updated
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add a unique constraint to prevent duplicates
    __table_args__ = (
        db.UniqueConstraint('player_id', 'room_id', name='uix_player_room'),
    )
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'room_id': self.room_id,
            'items_picked': json.loads(self.items_picked),
            'enemies_defeated': json.loads(self.enemies_defeated),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def add_picked_item(self, item_id):
        """Add an item to the list of picked items."""
        items = json.loads(self.items_picked)
        if item_id not in items:
            items.append(item_id)
            self.items_picked = json.dumps(items)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def add_defeated_enemy(self, enemy_id):
        """Add an enemy to the list of defeated enemies."""
        enemies = json.loads(self.enemies_defeated)
        if enemy_id not in enemies:
            enemies.append(enemy_id)
            self.enemies_defeated = json.dumps(enemies)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def has_picked_item(self, item_id):
        """Check if an item has been picked up."""
        items = json.loads(self.items_picked)
        return item_id in items
    
    def has_defeated_enemy(self, enemy_id):
        """Check if an enemy has been defeated."""
        enemies = json.loads(self.enemies_defeated)
        return enemy_id in enemies 