from flask import Blueprint, request, jsonify, current_app, send_file
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MediaService를 더 안전하게 import
try:
    from app.services.media_service import MediaService
    media_service_available = True
    print("✅ MediaService import 성공")
except Exception as e:
    print(f"❌ MediaService import 오류: {e}")
    import traceback
    traceback.print_exc()
    media_service_available = False
    
from app.services.file_service import FileService
import asyncio
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# MediaService를 동적으로 초기화
media_service = None

def get_media_service():
    """MediaService를 동적으로 가져오거나 초기화"""
    global media_service
    
    if media_service is None and media_service_available:
        try:
            print("🔧 MediaService 초기화 시도...")
            print("🔍 환경 변수 확인:")
            print(f"   KLINGAI_EMAIL: {'설정됨' if os.getenv('KLINGAI_EMAIL') else '미설정'}")
            print(f"   KLINGAI_PASSWORD: {'설정됨' if os.getenv('KLINGAI_PASSWORD') else '미설정'}")
            print(f"   VIDEO_GENERATOR_TYPE: {os.getenv('VIDEO_GENERATOR_TYPE', 'auto')}")
            print(f"   USE_PLACEHOLDER_GENERATOR: {os.getenv('USE_PLACEHOLDER_GENERATOR', 'false')}")
            
            # Playwright 설치 확인
            try:
                from playwright.async_api import async_playwright
                print("✅ Playwright 모듈 import 성공")
            except ImportError as e:
                print(f"❌ Playwright 모듈 import 실패: {e}")
                print("   Playwright 설치 필요: pip install playwright")
                print("   브라우저 설치 필요: playwright install")
            
            media_service = MediaService()
            print(f"✅ MediaService 초기화 성공! 비디오 생성기: {type(media_service.video_generator).__name__}")
            
            # 생성기 상태 확인
            if hasattr(media_service, 'video_generator') and hasattr(media_service.video_generator, 'get_status_report'):
                status = media_service.video_generator.get_status_report()
                print(f"📊 생성기 상태: {status}")
            
        except Exception as e:
            print(f"❌ MediaService 초기화 실패: {e}")
            import traceback
            print("상세 에러:")
            traceback.print_exc()
            return None
    
    return media_service

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
        # MediaService 동적 로드
        media_service = get_media_service()
        
        if not media_service:
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
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negativePrompt', '')  # negative prompt 추가
    motion_type = data.get('motionType', 'zoom')
    duration = int(data.get('duration', '5'))
    
    # 웹 생성기 전용 옵션들
    mode = data.get('mode', 'pro')  # std 또는 pro
    output_count = int(data.get('outputCount', 1))  # 1, 2, 3, 4
    cfg_scale = float(data.get('cfgScale', 0.5))  # CFG 스케일
    
    # 생성기 타입 선택 (옵션)
    generator_type_str = data.get('generatorType')  # 'api', 'web', 'placeholder'
    generator_type = None
    
    if generator_type_str:
        try:
            from app.services.generators.unified_video_generator import VideoGeneratorType
            generator_map = {
                'api': VideoGeneratorType.KLINGAI_API,
                'web': VideoGeneratorType.KLINGAI_WEB,
                'placeholder': VideoGeneratorType.PLACEHOLDER
            }
            generator_type = generator_map.get(generator_type_str.lower())
        except ImportError as e:
            current_app.logger.error(f"VideoGeneratorType import 실패: {e}")
    
    # 이미지 경로를 실제 파일 시스템 경로로 변환
    if image_path.startswith('/uploads/'):
        # 웹 경로를 실제 파일 경로로 변환
        relative_path = image_path.replace('/uploads/', '')
        absolute_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path)
    else:
        absolute_image_path = image_path
    
    # 파일 존재 확인
    if not os.path.exists(absolute_image_path):
        return jsonify({'error': f'이미지 파일을 찾을 수 없습니다: {image_path}'}), 400
    
    current_app.logger.info(f"이미지로 동영상 생성: {absolute_image_path}")
    current_app.logger.info(f"프롬프트: {prompt}")
    if negative_prompt:
        current_app.logger.info(f"네거티브 프롬프트: {negative_prompt}")
    current_app.logger.info(f"모션 타입: {motion_type}")
    current_app.logger.info(f"길이: {duration}초")
    if generator_type:
        current_app.logger.info(f"지정된 생성기: {generator_type_str}")
    
    # MediaService를 동적으로 초기화
    print("🔧 MediaService 가져오는 중...")
    media_service = get_media_service()
    
    if not media_service:
        current_app.logger.error("🚨 MediaService를 사용할 수 없습니다!")
        return jsonify({'error': 'MediaService를 사용할 수 없습니다. 환경 설정이나 의존성을 확인하세요.'}), 500
    
    try:
        current_app.logger.info(f"🎬 통합 비디오 생성기로 동영상 생성 시작!")
        
        # 통합 비디오 생성기를 사용하여 실제 동영상 생성
        result = run_async(media_service.video_generator.generate_video(
            image_path=absolute_image_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            duration=duration,
            cfg_scale=cfg_scale,
            mode=mode,
            output_count=output_count,  # 웹 생성기에서만 사용
            generator_type=generator_type,  # 지정된 생성기 타입
            fallback=True  # 실패 시 다른 생성기로 자동 전환
        ))
        
        if result['status'] == 'success':
            # 웹에서 접근 가능한 경로로 변환
            upload_folder = current_app.config['UPLOAD_FOLDER']
            relative_path = os.path.relpath(result['filepath'], upload_folder)
            web_path = relative_path.replace('\\', '/')
            
            generator_name = result.get('generator_name', result.get('generator_type', 'Unknown'))
            current_app.logger.info(f"✅ {generator_name} 동영상 생성 성공: {result['filename']}")
            
            response_data = {
                'success': True,
                'message': f'{generator_name}로 이미지 동영상이 생성되었습니다.',
                'id': result.get('task_id', str(__import__('uuid').uuid4())),
                'filename': result['filename'],
                'filepath': result['filepath'],
                'web_path': f'/uploads/{web_path}',
                'title': f"이미지 동영상: {prompt[:30]}...",
                'duration': duration,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'motion_type': motion_type,
                'views': 0,
                'likes': 0,
                'generator_type': result.get('generator_type'),
                'generator_name': generator_name
            }
            
            # 대안 생성기 사용되었을 경우 메시지 업데이트
            if 'fallback_from' in result:
                response_data['message'] += f" (초기 생성기 실패로 {result['fallback_from']}에서 전환됨)"
                response_data['fallback_info'] = {
                    'original_generator': result['fallback_from'],
                    'used_generator': result['generator_type']
                }
            
            return jsonify(response_data)
        else:
            current_app.logger.error(f"❌ 비디오 생성 실패: {result['error']}")
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        current_app.logger.error(f"❌ 동영상 생성 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'동영상 생성 중 오류가 발생했습니다: {str(e)}'}), 500

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
                image_files = []
                for f in os.listdir(image_dir):
                    if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')) and not f.startswith('.'):
                        filepath = os.path.join(image_dir, f)
                        try:
                            stat = os.stat(filepath)
                            image_files.append({
                                'filename': f,
                                'size': stat.st_size,
                                'modified': stat.st_mtime,
                                'url': f'/uploads/images/{f}'
                            })
                        except Exception:
                            continue
                # 수정 시간 기준으로 최신 순 정렬
                image_files.sort(key=lambda x: x['modified'], reverse=True)
                media_files['images'] = image_files
        
        # 동영상 목록
        if media_type in ['all', 'videos']:
            video_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos')
            if os.path.exists(video_dir):
                video_files = []
                for f in os.listdir(video_dir):
                    if f.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')) and not f.startswith('.'):
                        filepath = os.path.join(video_dir, f)
                        try:
                            stat = os.stat(filepath)
                            video_files.append({
                                'filename': f,
                                'size': stat.st_size,
                                'modified': stat.st_mtime,
                                'url': f'/uploads/videos/{f}'
                            })
                        except Exception:
                            continue
                # 수정 시간 기준으로 최신 순 정렬
                video_files.sort(key=lambda x: x['modified'], reverse=True)
                media_files['videos'] = video_files
        
        # 편집된 파일 목록
        if media_type in ['all', 'edited']:
            edited_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'edited')
            if os.path.exists(edited_dir):
                edited_files = []
                for f in os.listdir(edited_dir):
                    if not f.startswith('.'):
                        filepath = os.path.join(edited_dir, f)
                        try:
                            stat = os.stat(filepath)
                            edited_files.append({
                                'filename': f,
                                'size': stat.st_size,
                                'modified': stat.st_mtime,
                                'url': f'/uploads/edited/{f}'
                            })
                        except Exception:
                            continue
                # 수정 시간 기준으로 최신 순 정렬
                edited_files.sort(key=lambda x: x['modified'], reverse=True)
                media_files['edited'] = edited_files
        
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

@api_bp.route('/video/generators/status', methods=['GET'])
def get_video_generators_status():
    """비디오 생성기 상태 확인 API"""
    try:
        media_service = get_media_service()
        
        if not media_service:
            return jsonify({'error': 'MediaService를 사용할 수 없습니다.'}), 500
        
        # 생성기 상태 보고서 가져오기
        status_report = media_service.video_generator.get_status_report()
        available_generators = media_service.video_generator.get_available_generators()
        
        # 환경 변수 정보
        env_info = {
            'klingai_api_configured': bool(os.getenv('KLINGAI_API_KEY') and os.getenv('KLINGAI_SECRET_KEY')),
            'klingai_web_configured': bool(os.getenv('KLINGAI_EMAIL') and os.getenv('KLINGAI_PASSWORD')),
            'video_generator_type': os.getenv('VIDEO_GENERATOR_TYPE', 'auto'),
            'use_placeholder': os.getenv('USE_PLACEHOLDER_GENERATOR', 'false').lower() == 'true'
        }
        
        return jsonify({
            'success': True,
            'status_report': status_report,
            'available_generators': available_generators,
            'environment': env_info,
            'recommendations': _get_generator_recommendations(env_info, available_generators)
        })
        
    except Exception as e:
        current_app.logger.error(f"비디오 생성기 상태 확인 오류: {str(e)}")
        return jsonify({'error': '상태 확인 중 오류가 발생했습니다.'}), 500

def _get_generator_recommendations(env_info, available_generators):
    """생성기 설정 추천사항"""
    recommendations = []
    
    # API 키 설정 확인
    if not env_info['klingai_api_configured']:
        recommendations.append({
            'type': 'warning',
            'title': 'KlingAI API 키 미설정',
            'message': '.env 파일에 KLINGAI_API_KEY와 KLINGAI_SECRET_KEY를 설정하면 고품질 API 비디오 생성을 사용할 수 있습니다.',
            'action': 'KlingAI 개발자 페이지에서 API 키 발급'
        })
    
    # 웹 로그인 정보 설정 확인
    if not env_info['klingai_web_configured']:
        recommendations.append({
            'type': 'info',
            'title': 'KlingAI 웹 자동화 미설정',
            'message': '.env 파일에 KLINGAI_EMAIL과 KLINGAI_PASSWORD를 설정하면 웹사이트 자동화로 비디오를 생성할 수 있습니다.',
            'action': 'KlingAI 계정 로그인 정보 설정'
        })
    
    # 사용 가능한 생성기 개수에 따른 추천
    generator_count = len(available_generators)
    if generator_count == 1 and available_generators[0]['type'] == 'placeholder':
        recommendations.append({
            'type': 'warning',
            'title': '테스트 모드만 사용 가능',
            'message': '현재 플레이스홀더 생성기만 사용 가능합니다. 실제 비디오 생성을 위해 API 키 또는 웹 로그인 정보를 설정해주세요.',
            'action': 'KlingAI 인증 정보 설정'
        })
    elif generator_count >= 2:
        recommendations.append({
            'type': 'success',
            'title': '다중 생성기 사용 가능',
            'message': f'{generator_count}개의 비디오 생성기가 사용 가능합니다. 자동 전환 기능으로 더 안정적인 서비스를 제공합니다.',
            'action': '현재 설정 유지 추천'
        })
    
    return recommendations
