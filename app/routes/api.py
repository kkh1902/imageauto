from flask import Blueprint, request, jsonify, current_app, send_file
from app.services.media_service import MediaService
from app.services.file_service import FileService
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)
media_service = MediaService()

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
        
        required_fields = ['image_path', 'prompt']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field}가 필요합니다.'}), 400
        
        image_path = data['image_path']
        prompt = data['prompt']
        negative_prompt = data.get('negative_prompt', '')
        mode = data.get('mode', 'std')
        cfg_scale = data.get('cfg_scale', 0.5)
        duration = data.get('duration', 5)
        
        # 동영상 생성 (비동기)
        result = run_async(media_service.generate_video(
            image_path, prompt, negative_prompt, cfg_scale, mode, duration
        ))
        
        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': '동영상 생성이 완료되었습니다.',
                'filename': result['filename'],
                'filepath': result['filepath'],
                'prompt': result['prompt'],
                'duration': result['duration']
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        current_app.logger.error(f"동영상 생성 오류: {str(e)}")
        return jsonify({'error': '동영상 생성 중 오류가 발생했습니다.'}), 500

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
