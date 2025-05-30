import os
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleImageFXGenerator:
    """간단한 ImageFX 생성기"""
    
    def __init__(self):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.download_dir = os.path.join(project_root, 'uploads', 'images')
        os.makedirs(self.download_dir, exist_ok=True)
        
    async def generate_image(self, prompt, aspect_ratio="9:16"):
        """간단한 이미지 생성"""
        try:
            logger.info(f"이미지 생성 시작: {prompt}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                # ImageFX 페이지로 이동
                await page.goto('https://aitestkitchen.withgoogle.com/tools/image-fx')
                await page.wait_for_timeout(5000)
                
                # 프롬프트 입력
                await page.fill('textarea', prompt)
                await page.wait_for_timeout(2000)
                
                # 생성 버튼 클릭
                await page.click('button:has-text("만들기")')
                await page.wait_for_timeout(10000)
                
                # 이미지가 생성될 때까지 대기
                await page.wait_for_selector('img[src*="blob:"]', timeout=60000)
                
                # 이미지 다운로드
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"imagefx_{timestamp}.png"
                filepath = os.path.join(self.download_dir, filename)
                
                # 페이지 스크린샷으로 임시 저장
                await page.screenshot(path=filepath, full_page=False)
                
                await browser.close()
                
                return {
                    'status': 'success',
                    'filename': filename,
                    'filepath': filepath,
                    'prompt': prompt,
                    'aspect_ratio': aspect_ratio,
                    'generator': 'simple_imagefx'
                }
                
        except Exception as e:
            logger.error(f"이미지 생성 오류: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
