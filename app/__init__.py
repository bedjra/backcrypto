from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS 
from flasgger import Swagger


# Déclaration de l'instance SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.config["JWT_SECRET_KEY"] = "votre_cle_secrete"
    Swagger(app)  # ✅ Initialisation ici avec l'app Flask

    # Initialiser SQLAlchemy et JWTManager
    db.init_app(app)  # ✅ Pas de redéclaration !
    jwt = JWTManager(app)

    # Configurer CORS
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)


    # Importer et enregistrer les routes
    from .routes import main
    app.register_blueprint(main)

    # Créer les tables si elles n'existent pas
    with app.app_context():
        db.create_all()

    return app



