from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class CharacterModel(db.Model):
    __tablename__ = "characters"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    hp = db.Column(db.Integer, nullable=False)
    skill_description = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hp": self.hp,
            "skill_description": self.skill_description
        }


# Refactor your init_db function
def init_db(app, seed=False):
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@mysql:3307/character_db")
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()

        # Only seed if explicitly requested
        if seed:
            from seed_data import seed_characters
            seed_characters()