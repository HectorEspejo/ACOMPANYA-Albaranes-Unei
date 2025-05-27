import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'database', 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # App specific config
    ITEMS_PER_PAGE = 20
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Stock alerts
    STOCK_ALERT_THRESHOLD = 10  # Alert when stock falls below this
    EXPIRY_ALERT_DAYS = 7  # Alert when expiry is within this many days
    
    # Debug mode - bypasses stock verification
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() in ['true', '1', 'yes']