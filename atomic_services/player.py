#\text-game\atomic_services\player.py
from atomic_services.inventory import Inventory #Import Inventory Class
#from atomic_services.room import Room #Import Room class
import random
class Player:
    def __init__(self, name=None):
        self.name = name if name else "Unknown Hero" #Allow player to set name
        self.health = 100 #Set default health to 100
        self.inventory = Inventory() #Start with empty Inventory, called from inventory.py, initializes an Inventory object
        self.stats = {"strength": random.randint(5,10), "agility": random.randint(5,10), "intelligence": random.randint(5,10)} #Player will start with randomized stats 
        self.weapon = "None" #Start with no weapon
        self.armour = "None" #Start with no armour

    def get_player_info(self):
        return {
            "Player Name": self.name,
            "Current Health": self.health,
            "Current Inventory": f"You have {len(self.inventory.contents)} items in your inventory.",
            "Stats": self.stats,
            "Weapon": self.weapon,
            "Armour": self.armour
        }

    def increase_health(self, amount):
        self.health += amount
        return {"message": f"You regained {amount} health. Health increased to {self.health}."}
    
    def decrease_health(self, amount):
        self.health -= amount
        return {"message": f"You took {amount} damage. Health decreased to {self.health}."}

    def player_enters_room(self, room_name):
        return {"message": f"Player entered {room_name}."}

    def player_exits_room(self, room_name):
        return {"message": f"Player exited {room_name}."}
    
    def equip_weapon(self, weapon_name):
        # Check if weapon_name is in inventory
        for item in self.inventory.contents:
            if item.name == weapon_name:
                # Check if it's a weapon type
                if item.item_type == "Weapon":
                    self.weapon = weapon_name
                    return {"message": f"{weapon_name} equipped as weapon."}
                else:
                    return {"error": f"{weapon_name} is not a weapon and cannot be equipped as one."}
        return {"error": f"{weapon_name} not found in inventory."}
    
    def equip_armour(self, armour_name):
        # Check if armour_name is in inventory
        for item in self.inventory.contents:
            if item.name == armour_name:
                # Check if it's an armour type
                if item.item_type == "Armour":
                    self.armour = armour_name
                    return {"message": f"{armour_name} equipped as armour."}
                else:
                    return {"error": f"{armour_name} is not armour and cannot be equipped as one."}
        return {"error": f"{armour_name} not found in inventory."}
    
    def use_consumable(self, item_name):
        # Find the item in inventory
        for item in self.inventory.contents:
            if item.name == item_name:
                # Check if it's a consumable
                if item.item_type == "Consumable":
                    # Apply effect (for now just increase health by 20)
                    self.health += 20
                    # Remove item from inventory after use
                    self.inventory.remove_from_inventory(item_name)
                    return {"message": f"Used {item_name}. Health increased to {self.health}."}
                else:
                    return {"error": f"{item_name} is not a consumable item."}
        return {"error": f"{item_name} not found in inventory."}