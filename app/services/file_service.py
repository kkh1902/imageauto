import os
from flask import current_app
from werkzeug.utils import secure_filename

class FileService:
    """파일 관련 서비스"""
    
    @staticmethod
    def allowed_file(filename):
        """허용된 파일 확장자인지 확인"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    @staticmethod
    def save_file(file, filename=None, subfolder=''):
        """파일을 안전하게 저장"""
        if filename is None:
            filename = secure_filename(file.filename)
        else:
            filename = secure_filename(filename)
        
        # 서브폴더가 있으면 해당 폴더에 저장
        if subfolder:
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(upload_folder, exist_ok=True)
        else:
            upload_folder = current_app.config['UPLOAD_FOLDER']
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return file_path
    
    @staticmethod
    def file_exists(filename):
        """파일 존재 여부 확인"""
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        return os.path.exists(file_path)
    
    @staticmethod
    def get_file_path(filename):
        """파일의 전체 경로 반환"""
        return os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    @staticmethod
    def delete_file(filename):
        """파일 삭제"""
        file_path = FileService.get_file_path(filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    @staticmethod
    def list_uploaded_files():
        """업로드된 파일 목록 반환"""
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            return []
        
        files = []
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path) and FileService.allowed_file(filename):
                file_info = {
                    'filename': filename,
                    'size': os.path.getsize(file_path),
                    'modified_time': os.path.getmtime(file_path)
                }
                files.append(file_info)
        
        # 수정 시간 기준으로 정렬 (최신순)
        files.sort(key=lambda x: x['modified_time'], reverse=True)
        return files
    
    @staticmethod
    def get_file_size(filename):
        """파일 크기 반환 (바이트)"""
        file_path = FileService.get_file_path(filename)
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return None
    
    @staticmethod
    def format_file_size(size_bytes):
        """파일 크기를 읽기 쉬운 형태로 포맷"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
