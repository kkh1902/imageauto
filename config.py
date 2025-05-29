import os
from datetime import timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """기본 설정"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 파일 업로드 설정
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 104857600))  # 100MB 기본값
    
    # 허용된 파일 확장자
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    # 세션 설정
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # API 키
    KLINGAI_API_KEY = os.environ.get('KLINGAI_API_KEY')
    
    # Playwright 설정
    HEADLESS_BROWSER = os.environ.get('HEADLESS_BROWSER', 'false').lower() == 'true'
    
    # FFmpeg 경로
    FFMPEG_PATH = os.environ.get('FFMPEG_PATH', 'ffmpeg')
    
    # 서버 설정
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    FLASK_ENV = 'production'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    WTF_CSRF_ENABLED = False

# 설정 선택을 위한 딕셔너리
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
