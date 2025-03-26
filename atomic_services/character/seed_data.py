from models import db, CharacterModel

def seed_characters():
    characters = [
        {"name": "Warrior", "hp": 100, "skill_description": "Berserker attack: Damage scales with missing HP."},
        {"name": "Cleric", "hp": 80, "skill_description": "Heal: Restores 15 HP if dice roll succeeds."},
        {"name": "Rogue", "hp": 75, "skill_description": "Backstab: Double damage if dice roll succeeds."},
        {"name": "Witch", "hp": 70, "skill_description": "Poisons enemy for damage over time if dice roll succeeds."}
    ]
    
    # Check if data already exists and seed accordingly
    if CharacterModel.query.first() is None:
        for char_data in characters:
            character = CharacterModel(**char_data)
            db.session.add(character)
        
        try:
            db.session.commit()
            print("Character data successfully seeded!")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding character data: {str(e)}")
    else:
        print("Characters already seeded.")

