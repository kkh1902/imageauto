from flask import Blueprint, request, jsonify, current_app, send_file
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.services.media_service import MediaService
    media_service_available = True
except Exception as e:
    print(f"MediaService import 오류: {e}")
    media_service_available = False
    
from app.services.file_service import FileService
import asyncio
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

if media_service_available:
    media_service = MediaService()
else:
    media_service = None

# 비동기 작업을 위한 헬퍼 함수
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@api_bp.route('/generate/image', methods=['POST'])
def generate_image():
    """이미지 생성 API"""
    try:
        if not media_service_available or media_service is None:
            return jsonify({'error': 'MediaService를 사용할 수 없습니다. 서버 로그를 확인하세요.'}), 500
            
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': '프롬프트가 필요합니다.'}), 400
        
        prompt = data['prompt']
        aspect_ratio = data.get('aspect_ratio', '9:16')
        
        current_app.logger.info(f"이미지 생성 요청: prompt='{prompt}', aspect_ratio='{aspect_ratio}'")
        
        # 이미지 생성 (비동기)
        result = run_async(media_service.generate_image(prompt, aspect_ratio))
        
        if result['status'] == 'success':
            # 파일 경로 검증
            filepath = result['filepath']
            if not os.path.exists(filepath):
                current_app.logger.error(f"생성된 이미지 파일이 존재하지 않음: {filepath}")
                return jsonify({'error': '이미지 파일을 찾을 수 없습니다.'}), 500
            
            # 상대 경로로 변환 (웹에서 접근 가능하도록)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            relative_path = os.path.relpath(filepath, upload_folder)
            web_path = relative_path.replace('\\', '/')  # Windows 경로 호환성
            
            current_app.logger.info(f"이미지 생성 성공: {result['filename']}")
            current_app.logger.info(f"파일 경로: {filepath}")
            current_app.logger.info(f"웹 경로: {web_path}")
            
            return jsonify({
                'success': True,
                'message': '이미지 생성이 완료되었습니다.',
                'filename': result['filename'],
                'filepath': result['filepath'],
                'web_path': f'/uploads/{web_path}',  # 웹에서 접근 가능한 경로
                'prompt': result['prompt'],
                'aspect_ratio': result['aspect_ratio'],
                'file_size': result.get('file_size', 0)
            })
        else:
            current_app.logger.error(f"이미지 생성 실패: {result['error']}")
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        current_app.logger.error(f"이미지 생성 오류: {str(e)}")
        return jsonify({'error': '이미지 생성 중 오류가 발생했습니다.'}), 500

@api_bp.route('/generate/video', methods=['POST'])
def generate_video():
    """동영상 생성 API"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '데이터가 필요합니다.'}), 400
        
        generation_type = data.get('type', 'text-to-video')
        
        if generation_type == 'text-to-video':
            return handle_text_to_video(data)
        elif generation_type == 'image-to-video':
            return handle_image_to_video(data)
        elif generation_type == 'template':
            return handle_template_video(data)
        else:
            return jsonify({'error': '지원하지 않는 생성 타입입니다.'}), 400
            
    except Exception as e:
        current_app.logger.error(f"동영상 생성 오류: {str(e)}")
        return jsonify({'error': '동영상 생성 중 오류가 발생했습니다.'}), 500

def handle_text_to_video(data):
    """텍스트로 동영상 생성 처리"""
    if 'prompt' not in data:
        return jsonify({'error': '프롬프트가 필요합니다.'}), 400
    
    prompt = data['prompt']
    duration = data.get('duration', '5')
    aspect_ratio = data.get('aspectRatio', '16:9')
    style = data.get('style', 'realistic')
    cfg_scale = data.get('cfgScale', '7.5')
    seed = data.get('seed')
    negative_prompt = data.get('negativePrompt', '')
    
    current_app.logger.info(f"텍스트로 동영상 생성: {prompt}")
    
    # 동영상 생성 시뮬레이션 (실제로는 AI 모델 호출)
    import time
    import uuid
    time.sleep(2)  # 시뮬레이션
    
    # 더미 결과 생성
    filename = f"text_video_{uuid.uuid4().hex[:8]}.mp4"
    
    return jsonify({
        'success': True,
        'message': '텍스트 동영상이 생성되었습니다.',
        'id': str(uuid.uuid4()),
        'filename': filename,
        'title': f"텍스트 동영상: {prompt[:30]}...",
        'duration': duration,
        'prompt': prompt,
        'views': 0,
        'likes': 0
    })

def handle_image_to_video(data):
    """이미지로 동영상 생성 처리"""
    if 'imagePath' not in data:
        return jsonify({'error': '이미지 경로가 필요합니다.'}), 400
    
    image_path = data['imagePath']
    motion_type = data.get('motionType', '전체 확대/축소')
    duration = data.get('duration', '5')
    aspect_ratio = data.get('aspectRatio', '16:9')
    style = data.get('style', 'realistic')
    
    current_app.logger.info(f"이미지로 동영상 생성: {image_path}")
    
    # 동영상 생성 시뮬레이션
    import time
    import uuid
    time.sleep(3)  # 시뮬레이션
    
    filename = f"image_video_{uuid.uuid4().hex[:8]}.mp4"
    
    return jsonify({
        'success': True,
        'message': '이미지 동영상이 생성되었습니다.',
        'id': str(uuid.uuid4()),
        'filename': filename,
        'title': f"이미지 동영상: {motion_type}",
        'duration': duration,
        'motion_type': motion_type,
        'views': 0,
        'likes': 0
    })

def handle_template_video(data):
    """템플릿으로 동영상 생성 처리"""
    if 'template' not in data:
        return jsonify({'error': '템플릿이 필요합니다.'}), 400
    
    template = data['template']
    
    current_app.logger.info(f"템플릿으로 동영상 생성: {template}")
    
    # 동영상 생성 시뮬레이션
    import time
    import uuid
    time.sleep(2)  # 시뮬레이션
    
    filename = f"template_video_{uuid.uuid4().hex[:8]}.mp4"
    
    # 템플릿에 따른 기본 설정
    template_settings = {
        '기업 소개 영상': {'duration': '30', 'aspect': '16:9'},
        '인스타그램 릴스': {'duration': '15', 'aspect': '9:16'},
        '제품 광고': {'duration': '20', 'aspect': '1:1'},
        '교육 콘텐츠': {'duration': '60', 'aspect': '16:9'}
    }
    
    settings = template_settings.get(template, {'duration': '30', 'aspect': '16:9'})
    
    return jsonify({
        'success': True,
        'message': '템플릿 동영상이 생성되었습니다.',
        'id': str(uuid.uuid4()),
        'filename': filename,
        'title': f"템플릿: {template}",
        'duration': settings['duration'],
        'template': template,
        'views': 0,
        'likes': 0
    })

@api_bp.route('/edit/video', methods=['POST'])
def edit_video():
    """동영상 편집 API"""
    try:
        data = request.get_json()
        
        if not data or 'video_path' not in data or 'edit_options' not in data:
            return jsonify({'error': '동영상 경로와 편집 옵션이 필요합니다.'}), 400
        
        video_path = data['video_path']
        edit_options = data['edit_options']
        
        # 동영상 편집
        result = media_service.edit_video(video_path, edit_options)
        
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': '동영상 편집이 완료되었습니다.',
                'filename': result['filename'],
                'filepath': result['filepath'],
                **result
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        current_app.logger.error(f"동영상 편집 오류: {str(e)}")
        return jsonify({'error': '동영상 편집 중 오류가 발생했습니다.'}), 500

@api_bp.route('/workflow/complete', methods=['POST'])
def complete_workflow():
    """전체 워크플로우 실행 API"""
    try:
        data = request.get_json()
        
        required_fields = ['image_prompt', 'video_prompt']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field}가 필요합니다.'}), 400
        
        image_prompt = data['image_prompt']
        video_prompt = data['video_prompt']
        video_options = data.get('video_options', {})
        edit_options = data.get('edit_options', None)
        
        # 전체 워크플로우 실행 (비동기)
        result = run_async(media_service.complete_workflow(
            image_prompt, video_prompt, video_options, edit_options
        ))
        
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': '워크플로우가 완료되었습니다.',
                'result': result
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        current_app.logger.error(f"워크플로우 실행 오류: {str(e)}")
        return jsonify({'error': '워크플로우 실행 중 오류가 발생했습니다.'}), 500

@api_bp.route('/media/list', methods=['GET'])
def list_media():
    """미디어 파일 목록 조회"""
    try:
        media_type = request.args.get('type', 'all')
        
        media_files = {
            'images': [],
            'videos': [],
            'edited': []
        }
        
        # 이미지 목록
        if media_type in ['all', 'images']:
            image_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'images')
            if os.path.exists(image_dir):
                media_files['images'] = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        # 동영상 목록
        if media_type in ['all', 'videos']:
            video_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos')
            if os.path.exists(video_dir):
                media_files['videos'] = [f for f in os.listdir(video_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
        
        # 편집된 파일 목록
        if media_type in ['all', 'edited']:
            edited_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'edited')
            if os.path.exists(edited_dir):
                media_files['edited'] = [f for f in os.listdir(edited_dir)]
        
        return jsonify({
            'success': True,
            'media': media_files,
            'count': sum(len(files) for files in media_files.values())
        })
        
    except Exception as e:
        current_app.logger.error(f"미디어 목록 조회 오류: {str(e)}")
        return jsonify({'error': '미디어 목록을 가져올 수 없습니다.'}), 500

@api_bp.route('/media/download/<path:filepath>', methods=['GET'])
def download_media(filepath):
    """미디어 파일 다운로드"""
    try:
        # 보안을 위해 경로 검증
        safe_path = os.path.normpath(filepath)
        if '..' in safe_path:
            return jsonify({'error': '잘못된 경로입니다.'}), 400
        
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_path)
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_file(full_path, as_attachment=True)
        else:
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
            
    except Exception as e:
        current_app.logger.error(f"파일 다운로드 오류: {str(e)}")
        return jsonify({'error': '파일 다운로드 중 오류가 발생했습니다.'}), 500
