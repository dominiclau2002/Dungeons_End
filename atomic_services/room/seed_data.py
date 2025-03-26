from models import db, RoomModel

def seed_rooms():
    rooms_data = [
        {
            "Name": "A dark room with a treasure chest",
            "Description": "A mysterious room shrouded in darkness, with a promising treasure chest waiting to be discovered.",
            "ItemIDs": [1, 2],
            "EnemyIDs": [],
            "DoorLocked": False
        },
        {
            "Name": "A bright room with a fountain",
            "Description": "A well-lit chamber featuring a beautiful fountain. The water's gentle sound echoes through the room.",
            "ItemIDs": [3, 5],
            "EnemyIDs": [1],
            "DoorLocked": False
        },
        {
            "Name": "A mysterious cave",
            "Description": "A foreboding cave with strange markings on the walls and an eerie atmosphere.",
            "ItemIDs": [4],
            "EnemyIDs": [2],
            "DoorLocked": True
        }
    ]

    for room_data in rooms_data:
        room = RoomModel(**room_data)
        db.session.add(room)
    
    try:
        db.session.commit()
        print("Room data successfully seeded!")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding room data: {str(e)}") 