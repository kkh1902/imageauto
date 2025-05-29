"""
데이터 모델들

향후 데이터베이스를 사용할 때 이 폴더에 모델들을 정의합니다.
예: SQLAlchemy 모델, Pydantic 모델 등

예시:
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ImageRecord(Base):
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    upload_time = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
"""

# 현재는 파일 기반으로 작동하므로 모델이 필요하지 않습니다.
# 추후 데이터베이스 연동시 여기에 모델들을 추가하세요.
