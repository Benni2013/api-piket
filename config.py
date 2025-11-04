"""
Konfigurasi Database untuk API Absen Piket
"""
import os

class Config:
    """Konfigurasi aplikasi"""
    
    # Secret key untuk Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Konfigurasi Database MySQL
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or ''
    DB_NAME = os.environ.get('DB_NAME') or 'absen_apm'
    DB_PORT = int(os.environ.get('DB_PORT') or 3306)
    
    # SQLAlchemy Database URI
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True untuk debug SQL queries
    
    # Konfigurasi FaceNet
    FACE_RECOGNITION_THRESHOLD = float(os.environ.get('FACE_THRESHOLD') or 0.7)
    
    # Folder untuk menyimpan gambar wajah
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'data', 'wajah'
    )
    
    # Maksimum ukuran file upload (dalam bytes) - 5MB
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    
    # Konfigurasi CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')


class DevelopmentConfig(Config):
    """Konfigurasi untuk development"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Konfigurasi untuk production"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


# Dictionary untuk memilih konfigurasi berdasarkan environment
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
