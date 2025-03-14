#\text-game\atomic_services\player.py
import requests
import random
class Player:
    def __init__(self, name=None,itemid=None):
        self.name = name if name else "Unknown Hero" #Allow player to set name
        self.health = 100 #Set default health to 100
        inventory_response = requests.get("http://inventory:5001/inventory")#Start with empty Inventory, called from inventory.py, initializes an Inventory object
        if inventory_response.status_code == 200:
            self.inventory = inventory_response.json().get("Inventory Status", [])  # Extract inventory contents
        else:
            self.inventory = []  # Default to empty if service fails
        self.stats = {"strength": random.randint(5,10), "agility": random.randint(5,10), "intelligence": random.randint(5,10)} #Player will start with randomized stats 
        self.itemid = itemid #Start with no item

    def get_player_info(self):
        
        item_details = None
        if self.itemid:
            # Fetch item details from item microservice
            try:
                item_response = requests.get(f"http://item:5002/item/{self.itemid}", timeout=3)
                if item_response.status_code == 200:
                    item_details = item_response.json()  # ✅ Parse JSON properly
                else:
                    item_details = {"error": "Item not found"}
            except requests.exceptions.RequestException:
                item_details = {"error": "Item service unreachable"}
                
        return {
            "Player Name": self.name,
            "Current Health": self.health,
            "Current Inventory": f"You have {len(self.inventory)} items in your inventory.",
            "Stats": self.stats,
            "Item": item_details if item_details else "None"
        }

    # def increase_health(self, amount):
    #     self.health += amount
    #     return {"message": f"You regained {amount} health. Health increased to {self.health}."}
    
    # def decrease_health(self, amount):
    #     self.health -= amount
    #     return {"message": f"You took {amount} damage. Health decreased to {self.health}."}

    # def player_enters_room(self, room_name):
    #     return {"message": f"Player entered {room_name}."}

    # def player_exits_room(self, room_name):
    #     return {"message": f"Player exited {room_name}."}
    
    # def equip_weapon(self, weapon_id):
    #     inventory_response = requests.get("http://inventory:5001/inventory")
    #     if inventory_response.status_code == 200:
    #         inventory = inventory_response.json().get("inventory", [])
    #         for item in inventory:
    #             if item["id"] == weapon_id and item["type"] == "Weapon":
    #                 self.weapon = item["name"]
    #                 return {"message": f"{item['name']} equipped as weapon."}
    #     return {"error": f"Item ID {weapon_id} not found or is not a weapon."}

    # def equip_armour(self, armour_id):
    #     inventory_response = requests.get("http://inventory:5001/inventory")
    #     if inventory_response.status_code == 200:
    #         inventory = inventory_response.json().get("inventory", [])
    #         for item in inventory:
    #             if item["id"] == armour_id and item["type"] == "Armour":
    #                 self.armour = item["name"]
    #                 return {"message": f"{item['name']} equipped as armour."}
    #     return {"error": f"Item ID {armour_id} not found or is not armour."}

    # def use_consumable(self, item_id):
    #     inventory_response = requests.get("http://inventory:5001/inventory")
    #     if inventory_response.status_code == 200:
    #         inventory = inventory_response.json().get("inventory", [])
    #         for item in inventory:
    #             if item["id"] == item_id and item["type"] == "Consumable":
    #                 self.health += 20
    #                 requests.post("http://inventory:5001/remove", json={"id": item_id})  # Remove item from inventory
    #                 return {"message": f"Used {item['name']}. Health increased to {self.health}."}
    #     return {"error": f"Item ID {item_id} not found in inventory or is not a consumable."}