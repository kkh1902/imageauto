#!/usr/bin/env python3
"""
ImageAuto Flask Application
이미지 자동 처리를 위한 Flask 웹 애플리케이션
"""

import os
from app import create_app
from config import config

# 환경 설정
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[config_name])

if __name__ == '__main__':
    # 개발 서버 실행
    print(f"\n🚀 ImageAuto 서버가 시작되었습니다!")
    print(f"🌐 http://localhost:{app.config['PORT']} 에서 접속하세요\n")
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config.get('DEBUG', False)
    )
