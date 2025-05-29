import os
import aiohttp
import asyncio
import json
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class KlingAIVideoGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('KLINGAI_API_KEY')
        self.base_url = "https://api.klingai.com/v1"
        self.download_dir = os.path.join(os.path.dirname(__file__), '../../../../uploads/videos')
        os.makedirs(self.download_dir, exist_ok=True)
        
    async def generate_video(self, image_path, prompt, negative_prompt="", cfg_scale=0.5, mode="std", duration=5):
        """
        KlingAI API를 사용하여 이미지에서 동영상을 생성합니다.
        
        Args:
            image_path (str): 입력 이미지 경로
            prompt (str): 동영상 생성 프롬프트
            negative_prompt (str): 네거티브 프롬프트
            cfg_scale (float): Creativity Scale (0.0-1.0)
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
            
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                # 1. 이미지 업로드
                logger.info("이미지 업로드 중...")
                image_data = await self._upload_image(session, image_path)
                if not image_data:
                    raise Exception("이미지 업로드 실패")
                
                # 2. 비디오 생성 작업 시작
                logger.info("비디오 생성 작업 시작...")
                request_data = {
                    "model": "kling-v1",
                    "model_config": {
                        "cfg_scale": cfg_scale,
                        "mode": mode
                    },
                    "task_config": {
                        "type": "i2v",  # image to video
                        "input": {
                            "image": image_data['url']
                        },
                        "duration": duration
                    },
                    "prompt": prompt
                }
                
                if negative_prompt:
                    request_data["negative_prompt"] = negative_prompt
                
                async with session.post(
                    f'{self.base_url}/video-generation/image-to-video',
                    headers=headers,
                    json=request_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API 오류: {response.status} - {error_text}")
                        raise Exception(f"API 오류: {response.status}")
                    
                    result = await response.json()
                    
                    if result.get('code') != 0:
                        raise Exception(f"API 오류: {result.get('message', '알 수 없는 오류')}")
                    
                    task_id = result['data']['task_id']
                    logger.info(f"작업 ID: {task_id}")
                
                # 3. 생성 상태 확인 및 대기
                video_data = await self._wait_for_completion(session, task_id, headers)
                
                if not video_data:
                    raise Exception("비디오 생성 실패")
                
                # 4. 동영상 다운로드
                logger.info("동영상 다운로드 중...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"klingai_{timestamp}.mp4"
                filepath = os.path.join(self.download_dir, filename)
                
                async with session.get(video_data['video_url']) as video_response:
                    if video_response.status == 200:
                        with open(filepath, 'wb') as f:
                            async for chunk in video_response.content.iter_chunked(8192):
                                f.write(chunk)
                    else:
                        raise Exception("동영상 다운로드 실패")
                
                logger.info(f"동영상 생성 완료: {filename}")
                
                return {
                    'status': 'success',
                    'filename': filename,
                    'filepath': filepath,
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'duration': duration,
                    'mode': mode,
                    'task_id': task_id
                }
                
            except Exception as e:
                logger.error(f"동영상 생성 중 오류 발생: {str(e)}")
                return {
                    'status': 'error',
                    'error': str(e)
                }
    
    async def _upload_image(self, session, image_path):
        """
        이미지를 KlingAI 서버에 업로드합니다.
        
        Args:
            session: aiohttp 세션
            image_path: 업로드할 이미지 경로
            
        Returns:
            dict: 업로드된 이미지 정보 (url 포함)
        """
        try:
            # 업로드 URL 가져오기
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 1. 업로드 URL 요청
            async with session.post(
                f'{self.base_url}/storage/upload-url',
                headers=headers,
                json={"file_name": os.path.basename(image_path)}
            ) as response:
                if response.status != 200:
                    return None
                    
                result = await response.json()
                if result.get('code') != 0:
                    return None
                    
                upload_data = result['data']
                upload_url = upload_data['upload_url']
                image_id = upload_data['id']
            
            # 2. 이미지 업로드
            with open(image_path, 'rb') as f:
                file_data = f.read()
                
            async with session.put(
                upload_url,
                data=file_data,
                headers={'Content-Type': 'image/jpeg'}
            ) as response:
                if response.status != 200:
                    return None
            
            # 3. 업로드 확인
            return {
                'id': image_id,
                'url': upload_url.split('?')[0]  # URL에서 쿼리 파라미터 제거
            }
            
        except Exception as e:
            logger.error(f"이미지 업로드 중 오류: {str(e)}")
            return None
    
    async def _wait_for_completion(self, session, task_id, headers, max_wait=600):
        """
        동영상 생성 완료를 기다립니다.
        
        Args:
            session: aiohttp 세션
            task_id: 작업 ID
            headers: HTTP 헤더
            max_wait: 최대 대기 시간 (초)
            
        Returns:
            dict: 생성된 동영상 정보
        """
        start_time = time.time()
        check_interval = 5  # 5초마다 확인
        
        while True:
            if time.time() - start_time > max_wait:
                raise TimeoutError("동영상 생성 시간 초과")
            
            try:
                async with session.get(
                    f'{self.base_url}/video-generation/tasks/{task_id}',
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"상태 확인 실패: {response.status}")
                        await asyncio.sleep(check_interval)
                        continue
                    
                    result = await response.json()
                    
                    if result.get('code') != 0:
                        logger.error(f"상태 확인 오류: {result.get('message')}")
                        await asyncio.sleep(check_interval)
                        continue
                    
                    task_data = result['data']
                    status = task_data.get('status')
                    
                    logger.info(f"작업 상태: {status}")
                    
                    if status == 'completed':
                        # 성공
                        video_info = task_data.get('output', {})
                        if video_info and video_info.get('video_url'):
                            return {
                                'video_url': video_info['video_url'],
                                'duration': video_info.get('duration', 5),
                                'resolution': video_info.get('resolution', '1080p')
                            }
                        else:
                            raise Exception("비디오 URL을 찾을 수 없습니다")
                            
                    elif status == 'failed':
                        error_msg = task_data.get('error', {}).get('message', '알 수 없는 오류')
                        raise Exception(f"동영상 생성 실패: {error_msg}")
                    
                    elif status in ['pending', 'processing']:
                        # 아직 처리 중
                        progress = task_data.get('progress', 0)
                        logger.info(f"진행률: {progress}%")
                        await asyncio.sleep(check_interval)
                    
                    else:
                        # 알 수 없는 상태
                        logger.warning(f"알 수 없는 상태: {status}")
                        await asyncio.sleep(check_interval)
                        
            except Exception as e:
                logger.error(f"상태 확인 중 오류: {str(e)}")
                await asyncio.sleep(check_interval)
