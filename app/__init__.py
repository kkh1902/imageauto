from flask import Flask
import os
from config import Config
import logging

def create_app(config_class=Config):
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 업로드 폴더 생성
    upload_folders = [
        app.config['UPLOAD_FOLDER'],
        os.path.join(app.config['UPLOAD_FOLDER'], 'images'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'videos'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'edited')
    ]
    
    for folder in upload_folders:
        os.makedirs(folder, exist_ok=True)
    
    # Blueprint 등록
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
