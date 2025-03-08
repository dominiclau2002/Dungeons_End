#C:\text-game\atomic_services\inventory.py
from atomic_services.item import Item
class Inventory:
    def __init__(self,name="Your Inventory"):
        self.name = name
        self.contents = []
        self.capacity = 10
        
    def add_to_inventory(self, item:Item):
        
        current_capacity = len(self.contents)
        
        if current_capacity < self.capacity:
            self.contents.append(item)
            return {"message": f"{item.name} added to inventory"}
        else:
            return {"error": "Your inventory is full!"}
    
    def remove_from_inventory(self, item_name):
        
        for item in self.contents:
            if item.name == item_name:
                self.contents.remove(item)
                return {"message": f"{item_name} removed from inventory"}
        
           
        return {"error":f"Error! {item_name} not found in inventory!" }
        
    def view_inventory_items(self):
        
        if self.contents:
            return {"inventory": [item.name for item in self.contents]} #Show item names in the inventory
        else:
            return {"message": "Your inventory is empty!"}
        
        
