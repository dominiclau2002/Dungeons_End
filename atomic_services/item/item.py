# \text-game\atomic_services\item.py
class Item:
    def __init__(self,id, name,item_type):
        self.id = id
        self.name = name
        self.item_type = item_type
        
    def __repr__(self):
        return f"Item(name='{self.name}',type='{self.item_type}')"
        
    def __str__(self):
        return f"{self.name}: ({self.item_type})"