from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
import os
from app.services.file_service import FileService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """메인 페이지 - 워크플로우"""
    return render_template('index.html')

@main_bp.route('/workflow')
def workflow():
    """워크플로우 페이지"""
    return render_template('workflow.html')

@main_bp.route('/image-generation')
def image_generation():
    """이미지 생성 페이지"""
    return render_template('image_generation.html')

@main_bp.route('/video-generation')
def video_generation():
    """동영상 생성 페이지 - 새로운 이쁜 디자인"""
    return render_template('video_generation.html')

@main_bp.route('/video-generation/text-to-video')
def text_to_video():
    """텍스트로 동영상 생성 페이지"""
    return render_template('video_generation.html', default_tab='text-to-video')

@main_bp.route('/video-generation/image-to-video')
def image_to_video():
    """이미지로 동영상 생성 페이지"""
    return render_template('video_generation.html', default_tab='image-to-video')

@main_bp.route('/video-generation/template')
def template_video():
    """템플릿으로 동영상 생성 페이지"""
    return render_template('video_generation.html', default_tab='template')

@main_bp.route('/video-editor')
def video_editor():
    """동영상 편집 페이지"""
    return render_template('video_editor.html')

@main_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """파일 업로드 처리"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if file and FileService.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # 파일 타입에 따라 적절한 폴더에 저장
            file_ext = filename.rsplit('.', 1)[1].lower()
            if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                subfolder = 'images'
            elif file_ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
                subfolder = 'videos'
            else:
                subfolder = ''
            
            file_path = FileService.save_file(file, filename, subfolder)
            
            return jsonify({
                'success': True,
                'message': '파일이 성공적으로 업로드되었습니다.',
                'filename': filename,
                'filepath': file_path
            })
        
        return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400
        
    except Exception as e:
        current_app.logger.error(f"파일 업로드 오류: {str(e)}")
        return jsonify({'error': '파일 업로드 중 오류가 발생했습니다.'}), 500

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """업로드된 파일 서빙 - 개선된 버전"""
    try:
        # 보안을 위해 경로 정규화
        safe_filename = os.path.normpath(filename)
        
        # 디렉토리 탐색 공격 방지
        if '..' in safe_filename or safe_filename.startswith('/'):
            current_app.logger.warning(f"의심스러운 파일 요청: {filename}")
            return jsonify({'error': '잘못된 경로입니다.'}), 403
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, safe_filename)
        
        # 파일 존재 확인
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            current_app.logger.warning(f"파일을 찾을 수 없음: {file_path}")
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
        
        # 파일의 디렉토리와 파일명 분리
        directory = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        
        current_app.logger.debug(f"파일 서빙: {filename}")
        return send_from_directory(directory, basename)
        
    except Exception as e:
        current_app.logger.error(f"파일 서빙 오류: {str(e)}")
        return jsonify({'error': '파일 서빙 중 오류가 발생했습니다.'}), 500

@main_bp.route('/health')
def health_check():
    """헬스 체크"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # 업로드 폴더 상태 확인
        folder_status = {
            'upload_folder_exists': os.path.exists(upload_folder),
            'images_folder_exists': os.path.exists(os.path.join(upload_folder, 'images')),
            'videos_folder_exists': os.path.exists(os.path.join(upload_folder, 'videos')),
            'edited_folder_exists': os.path.exists(os.path.join(upload_folder, 'edited'))
        }
        
        return jsonify({
            'status': 'healthy', 
            'message': 'ImageAuto Flask app is running!',
            'version': '2.0.0',
            'upload_folder': upload_folder,
            'folder_status': folder_status
        })
        
    except Exception as e:
        current_app.logger.error(f"헬스 체크 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'헬스 체크 실패: {str(e)}'
        }), 500

@main_bp.route('/debug/check-files')
def debug_check_files():
    """디버깅용 파일 체크"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        debug_info = {
            'upload_folder': upload_folder,
            'upload_folder_exists': os.path.exists(upload_folder),
            'subdirectories': {}
        }
        
        # 각 서브디렉토리 확인
        subdirs = ['images', 'videos', 'edited']
        for subdir in subdirs:
            subdir_path = os.path.join(upload_folder, subdir)
            debug_info['subdirectories'][subdir] = {
                'path': subdir_path,
                'exists': os.path.exists(subdir_path),
                'files': []
            }
            
            if os.path.exists(subdir_path):
                try:
                    files = os.listdir(subdir_path)
                    debug_info['subdirectories'][subdir]['files'] = files[:10]  # 최대 10개
                except Exception as e:
                    debug_info['subdirectories'][subdir]['files'] = [f'오류: {str(e)}']
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': f'디버깅 정보 조회 오류: {str(e)}'}), 500
