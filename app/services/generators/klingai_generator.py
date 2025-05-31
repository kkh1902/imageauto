import os
import aiohttp
import asyncio
import json
import logging
from datetime import datetime
import time
import base64

# PyJWT를 안전하게 import
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("⚠️ PyJWT가 설치되지 않았습니다. 'pip install PyJWT==2.8.0' 명령어로 설치해주세요.")

logger = logging.getLogger(__name__)

class KlingAIVideoGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('KLINGAI_API_KEY')
        self.secret_key = os.getenv('KLINGAI_SECRET_KEY')
        
        # 디버깅: API 키 로드 상태 확인
        print(f"\n=== KlingAI API 키 디버깅 ===")
        print(f"Access Key: {self.api_key}")
        print(f"Secret Key: {self.secret_key}")
        print(f"Access Key 길이: {len(self.api_key) if self.api_key else 0}")
        print(f"Secret Key 길이: {len(self.secret_key) if self.secret_key else 0}")
        print(f"==================================\n")
        
        # 공식 API 엔드포인트 (문서 기준)
        self.base_url = "https://api-singapore.klingai.com"
        self.download_dir = os.path.join(os.path.dirname(__file__), '../../../../uploads/videos')
        os.makedirs(self.download_dir, exist_ok=True)
        
    def _generate_jwt_token(self):
        """
        KlingAI JWT 토큰 생성 (공식 문서 기준)
        """
        if not JWT_AVAILABLE:
            raise Exception("PyJWT 패키지가 설치되지 않았습니다. 'pip install PyJWT==2.8.0' 명령어로 설치해주세요.")
            
        if not self.api_key or not self.secret_key:
            raise Exception("Access Key와 Secret Key가 모두 필요합니다.")
        
        headers = {
            "alg": "HS256",
            "typ": "JWT"
        }
        
        current_time = int(time.time())
        payload = {
            "iss": self.api_key,  # Access Key as issuer
            "exp": current_time + 1800,  # 30분 후 만료
            "nbf": current_time - 5       # 5초 전부터 유효
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256', headers=headers)
        logger.info(f"JWT 토큰 생성 완료: {token[:20]}...")
        return token
        
    async def generate_video(self, image_path, prompt, negative_prompt="", cfg_scale=0.5, mode="std", duration=5):
        """
        KlingAI API를 사용하여 이미지에서 동영상을 생성합니다.
        
        Args:
            image_path (str): 입력 이미지 경로
            prompt (str): 동영상 생성 프롬프트
            negative_prompt (str): 네거티브 프롬프트
            cfg_scale (float): Flexibility (0.0-1.0)
            mode (str): 생성 모드 (std, pro)
            duration (int): 동영상 길이 (5 또는 10초)
            
        Returns:
            dict: 생성된 동영상 정보
        """
        if not self.api_key:
            return {
                'status': 'error',
                'error': 'KlingAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.'
            }
        
        if not self.secret_key:
            return {
                'status': 'error',
                'error': 'KlingAI Secret Key가 설정되지 않았습니다. .env 파일에 KLINGAI_SECRET_KEY를 추가해주세요.'
            }
        
        if not JWT_AVAILABLE:
            return {
                'status': 'error',
                'error': 'PyJWT 패키지가 설치되지 않았습니다. 명령프롬프트에서 "pip install PyJWT==2.8.0" 명령어로 설치해주세요.'
            }
        
        # JWT 토큰 생성
        try:
            jwt_token = self._generate_jwt_token()
        except Exception as e:
            return {
                'status': 'error',
                'error': f'JWT 토큰 생성 실패: {str(e)}'
            }
            
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"인증 방식: JWT 토큰")
        logger.info(f"API 엔드포인트: {self.base_url}")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 1. 이미지를 Base64로 인코딩
                logger.info("이미지 Base64 인코딩 중...")
                image_base64 = await self._encode_image_to_base64(image_path)
                if not image_base64:
                    raise Exception("이미지 인코딩 실패")
                
                # 2. 비디오 생성 작업 시작 (공식 문서 API 구조)
                logger.info("이미지에서 비디오 생성 작업 시작...")
                
                # 문서에 따른 정확한 요청 데이터 구조
                request_data = {
                    "model_name": "kling-v1",  # 기본 모델
                    "mode": mode,              # std 또는 pro
                    "duration": str(duration), # 문자열로 전달
                    "image": image_base64,     # Base64 인코딩된 이미지 (prefix 없이)
                    "prompt": prompt,          # 동영상 프롬프트
                    "cfg_scale": cfg_scale     # 유연성 설정
                }
                
                # 네거티브 프롬프트 추가 (있는 경우)
                if negative_prompt:
                    request_data["negative_prompt"] = negative_prompt
                
                logger.info(f"요청 데이터: {json.dumps({**request_data, 'image': 'base64_encoded_image...'}, indent=2)}")
                
                # 3. Image to Video API 호출 (공식 문서 엔드포인트)
                endpoint = f'{self.base_url}/v1/videos/image2video'
                logger.info(f"API 호출: {endpoint}")
                
                async with session.post(
                    endpoint,
                    headers=headers,
                    json=request_data
                ) as response:
                    response_text = await response.text()
                    logger.info(f"API 응답 상태: {response.status}")
                    logger.info(f"API 응답 헤더: {dict(response.headers)}")
                    logger.info(f"API 응답 내용: {response_text}")
                    
                    # 401 오류 시 상세 디버깅
                    if response.status == 401:
                        logger.error("=== 401 인증 실패 디버깅 ===")
                        logger.error(f"API 키 상태: {'있음' if self.api_key else '없음'}")
                        logger.error(f"Secret 키 상태: {'있음' if self.secret_key else '없음'}")
                        logger.error(f"JWT 토큰: {jwt_token[:30]}...")
                        logger.error("API 키가 올바르지 않거나 계정 문제일 수 있습니다.")
                        logger.error("1. KlingAI 계정에서 API 키 재확인")
                        logger.error("2. 계정 크레디트 잔액 확인")
                        logger.error("3. API 키 권한 확인")
                        logger.error("==================================")
                        
                        return {
                            'status': 'error',
                            'error': f'인증 실패 (401): API 키 또는 Secret Key가 올바르지 않습니다.',
                            'debug_info': {
                                'response_status': response.status,
                                'response_text': response_text,
                                'api_key_length': len(self.api_key) if self.api_key else 0,
                                'secret_key_length': len(self.secret_key) if self.secret_key else 0
                            }
                        }
                    
                    if response.status != 200:
                        error_detail = f"HTTP {response.status}: {response_text}"
                        logger.error(f"API 오류: {error_detail}")
                        return {
                            'status': 'error',
                            'error': f'API 호출 실패: {error_detail}',
                            'debug_info': {
                                'response_status': response.status,
                                'response_text': response_text
                            }
                        }
                    
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 파싱 오류: {e}")
                        return {
                            'status': 'error',
                            'error': f'API 응답 파싱 실패: {response_text}'
                        }
                    
                    if result.get('code') != 0:
                        error_msg = result.get('message', '알 수 없는 오류')
                        logger.error(f"API 오류 코드: {result.get('code')} - {error_msg}")
                        return {
                            'status': 'error',
                            'error': f'API 오류: {error_msg}',
                            'debug_info': result
                        }
                    
                    task_id = result['data']['task_id']
                    logger.info(f"비디오 생성 작업 시작됨 - Task ID: {task_id}")
                
                # 4. 생성 상태 확인 및 대기
                logger.info("비디오 생성 완료 대기 중...")
                video_data = await self._wait_for_completion(session, task_id, headers)
                
                if not video_data:
                    raise Exception("비디오 생성 실패")
                
                # 5. 동영상 다운로드
                logger.info(f"동영상 다운로드 중: {video_data['video_url']}")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"klingai_{timestamp}.mp4"
                filepath = os.path.join(self.download_dir, filename)
                
                async with session.get(video_data['video_url']) as video_response:
                    if video_response.status == 200:
                        with open(filepath, 'wb') as f:
                            async for chunk in video_response.content.iter_chunked(8192):
                                f.write(chunk)
                        logger.info(f"동영상 다운로드 완료: {filename}")
                    else:
                        raise Exception(f"동영상 다운로드 실패: {video_response.status}")
                
                logger.info(f"동영상 생성 완료: {filename}")
                
                return {
                    'status': 'success',
                    'filename': filename,
                    'filepath': filepath,
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'duration': duration,
                    'mode': mode,
                    'task_id': task_id,
                    'generator': 'klingai'
                }
                
            except Exception as e:
                logger.error(f"동영상 생성 중 오류 발생: {str(e)}")
                return {
                    'status': 'error',
                    'error': str(e)
                }
    
    async def _encode_image_to_base64(self, image_path):
        """
        이미지를 Base64로 인코딩합니다. (공식 문서 기준)
        
        Args:
            image_path: 인코딩할 이미지 경로
            
        Returns:
            str: Base64 인코딩된 이미지 데이터 (prefix 없이)
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                
            # 파일 크기 확인 (10MB 제한)
            file_size_mb = len(image_data) / (1024 * 1024)
            if file_size_mb > 10:
                raise Exception(f"이미지 파일 크기가 너무 큽니다: {file_size_mb:.2f}MB (최대 10MB)")
                
            # Base64 인코딩 (prefix 없이, 공식 문서 기준)
            base64_data = base64.b64encode(image_data).decode('utf-8')
            logger.info(f"이미지 Base64 인코딩 완료: {len(base64_data)} 문자, 파일 크기: {file_size_mb:.2f}MB")
            return base64_data
            
        except Exception as e:
            logger.error(f"이미지 Base64 인코딩 중 오류: {str(e)}")
            return None
    
    async def _wait_for_completion(self, session, task_id, headers, max_wait=600):
        """
        동영상 생성 완료를 기다립니다. (공식 문서 API 기준)
        
        Args:
            session: aiohttp 세션
            task_id: 작업 ID
            headers: HTTP 헤더
            max_wait: 최대 대기 시간 (초)
            
        Returns:
            dict: 생성된 동영상 정보
        """
        start_time = time.time()
        check_interval = 10  # 10초마다 확인
        
        # 공식 문서 기준 상태 확인 엔드포인트
        status_endpoint = f'{self.base_url}/v1/videos/image2video/{task_id}'
        
        while True:
            if time.time() - start_time > max_wait:
                raise TimeoutError(f"동영상 생성 시간 초과 ({max_wait}초)")
            
            try:
                logger.info(f"작업 상태 확인 중... (경과 시간: {int(time.time() - start_time)}초)")
                
                async with session.get(status_endpoint, headers=headers) as response:
                    response_text = await response.text()
                    logger.info(f"상태 확인 응답: {response.status}")
                    
                    if response.status != 200:
                        logger.warning(f"상태 확인 실패: {response.status} - {response_text}")
                        await asyncio.sleep(check_interval)
                        continue
                    
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"상태 확인 JSON 파싱 실패: {e} - {response_text}")
                        await asyncio.sleep(check_interval)
                        continue
                    
                    if result.get('code') != 0:
                        logger.warning(f"상태 확인 오류: {result.get('message')}")
                        await asyncio.sleep(check_interval)
                        continue
                    
                    task_data = result['data']
                    status = task_data.get('task_status')
                    
                    logger.info(f"작업 상태: {status}")
                    
                    if status == 'succeed':
                        # 성공 - 비디오 URL 추출 (공식 문서 응답 구조)
                        task_result = task_data.get('task_result', {})
                        videos = task_result.get('videos', [])
                        
                        if videos and len(videos) > 0:
                            video_info = videos[0]
                            video_url = video_info.get('url')
                            video_duration = video_info.get('duration', str(duration))
                            
                            if video_url:
                                logger.info(f"비디오 생성 성공! URL: {video_url}")
                                return {
                                    'video_url': video_url,
                                    'duration': video_duration,
                                    'video_id': video_info.get('id')
                                }
                        
                        # 비디오 URL을 찾을 수 없는 경우
                        logger.error(f"비디오 URL을 찾을 수 없습니다. task_result: {json.dumps(task_result, indent=2)}")
                        raise Exception("생성 완료되었지만 비디오 URL을 찾을 수 없습니다")
                        
                    elif status == 'failed':
                        error_msg = task_data.get('task_status_msg', '알 수 없는 오류')
                        logger.error(f"비디오 생성 실패: {error_msg}")
                        raise Exception(f"동영상 생성 실패: {error_msg}")
                    
                    elif status in ['submitted', 'processing']:
                        # 아직 처리 중
                        logger.info(f"처리 중... 상태: {status}")
                        await asyncio.sleep(check_interval)
                    
                    else:
                        # 알 수 없는 상태
                        logger.warning(f"알 수 없는 상태: {status}")
                        await asyncio.sleep(check_interval)
                        
            except Exception as e:
                logger.error(f"상태 확인 중 오류: {str(e)}")
                # 네트워크 오류 등은 재시도
                await asyncio.sleep(check_interval)
