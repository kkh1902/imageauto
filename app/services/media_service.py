import os
import asyncio
from .generators.imagefx_generator import ImageFXGenerator
from .generators.placeholder_generator import PlaceholderGenerator
from .generators.unified_video_generator import UnifiedVideoGenerator, VideoGeneratorType
from .video_editor import VideoEditor
import logging

logger = logging.getLogger(__name__)

class MediaService:
    def __init__(self):
        # 환경변수로 이미지 생성기 선택
        use_placeholder = os.environ.get('USE_PLACEHOLDER_GENERATOR', 'false').lower() == 'true'
        
        if use_placeholder:
            logger.info("플레이스홀더 이미지 생성기를 사용합니다.")
            self.image_generator = PlaceholderGenerator()
        else:
            logger.info("ImageFX 생성기를 사용합니다.")
            self.image_generator = ImageFXGenerator()
        
        # 통합 비디오 생성기 사용
        logger.info("🎬 통합 비디오 생성기 초기화 중...")
        
        # 비디오 생성기 타입 설정
        generator_type_env = os.environ.get('VIDEO_GENERATOR_TYPE', 'auto').lower()
        if generator_type_env == 'api':
            generator_type = VideoGeneratorType.KLINGAI_API
        elif generator_type_env == 'web':
            generator_type = VideoGeneratorType.KLINGAI_WEB
        elif generator_type_env == 'placeholder':
            generator_type = VideoGeneratorType.PLACEHOLDER
        else:
            generator_type = VideoGeneratorType.AUTO
        
        self.video_generator = UnifiedVideoGenerator(generator_type)
        
        # 상태 보고서 출력
        status_report = self.video_generator.get_status_report()
        logger.info(f"✅ 통합 비디오 생성기 초기화 완료")
        logger.info(f"   기본 생성기: {status_report['default_generator']}")
        logger.info(f"   사용 가능한 생성기: {status_report['available_generators']}개")
        
        for gen_name, gen_info in status_report['generators'].items():
            logger.info(f"   - {gen_info['name']} ({gen_name})")
            
        self.video_editor = VideoEditor()
        
    async def generate_image(self, prompt, aspect_ratio="9:16"):
        """이미지 생성"""
        return await self.image_generator.generate_image(prompt, aspect_ratio)
    
    async def generate_video(self, image_path, prompt, negative_prompt="", cfg_scale=0.5, mode="std", duration=5):
        """동영상 생성"""
        return await self.video_generator.generate_video(
            image_path, prompt, negative_prompt, cfg_scale, mode, duration
        )
    
    def edit_video(self, video_path, edit_options):
        """
        동영상 편집
        
        Args:
            video_path (str): 편집할 동영상 경로
            edit_options (dict): 편집 옵션
                - action: 'add_subtitles', 'trim', 'merge', 'add_watermark'
                - params: 각 액션에 필요한 파라미터
        
        Returns:
            dict: 편집 결과
        """
        action = edit_options.get('action')
        params = edit_options.get('params', {})
        
        if action == 'add_subtitles':
            return self.video_editor.add_subtitles(video_path, **params)
        elif action == 'trim':
            return self.video_editor.trim_video(video_path, **params)
        elif action == 'merge':
            return self.video_editor.merge_videos([video_path] + params.get('additional_videos', []))
        elif action == 'add_watermark':
            return self.video_editor.add_watermark(video_path, **params)
        else:
            return {
                'status': 'error',
                'error': f'알 수 없는 편집 작업: {action}'
            }
    
    async def complete_workflow(self, prompt, video_prompt, video_options=None, edit_options=None):
        """
        전체 워크플로우 실행 (이미지 생성 -> 동영상 생성 -> 편집)
        
        Args:
            prompt (str): 이미지 생성 프롬프트
            video_prompt (str): 동영상 생성 프롬프트
            video_options (dict): 동영상 생성 옵션
            edit_options (dict): 편집 옵션
            
        Returns:
            dict: 전체 워크플로우 결과
        """
        try:
            # 1. 이미지 생성
            logger.info("이미지 생성 시작...")
            image_result = await self.generate_image(prompt)
            if image_result['status'] != 'success':
                return image_result
            
            # 2. 동영상 생성
            logger.info("동영상 생성 시작...")
            video_options = video_options or {}
            video_result = await self.generate_video(
                image_result['filepath'],
                video_prompt,
                **video_options
            )
            if video_result['status'] != 'success':
                return video_result
            
            # 3. 동영상 편집 (옵션)
            if edit_options:
                logger.info("동영상 편집 시작...")
                edit_result = self.edit_video(video_result['filepath'], edit_options)
                if edit_result['status'] != 'success':
                    return edit_result
                
                return {
                    'status': 'success',
                    'image': image_result,
                    'video': video_result,
                    'edited_video': edit_result
                }
            
            return {
                'status': 'success',
                'image': image_result,
                'video': video_result
            }
            
        except Exception as e:
            logger.error(f"워크플로우 실행 중 오류: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
