from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Character(db.Model):
    __tablename__ = "characters"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    hp = db.Column(db.Integer, nullable=False)
    skill_description = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hp": self.hp,
            "skill_description": self.skill_description
        }

class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    character_name = db.Column(db.String(50), nullable=False)
    health = db.Column(db.Integer, nullable=False)
    current_room_id = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            "id": self.id,
            "character_name": self.character_name,
            "health": self.health,
            "current_room_id": self.current_room_id
        }
