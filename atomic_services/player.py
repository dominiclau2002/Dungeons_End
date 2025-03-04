class Player:
    def __init__(self, name="Hero"):
        self.name = name
        self.health = 100
        self.inventory = []
        self.stats = {"strength": 10, "agility": 8, "intelligence": 7}

    def get_player_info(self):
        return {
            "name": self.name,
            "health": self.health,
            "inventory": self.inventory,
            "stats": self.stats,
        }

    def update_health(self, amount):
        self.health += amount
        return {"message": f"Health updated to {self.health}"}

    def add_to_inventory(self, item):
        self.inventory.append(item)
        return {"message": f"{item} added to inventory"}
