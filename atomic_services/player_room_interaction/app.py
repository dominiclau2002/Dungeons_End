import os
from flask import Flask, jsonify, request
from models import db, PlayerRoomInteraction
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+mysqlconnector://user:password@mysql/player_room_interaction_db"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Helper function to get or create a player-room interaction
def get_or_create_interaction(player_id, room_id):
    """Get or create a player-room interaction record."""
    interaction = PlayerRoomInteraction.query.filter_by(
        player_id=player_id, room_id=room_id
    ).first()
    
    if not interaction:
        interaction = PlayerRoomInteraction(
            player_id=player_id,
            room_id=room_id
        )
        db.session.add(interaction)
        db.session.commit()
    
    return interaction

# API Routes

@app.route('/interaction', methods=['GET'])
def get_all_interactions():
    """Get all player-room interactions."""
    interactions = PlayerRoomInteraction.query.all()
    return jsonify({
        "interactions": [interaction.to_dict() for interaction in interactions]
    }), 200

@app.route('/player/<int:player_id>/room/<int:room_id>/interactions', methods=['GET'])
def get_player_room_interaction(player_id, room_id):
    """Get a specific player's interactions with a room."""
    interaction = PlayerRoomInteraction.query.filter_by(
        player_id=player_id, room_id=room_id
    ).first()
    
    if not interaction:
        # Return empty lists if no interaction found
        return jsonify({
            "player_id": player_id,
            "room_id": room_id,
            "items_picked": [],
            "enemies_defeated": []
        }), 200
    
    return jsonify(interaction.to_dict()), 200

@app.route('/player/<int:player_id>/interactions', methods=['GET'])
def get_player_interactions(player_id):
    """Get all interactions for a specific player."""
    interactions = PlayerRoomInteraction.query.filter_by(player_id=player_id).all()
    return jsonify({
        "player_id": player_id,
        "interactions": [interaction.to_dict() for interaction in interactions]
    }), 200

@app.route('/player/<int:player_id>/room/<int:room_id>/item/<int:item_id>/pickup', methods=['POST'])
def pickup_item(player_id, room_id, item_id):
    """Record that a player has picked up an item in a room."""
    interaction = get_or_create_interaction(player_id, room_id)
    
    # Check if already picked up
    if interaction.has_picked_item(item_id):
        return jsonify({
            "message": "Item already picked up",
            "player_id": player_id,
            "room_id": room_id,
            "item_id": item_id
        }), 200
    
    # Add the item to picked items
    interaction.add_picked_item(item_id)
    db.session.commit()
    
    logger.debug(f"Player {player_id} picked up item {item_id} in room {room_id}")
    
    return jsonify({
        "message": "Item pickup recorded successfully",
        "player_id": player_id,
        "room_id": room_id,
        "item_id": item_id
    }), 201

@app.route('/player/<int:player_id>/room/<int:room_id>/enemy/<int:enemy_id>/defeat', methods=['POST'])
def defeat_enemy(player_id, room_id, enemy_id):
    """Record that a player has defeated an enemy in a room."""
    interaction = get_or_create_interaction(player_id, room_id)
    
    # Check if already defeated
    if interaction.has_defeated_enemy(enemy_id):
        return jsonify({
            "message": "Enemy already defeated",
            "player_id": player_id,
            "room_id": room_id,
            "enemy_id": enemy_id
        }), 200
    
    # Add the enemy to defeated enemies
    interaction.add_defeated_enemy(enemy_id)
    db.session.commit()
    
    logger.debug(f"Player {player_id} defeated enemy {enemy_id} in room {room_id}")
    
    return jsonify({
        "message": "Enemy defeat recorded successfully",
        "player_id": player_id,
        "room_id": room_id,
        "enemy_id": enemy_id
    }), 201

@app.route('/player/<int:player_id>/reset', methods=['POST'])
def reset_player(player_id):
    """Reset all interactions for a specific player."""
    interactions = PlayerRoomInteraction.query.filter_by(player_id=player_id).all()
    
    for interaction in interactions:
        db.session.delete(interaction)
    
    db.session.commit()
    
    logger.debug(f"Reset all interactions for player {player_id}")
    
    return jsonify({
        "message": "Player interactions reset successfully",
        "player_id": player_id
    }), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5040, debug=True) 