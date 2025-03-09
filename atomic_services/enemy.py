import random

# Dictionary to store active enemies (key = room name, value = Enemy object)
enemy_instances = {}

class Enemy:
    """
    Represents an enemy in the game.
    Each enemy has:
    - Health points (HP)
    - Multiple attack types (with random damage)
    - Status effects they can inflict
    - Loot drops when defeated
    """

    def __init__(self, name, health, attacks, status_effects=None, loot=None):
        self.name = name
        self.health = health
        self.attacks = attacks  # Dictionary of attack names and damage range
        self.status_effects = status_effects if status_effects else {}  # Status effects enemy can inflict
        self.loot = loot if loot else []  # Items dropped after defeat

    def take_damage(self, damage):
        """
        Reduces enemy health when attacked and updates the stored state.
        """
        self.health -= damage
        if self.health <= 0:
            return {
                "message": f"{self.name} has been defeated!",
                "loot": self.drop_loot()  # Fixed: Loot drop is now called correctly
            }
        return {"message": f"{self.name} took {damage} damage. Remaining HP: {self.health}"}

    def attack(self):
        """
        Enemy performs a random attack from its attack list.
        """
        attack_name, damage_range = random.choice(list(self.attacks.items()))  # Randomly choose an attack
        damage = random.randint(*damage_range)  # Roll damage within the attack range
        status_inflicted = None

        # 30% chance to inflict a status effect
        if self.status_effects and random.random() < 0.3:
            status_inflicted = random.choice(list(self.status_effects.keys()))
            effect_duration = self.status_effects[status_inflicted]  # Duration of the effect
        else:
            effect_duration = 0

        return {
            "attack": attack_name,
            "damage": damage,
            "status_effect": status_inflicted,
            "effect_duration": effect_duration  # How long the effect lasts
        }

    def is_defeated(self):
        """
        Checks if the enemy is defeated.
        """
        return self.health <= 0

    def drop_loot(self):
        """
        Returns the loot items dropped when the enemy is defeated.
        Also removes the enemy from active instances.
        """
        if self.is_defeated():
            if self.name in enemy_instances:
                del enemy_instances[self.name]  # Remove defeated enemy
            return self.loot
        return []

def get_enemy(room_name):
    """
    Retrieves the enemy in the given room.
    If the enemy does not exist, it creates a new one.
    """
    if room_name not in enemy_instances:
        # Creating a new enemy for this room
        enemy_instances[room_name] = Enemy(
            name="Goblin",
            health=30,
            attacks={
                "Slash": (5, 12),
                "Bite": (3, 8),
                "Poisoned Dagger": (4, 10)
            },
            status_effects={"Poison": 3},  # Poison effect lasts for 3 turns
            loot=["Leather Armor", "5 Gold Coins"]
        )
    return enemy_instances[room_name]


# python api/enemy_service.py
# get enemy
# http://127.0.0.1:5005/enemy/Room 2

# getting attacked
# http://127.0.0.1:5005/enemy/Room 2/attack

# attack enemy
# http://127.0.0.1:5005/enemy/Room 2/damage
# {
#     "damage": 12
# }