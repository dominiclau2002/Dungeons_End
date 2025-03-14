from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Enemy(db.Model):
    """
    Represents an enemy with health, attacks, and loot.
    Now stored in a MySQL database using SQLAlchemy.
    """

    __tablename__ = "Enemy"

    EnemyID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RoomID = db.Column(db.Integer, nullable=False, unique=True)  # Each room has 1 enemy
    Name = db.Column(db.String(50), nullable=False)
    Health = db.Column(db.Integer, nullable=False)
    Attacks = db.Column(db.JSON, nullable=False)  # Store attacks as a JSON object
    Loot = db.Column(db.JSON, nullable=True)  # Store loot as a JSON object

    def __init__(self, room_id, name, health, attacks, loot=None):
        self.RoomID = room_id
        self.Name = name
        self.Health = health
        self.Attacks = attacks
        self.Loot = loot if loot else []

    def to_dict(self):
        return {
            "EnemyID": self.EnemyID,
            "RoomID": self.RoomID,
            "Name": self.Name,
            "Health": self.Health,
            "Attacks": self.Attacks,
            "Loot": self.Loot,
        }

    def take_damage(self, damage):
        """
        Reduces enemy health. If defeated, returns loot.
        """
        self.Health -= damage
        if self.Health <= 0:
            return {"message": f"{self.Name} has been defeated!", "loot": self.Loot}
        return {"message": f"{self.Name} took {damage} damage. Remaining HP: {self.Health}"}

    def attack(self):
        """
        Enemy performs a random attack.
        """
        import random
        attack_name, damage_range = random.choice(list(self.Attacks.items()))
        damage = random.randint(*damage_range)
        return {"attack": attack_name, "damage": damage}