from flask import Flask, render_template, redirect, url_for
from config import Config
from database import init_db
from routes import ingredientes_bp, platos_bp, menus_bp, albaranes_bp, importar_bp, clientes_bp
from routes.albaranes_masivos import albaranes_masivos_bp
from routes.cuadro_mando import cuadro_mando_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(ingredientes_bp, url_prefix='/ingredientes')
    app.register_blueprint(platos_bp, url_prefix='/platos')
    app.register_blueprint(menus_bp, url_prefix='/menus')
    app.register_blueprint(albaranes_bp, url_prefix='/albaranes')
    app.register_blueprint(importar_bp, url_prefix='/importar')
    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    app.register_blueprint(albaranes_masivos_bp, url_prefix='/albaranes-masivos')
    app.register_blueprint(cuadro_mando_bp, url_prefix='/cuadro-mando')
    
    # Make config available in templates
    @app.context_processor
    def inject_config():
        return dict(config=app.config)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)