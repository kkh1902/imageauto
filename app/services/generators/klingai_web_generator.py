import os
import asyncio
import logging
from datetime import datetime
import time
from playwright.async_api import async_playwright
import requests
from urllib.parse import urljoin, urlparse
import aiofiles

logger = logging.getLogger(__name__)

class KlingAIWebGenerator:
    """
    Playwright를 사용한 KlingAI 웹사이트 자동화 비디오 생성기
    https://klingai.com/global/ 사이트 기준
    """
    def __init__(self):
        self.download_dir = os.path.join(os.path.dirname(__file__), '../../../../uploads/videos')
        os.makedirs(self.download_dir, exist_ok=True)
        self.base_url = "https://klingai.com"
        self.headless = os.getenv('KLINGAI_WEB_HEADLESS', 'false').lower() == 'true'
        
        # 로그인 정보 (환경변수에서)
        self.email = os.getenv('KLINGAI_EMAIL')
        self.password = os.getenv('KLINGAI_PASSWORD')
        
        if not self.email or not self.password:
            logger.warning("KlingAI 웹 로그인 정보가 설정되지 않았습니다. .env에 KLINGAI_EMAIL, KLINGAI_PASSWORD를 추가하세요.")
    
    async def generate_video(self, image_path, prompt, negative_prompt="", cfg_scale=0.5, mode="pro", duration=5, output_count=1):
        """
        Playwright를 사용하여 KlingAI 웹사이트에서 비디오 생성 준비
        현재는 Generate 버튼을 누르지 않고 설정까지만 진행
        
        Args:
            image_path: 입력 이미지 경로
            prompt: 비디오 생성 프롬프트
            negative_prompt: 네거티브 프롬프트
            cfg_scale: CFG 스케일 (사용되지 않을 수 있음)
            mode: 생성 모드 ("std" 또는 "pro")
            duration: 비디오 길이 (5 또는 10초)
            output_count: 출력 개수 (1, 2, 3, 4)
        """
        if not self.email or not self.password:
            return {
                'status': 'error',
                'error': 'KlingAI 웹 로그인 정보가 설정되지 않았습니다. .env에 KLINGAI_EMAIL, KLINGAI_PASSWORD를 추가하세요.'
            }
        
        try:
            async with async_playwright() as p:
                # 브라우저 실행
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--no-sandbox', 
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    # 1. KlingAI 메인 페이지로 이동
                    logger.info("🌐 KlingAI 웹사이트 접속 중...")
                    await page.goto(f"{self.base_url}/global/", wait_until='networkidle')
                    await page.wait_for_timeout(3000)
                    
                    # 2. 로그인 확인 및 로그인
                    logger.info("🔐 로그인 상태 확인...")
                    login_success = await self._handle_login(page)
                    if not login_success:
                        raise Exception("로그인 실패")
                    
                    # 3. Create 버튼 클릭
                    logger.info("🎬 Create 버튼 클릭...")
                    await self._click_create_button(page)
                    
                    # 4. Video 옵션 선택
                    logger.info("📹 Video 옵션 선택...")
                    await self._select_video_option(page)
                    
                    # 5. 이미지 업로드
                    logger.info("📸 이미지 업로드 중...")
                    upload_success = await self._upload_image(page, image_path)
                    if not upload_success:
                        raise Exception("이미지 업로드 실패")
                    
                    # 6. 프롬프트 입력
                    logger.info("✏️ 프롬프트 설정 중...")
                    await self._set_prompts(page, prompt, negative_prompt)
                    
                    # 7. Professional VIP 선택
                    logger.info("💎 Professional VIP 모드 선택...")
                    await self._select_professional_mode(page, mode)
                    
                    # 8. 기간 선택 (5초 또는 10초)
                    logger.info(f"⏱️ {duration}초 설정...")
                    await self._select_duration(page, duration)
                    
                    # 9. Output 개수 선택 (1, 2, 3, 4)
                    logger.info(f"🎯 Output {output_count}개 설정...")
                    await self._select_output_count(page, output_count)
                    
                    # 🛑 Generate 버튼은 누르지 않음 - 설정까지만 진행
                    logger.info("⏸️ Generate 버튼을 누르지 않고 설정 완료!")
                    logger.info("👀 브라우저에서 KlingAI 페이지를 확인하세요.")
                    logger.info("🎬 수동으로 Generate 버튼을 눌러 비디오를 생성할 수 있습니다.")
                    
                    # 브라우저를 열어둔 상태로 잠시 대기 (사용자가 확인할 수 있도록)
                    logger.info("⏳ 30초 동안 브라우저를 열어둡니다...")
                    await page.wait_for_timeout(30000)  # 30초 대기
                    
                    # 성공 응답 반환 (실제 비디오는 없지만 설정 완료)
                    return {
                        'status': 'success',
                        'filename': 'setup_completed.txt',  # 더미 파일명
                        'filepath': os.path.join(self.download_dir, 'setup_completed.txt'),
                        'prompt': prompt,
                        'negative_prompt': negative_prompt,
                        'duration': duration,
                        'mode': mode,
                        'output_count': output_count,
                        'generator': 'klingai_web',
                        'message': 'KlingAI 웹사이트 설정이 완료되었습니다. 브라우저에서 수동으로 Generate 버튼을 눌러주세요.',
                        'note': 'Generate 버튼을 누르지 않고 설정까지만 완료됨'
                    }
                    
                finally:
                    # 브라우저는 자동으로 닫힘
                    await browser.close()
                    logger.info("🔄 브라우저가 닫혔습니다.")
                    
        except Exception as e:
            logger.error(f"KlingAI 웹 설정 중 오류: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _handle_login(self, page):
        """로그인 처리"""
        try:
            # 로그인 버튼이 있는지 확인
            login_selectors = [
                'text="Sign in"',
                'text="Login"',
                'text="log in"',
                '[data-testid="login"]',
                '.login-btn',
                'button:has-text("Sign")',
                'a:has-text("Sign")'
            ]
            
            login_button_found = False
            for selector in login_selectors:
                try:
                    login_element = page.locator(selector).first
                    if await login_element.is_visible(timeout=2000):
                        logger.info("로그인 버튼 발견, 로그인 진행...")
                        await login_element.click()
                        login_button_found = True
                        break
                except:
                    continue
            
            if login_button_found:
                await page.wait_for_timeout(2000)
                
                # 이메일 입력
                email_selectors = [
                    'input[type="email"]',
                    'input[placeholder*="email"]',
                    'input[placeholder*="Email"]',
                    'input[name="email"]',
                    '.email-input input'
                ]
                
                email_input = None
                for selector in email_selectors:
                    try:
                        email_input = page.locator(selector).first
                        if await email_input.is_visible(timeout=2000):
                            break
                    except:
                        continue
                
                if email_input:
                    await email_input.fill(self.email)
                    await page.wait_for_timeout(1000)
                
                # 비밀번호 입력
                password_selectors = [
                    'input[type="password"]',
                    'input[placeholder*="password"]',
                    'input[placeholder*="Password"]',
                    'input[name="password"]',
                    '.password-input input'
                ]
                
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = page.locator(selector).first
                        if await password_input.is_visible(timeout=2000):
                            break
                    except:
                        continue
                
                if password_input:
                    await password_input.fill(self.password)
                    await page.wait_for_timeout(1000)
                
                # 로그인 제출 버튼 클릭
                submit_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Sign in")',
                    'button:has-text("Login")',
                    'button:has-text("Log in")',
                    '.login-submit',
                    '.signin-btn'
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_btn = page.locator(selector).first
                        if await submit_btn.is_visible(timeout=2000):
                            await submit_btn.click()
                            break
                    except:
                        continue
                
                # 로그인 완료 대기
                await page.wait_for_timeout(5000)
            
            # 로그인 성공 확인 (Create 버튼이나 사용자 정보가 보이는지)
            success_indicators = [
                'text="Create"',
                'text="create"',
                '.user-menu',
                '.profile',
                '[data-testid="create"]'
            ]
            
            for indicator in success_indicators:
                try:
                    if await page.locator(indicator).first.is_visible(timeout=3000):
                        logger.info("✅ 로그인 성공 확인")
                        return True
                except:
                    continue
            
            logger.info("⚠️ 로그인 상태 불확실, 계속 진행...")
            return True  # 일단 진행
            
        except Exception as e:
            logger.error(f"로그인 처리 중 오류: {str(e)}")
            return False
    
    async def _click_create_button(self, page):
        """Create 버튼 클릭"""
        create_selectors = [
            'text="Create"',
            'text="create"',
            '[data-testid="create"]',
            'button:has-text("Create")',
            '.create-btn',
            'a:has-text("Create")'
        ]
        
        for selector in create_selectors:
            try:
                create_btn = page.locator(selector).first
                if await create_btn.is_visible(timeout=5000):
                    await create_btn.click()
                    await page.wait_for_timeout(2000)
                    return True
            except:
                continue
        
        raise Exception("Create 버튼을 찾을 수 없습니다")
    
    async def _select_video_option(self, page):
        """Video 옵션 선택"""
        video_selectors = [
            'text="Video"',
            'text="video"',
            '[data-testid="video"]',
            'button:has-text("Video")',
            '.video-option',
            'div:has-text("Video")'
        ]
        
        for selector in video_selectors:
            try:
                video_option = page.locator(selector).first
                if await video_option.is_visible(timeout=5000):
                    await video_option.click()
                    await page.wait_for_timeout(2000)
                    return True
            except:
                continue
        
        raise Exception("Video 옵션을 찾을 수 없습니다")
    
    async def _upload_image(self, page, image_path):
        """이미지 업로드"""
        try:
            # 파일 업로드 input 찾기
            upload_selectors = [
                'input[type="file"]',
                'input[accept*="image"]',
                '[data-testid="file-upload"]',
                '.file-upload input'
            ]
            
            # 먼저 업로드 영역 클릭 시도
            upload_area_selectors = [
                'text="Upload"',
                'text="upload"',
                '.upload-area',
                '.drag-drop',
                '[data-testid="upload-area"]',
                'div:has-text("Upload")',
                'div:has-text("drag")'
            ]
            
            # 업로드 영역 클릭
            for selector in upload_area_selectors:
                try:
                    upload_area = page.locator(selector).first
                    if await upload_area.is_visible(timeout=3000):
                        await upload_area.click()
                        await page.wait_for_timeout(1000)
                        break
                except:
                    continue
            
            # 파일 input 찾아서 파일 업로드
            for selector in upload_selectors:
                try:
                    file_input = page.locator(selector).first
                    if await file_input.count() > 0:
                        await file_input.set_input_files(image_path)
                        await page.wait_for_timeout(3000)
                        
                        # 업로드 완료 확인
                        success_indicators = [
                            '.upload-success',
                            '.image-preview',
                            'img[src*="blob:"]',
                            '.uploaded-image',
                            '.preview-image'
                        ]
                        
                        for indicator in success_indicators:
                            try:
                                if await page.locator(indicator).first.is_visible(timeout=5000):
                                    logger.info("✅ 이미지 업로드 성공")
                                    return True
                            except:
                                continue
                        
                        # 업로드 후 추가 대기
                        await page.wait_for_timeout(3000)
                        return True
                except:
                    continue
            
            raise Exception("파일 업로드 input을 찾을 수 없습니다")
            
        except Exception as e:
            logger.error(f"이미지 업로드 중 오류: {str(e)}")
            return False
    
    async def _set_prompts(self, page, prompt, negative_prompt):
        """프롬프트 설정"""
        try:
            # 포지티브 프롬프트 입력
            prompt_selectors = [
                'textarea[placeholder*="prompt"]',
                'textarea[placeholder*="Prompt"]',
                'textarea[placeholder*="describe"]',
                'textarea[name="prompt"]',
                '.prompt-input textarea',
                '.prompt-textarea',
                'textarea:first-of-type'
            ]
            
            for selector in prompt_selectors:
                try:
                    prompt_input = page.locator(selector).first
                    if await prompt_input.is_visible(timeout=3000):
                        await prompt_input.click()
                        await prompt_input.fill(prompt)
                        await page.wait_for_timeout(1000)
                        logger.info(f"✅ 포지티브 프롬프트 입력: {prompt[:50]}...")
                        break
                except:
                    continue
            
            # 네거티브 프롬프트 입력 (있는 경우)
            if negative_prompt:
                negative_selectors = [
                    'textarea[placeholder*="negative"]',
                    'textarea[placeholder*="Negative"]',
                    'textarea[placeholder*="avoid"]',
                    'textarea[name="negative_prompt"]',
                    '.negative-prompt textarea',
                    'textarea:last-of-type'
                ]
                
                for selector in negative_selectors:
                    try:
                        negative_input = page.locator(selector).first
                        if await negative_input.is_visible(timeout=3000):
                            await negative_input.click()
                            await negative_input.fill(negative_prompt)
                            await page.wait_for_timeout(1000)
                            logger.info(f"✅ 네거티브 프롬프트 입력: {negative_prompt[:50]}...")
                            break
                    except:
                        continue
            
            return True
            
        except Exception as e:
            logger.error(f"프롬프트 설정 중 오류: {str(e)}")
            return False
    
    async def _select_professional_mode(self, page, mode):
        """Professional VIP 모드 선택"""
        try:
            if mode.lower() == "pro":
                pro_selectors = [
                    'text="Professional"',
                    'text="Pro"',
                    'text="VIP"',
                    '[data-testid="pro"]',
                    '.pro-mode',
                    '.professional',
                    'button:has-text("Pro")',
                    'div:has-text("Professional")'
                ]
                
                for selector in pro_selectors:
                    try:
                        pro_option = page.locator(selector).first
                        if await pro_option.is_visible(timeout=3000):
                            await pro_option.click()
                            await page.wait_for_timeout(1000)
                            logger.info("✅ Professional 모드 선택")
                            return True
                    except:
                        continue
            
            return True  # 기본값으로 진행
            
        except Exception as e:
            logger.error(f"모드 선택 중 오류: {str(e)}")
            return True
    
    async def _select_duration(self, page, duration):
        """비디오 길이 선택"""
        try:
            duration_selectors = [
                f'text="{duration}s"',
                f'text="{duration} seconds"',
                f'text="{duration}sec"',
                f'[data-duration="{duration}"]',
                f'button:has-text("{duration}")',
                f'.duration-{duration}'
            ]
            
            for selector in duration_selectors:
                try:
                    duration_option = page.locator(selector).first
                    if await duration_option.is_visible(timeout=3000):
                        await duration_option.click()
                        await page.wait_for_timeout(1000)
                        logger.info(f"✅ {duration}초 선택")
                        return True
                except:
                    continue
            
            # 슬라이더나 드롭다운으로 시도
            slider_selectors = [
                'input[type="range"]',
                '.duration-slider',
                'select[name*="duration"]'
            ]
            
            for selector in slider_selectors:
                try:
                    slider = page.locator(selector).first
                    if await slider.is_visible(timeout=2000):
                        await slider.fill(str(duration))
                        await page.wait_for_timeout(1000)
                        return True
                except:
                    continue
            
            return True  # 기본값으로 진행
            
        except Exception as e:
            logger.error(f"길이 선택 중 오류: {str(e)}")
            return True
    
    async def _select_output_count(self, page, output_count):
        """출력 개수 선택"""
        try:
            count_selectors = [
                f'text="{output_count}"',
                f'[data-count="{output_count}"]',
                f'button:has-text("{output_count}")',
                f'.output-{output_count}',
                f'input[value="{output_count}"]'
            ]
            
            for selector in count_selectors:
                try:
                    count_option = page.locator(selector).first
                    if await count_option.is_visible(timeout=3000):
                        await count_option.click()
                        await page.wait_for_timeout(1000)
                        logger.info(f"✅ Output {output_count}개 선택")
                        return True
                except:
                    continue
            
            # 숫자 입력 필드로 시도
            number_inputs = [
                'input[type="number"]',
                'input[name*="count"]',
                'input[name*="output"]',
                '.output-count input'
            ]
            
            for selector in number_inputs:
                try:
                    number_input = page.locator(selector).first
                    if await number_input.is_visible(timeout=2000):
                        await number_input.fill(str(output_count))
                        await page.wait_for_timeout(1000)
                        return True
                except:
                    continue
            
            return True  # 기본값으로 진행
            
        except Exception as e:
            logger.error(f"출력 개수 선택 중 오류: {str(e)}")
            return True
