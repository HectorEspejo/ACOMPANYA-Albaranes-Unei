from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from database import init_db, db
from routes import ingredientes_bp, platos_bp, menus_bp, albaranes_bp, importar_bp, clientes_bp
from routes.albaranes_masivos import albaranes_masivos_bp
from routes.cuadro_mando import cuadro_mando_bp
from database.models import Usuario

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    init_db(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Login route
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            nombre_usuario = request.form.get('nombre_usuario')
            password = request.form.get('password')
            
            usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
            
            if usuario and usuario.check_password(password):
                login_user(usuario)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                return render_template('login.html', error='Usuario o contraseña incorrectos')
        
        return render_template('login.html')
    
    # Logout route
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
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
    @login_required
    def index():
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error_code=404), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('error.html', error_code=403), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error_code=500), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)