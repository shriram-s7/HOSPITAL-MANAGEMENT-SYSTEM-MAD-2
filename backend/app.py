from flask import Flask
from config import Config
from models import db, cache, User
from flask_jwt_extended import JWTManager
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app)
    db.init_app(app)
    JWTManager(app)
    cache.init_app(app)
    
    from routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(role='Admin').first()
        if not admin_user:
            admin = User(username='admin', role='Admin', email='admin@hms.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
