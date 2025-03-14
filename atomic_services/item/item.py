# \text-game\atomic_services\item.py

import requests

class Item:
    def __init__(self, item_id):
        """Initialize an item by fetching its details from the database"""
        response = requests.get(f"http://item:5002/item/{item_id}")

        if response.status_code == 200:
            item_data = response.json()
            self.item_id = item_data["ItemID"]
            self.name = item_data["Name"]
            self.description = item_data["Description"]
            self.points = item_data["Points"]
        else:
            raise ValueError("Item not found in database!")

    def to_dict(self):
        return {
            "ItemID": self.item_id,
            "Name": self.name,
            "Description": self.description,
            "Points": self.points
        }
