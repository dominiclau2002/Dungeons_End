#\text-game\atomic_services\inventory.py
import requests
class Inventory:
    def __init__(self,name="Your Inventory"):
        self.name = name
        self.contents = []
        self.capacity = 10
        
    def add_to_inventory(self, id, item_name, item_type):
        response = requests.post("http://item:5002/item", json={"id":id,"name": item_name, "item_type": item_type})
        if response.status_code == 200:
            try:
                item = response.json()
                self.contents.append(item)
                return {"message": f"{item['name']} (ID: {item['id']}) added to inventory"}

            except ValueError:
                return {"error": "Invalid response from item service"}
        return {"error": "Failed to retrieve item"}
    
    def remove_from_inventory(self, item_id):
        for item in self.contents:
            if item["id"] == item_id:
                self.contents.remove(item)
                return {"message": f"Item ID {item_id} removed from inventory"}

        return {"error": f"Error! Item ID {item_id} not found in inventory!"}

    def view_inventory_items(self):
        if self.contents:
            return {"inventory": [{"id": item["id"], "name": item["name"], "type": item["item_type"]} for item in self.contents]}
        else:
            return {"message": "Your inventory is empty!"}
        
        
