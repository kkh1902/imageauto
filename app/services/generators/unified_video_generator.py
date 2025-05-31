import os
import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any

# 다양한 생성기 import
from .klingai_generator import KlingAIVideoGenerator
from .klingai_web_generator import KlingAIWebGenerator
from .placeholder_video_generator import PlaceholderVideoGenerator

logger = logging.getLogger(__name__)

class VideoGeneratorType(Enum):
    """비디오 생성기 타입 열거형"""
    KLINGAI_API = "klingai_api"           # KlingAI 공식 API
    KLINGAI_WEB = "klingai_web"           # KlingAI 웹사이트 (Playwright)
    PLACEHOLDER = "placeholder"           # 테스트용 플레이스홀더
    AUTO = "auto"                         # 자동 선택

class UnifiedVideoGenerator:
    """
    통합 비디오 생성기 - 여러 생성 방식을 지원
    """
    
    def __init__(self, generator_type: VideoGeneratorType = VideoGeneratorType.AUTO):
        self.generator_type = generator_type
        self.generators = {}
        self._initialize_generators()
        self._select_default_generator()
    
    def _initialize_generators(self):
        """사용 가능한 생성기들 초기화"""
        
        # 환경 변수 확인
        klingai_api_key = os.getenv('KLINGAI_API_KEY')
        klingai_secret_key = os.getenv('KLINGAI_SECRET_KEY')
        klingai_email = os.getenv('KLINGAI_EMAIL')
        klingai_password = os.getenv('KLINGAI_PASSWORD')
        
        # KlingAI API 생성기
        if klingai_api_key and klingai_secret_key:
            try:
                self.generators[VideoGeneratorType.KLINGAI_API] = KlingAIVideoGenerator()
                logger.info("✅ KlingAI API 생성기 초기화 완료")
            except Exception as e:
                logger.warning(f"KlingAI API 생성기 초기화 실패: {e}")
        
        # KlingAI 웹 생성기 (Playwright)
        if klingai_email and klingai_password:
            try:
                self.generators[VideoGeneratorType.KLINGAI_WEB] = KlingAIWebGenerator()
                logger.info("✅ KlingAI 웹 생성기 초기화 완료")
            except Exception as e:
                logger.warning(f"KlingAI 웹 생성기 초기화 실패: {e}")
        
        # 플레이스홀더 생성기 (항상 사용 가능)
        try:
            self.generators[VideoGeneratorType.PLACEHOLDER] = PlaceholderVideoGenerator()
            logger.info("✅ 플레이스홀더 생성기 초기화 완료")
        except Exception as e:
            logger.error(f"플레이스홀더 생성기 초기화 실패: {e}")
    
    def _select_default_generator(self):
        """기본 생성기 선택"""
        
        # 환경 변수로 강제 지정
        force_generator = os.getenv('VIDEO_GENERATOR_TYPE', '').lower()
        if force_generator == 'api' and VideoGeneratorType.KLINGAI_API in self.generators:
            self.default_generator = VideoGeneratorType.KLINGAI_API
            logger.info("🎯 강제 지정: KlingAI API 생성기 사용")
            return
        elif force_generator == 'web' and VideoGeneratorType.KLINGAI_WEB in self.generators:
            self.default_generator = VideoGeneratorType.KLINGAI_WEB
            logger.info("🎯 강제 지정: KlingAI 웹 생성기 사용")
            return
        elif force_generator == 'placeholder':
            self.default_generator = VideoGeneratorType.PLACEHOLDER
            logger.info("🎯 강제 지정: 플레이스홀더 생성기 사용")
            return
        
        # 자동 선택 로직
        if self.generator_type == VideoGeneratorType.AUTO:
            # 1순위: KlingAI API (가장 안정적)
            if VideoGeneratorType.KLINGAI_API in self.generators:
                self.default_generator = VideoGeneratorType.KLINGAI_API
                logger.info("🔄 자동 선택: KlingAI API 생성기")
            
            # 2순위: KlingAI 웹 (API 실패 시 대안)
            elif VideoGeneratorType.KLINGAI_WEB in self.generators:
                self.default_generator = VideoGeneratorType.KLINGAI_WEB
                logger.info("🔄 자동 선택: KlingAI 웹 생성기")
            
            # 3순위: 플레이스홀더 (최후 수단)
            else:
                self.default_generator = VideoGeneratorType.PLACEHOLDER
                logger.info("🔄 자동 선택: 플레이스홀더 생성기")
        else:
            self.default_generator = self.generator_type
    
    async def generate_video(self, 
                           image_path: str, 
                           prompt: str, 
                           negative_prompt: str = "", 
                           cfg_scale: float = 0.5, 
                           mode: str = "std", 
                           duration: int = 5,
                           output_count: int = 1,
                           generator_type: Optional[VideoGeneratorType] = None,
                           fallback: bool = True) -> Dict[str, Any]:
        """
        비디오 생성 (통합 인터페이스)
        
        Args:
            image_path: 입력 이미지 경로
            prompt: 비디오 생성 프롬프트
            negative_prompt: 네거티브 프롬프트
            cfg_scale: CFG 스케일
            mode: 생성 모드 (std/pro)
            duration: 비디오 길이 (초)
            output_count: 출력 개수 (1-4, 웹 생성기에서만 사용)
            generator_type: 사용할 생성기 타입 (None이면 기본값 사용)
            fallback: 실패 시 다른 생성기로 자동 전환 여부
            
        Returns:
            생성 결과 딕셔너리
        """
        
        # 사용할 생성기 결정
        target_generator = generator_type or self.default_generator
        
        # 생성기 사용 가능 여부 확인
        if target_generator not in self.generators:
            if fallback:
                logger.warning(f"{target_generator.value} 생성기를 사용할 수 없습니다. 대안 생성기를 찾는 중...")
                target_generator = self._find_alternative_generator(target_generator)
                if not target_generator:
                    return {
                        'status': 'error',
                        'error': '사용 가능한 비디오 생성기가 없습니다.'
                    }
            else:
                return {
                    'status': 'error',
                    'error': f'{target_generator.value} 생성기를 사용할 수 없습니다.'
                }
        
        generator = self.generators[target_generator]
        
        try:
            logger.info(f"🎬 {target_generator.value} 생성기로 비디오 생성 시작")
            logger.info(f"   이미지: {os.path.basename(image_path)}")
            logger.info(f"   프롬프트: {prompt[:100]}...")
            
            # 비디오 생성 실행
            result = await generator.generate_video(
                image_path=image_path,
                prompt=prompt,
                negative_prompt=negative_prompt,
                cfg_scale=cfg_scale,
                mode=mode,
                duration=duration,
                output_count=output_count
            )
            
            # 결과에 생성기 정보 추가
            if result.get('status') == 'success':
                result['generator_type'] = target_generator.value
                result['generator_name'] = self._get_generator_display_name(target_generator)
                logger.info(f"✅ {target_generator.value} 생성기로 비디오 생성 성공")
            else:
                logger.error(f"❌ {target_generator.value} 생성기 실패: {result.get('error')}")
                
                # 실패 시 대안 생성기 시도
                if fallback and target_generator != VideoGeneratorType.PLACEHOLDER:
                    logger.info("대안 생성기로 재시도...")
                    return await self._try_fallback_generation(
                        image_path, prompt, negative_prompt, cfg_scale, mode, duration, target_generator
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ {target_generator.value} 생성기 예외: {str(e)}")
            
            # 예외 발생 시 대안 생성기 시도
            if fallback and target_generator != VideoGeneratorType.PLACEHOLDER:
                logger.info("예외 발생으로 인한 대안 생성기 시도...")
                return await self._try_fallback_generation(
                    image_path, prompt, negative_prompt, cfg_scale, mode, duration, target_generator
                )
            
            return {
                'status': 'error',
                'error': f'{target_generator.value} 생성기 오류: {str(e)}'
            }
    
    async def _try_fallback_generation(self, image_path, prompt, negative_prompt, cfg_scale, mode, duration, failed_generator):
        """대안 생성기로 재시도"""
        
        # 대안 생성기 우선순위
        fallback_order = []
        
        if failed_generator == VideoGeneratorType.KLINGAI_API:
            fallback_order = [VideoGeneratorType.KLINGAI_WEB, VideoGeneratorType.PLACEHOLDER]
        elif failed_generator == VideoGeneratorType.KLINGAI_WEB:
            fallback_order = [VideoGeneratorType.KLINGAI_API, VideoGeneratorType.PLACEHOLDER]
        else:
            fallback_order = [VideoGeneratorType.PLACEHOLDER]
        
        for fallback_type in fallback_order:
            if fallback_type in self.generators:
                logger.info(f"🔄 대안 생성기 시도: {fallback_type.value}")
                
                try:
                    result = await self.generators[fallback_type].generate_video(
                        image_path=image_path,
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        cfg_scale=cfg_scale,
                        mode=mode,
                        duration=duration,
                        output_count=1
                    )
                    
                    if result.get('status') == 'success':
                        result['generator_type'] = fallback_type.value
                        result['generator_name'] = self._get_generator_display_name(fallback_type)
                        result['fallback_from'] = failed_generator.value
                        logger.info(f"✅ 대안 생성기 {fallback_type.value} 성공")
                        return result
                        
                except Exception as e:
                    logger.warning(f"대안 생성기 {fallback_type.value} 실패: {str(e)}")
                    continue
        
        return {
            'status': 'error',
            'error': '모든 생성기가 실패했습니다.'
        }
    
    def _find_alternative_generator(self, target_generator):
        """대안 생성기 찾기"""
        alternatives = [
            VideoGeneratorType.KLINGAI_API,
            VideoGeneratorType.KLINGAI_WEB,
            VideoGeneratorType.PLACEHOLDER
        ]
        
        for alt in alternatives:
            if alt != target_generator and alt in self.generators:
                return alt
        
        return None
    
    def _get_generator_display_name(self, generator_type):
        """생성기 표시 이름"""
        names = {
            VideoGeneratorType.KLINGAI_API: "KlingAI API",
            VideoGeneratorType.KLINGAI_WEB: "KlingAI Web (Playwright)",
            VideoGeneratorType.PLACEHOLDER: "Test Placeholder"
        }
        return names.get(generator_type, generator_type.value)
    
    def get_available_generators(self):
        """사용 가능한 생성기 목록"""
        return [
            {
                'type': gen_type.value,
                'name': self._get_generator_display_name(gen_type),
                'available': True
            }
            for gen_type in self.generators.keys()
        ]
    
    def get_status_report(self):
        """생성기 상태 보고서"""
        report = {
            'default_generator': self.default_generator.value,
            'available_generators': len(self.generators),
            'generators': {}
        }
        
        for gen_type, generator in self.generators.items():
            report['generators'][gen_type.value] = {
                'name': self._get_generator_display_name(gen_type),
                'class': generator.__class__.__name__,
                'available': True
            }
        
        return report
