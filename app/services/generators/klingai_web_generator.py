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
                
                # 브라우저 콘솔 로그 출력
                page.on('console', lambda msg: logger.info(f"🌐 브라우저: {msg.text}"))
                
                try:
                    # 1. KlingAI 메인 페이지로 이동
                    logger.info("🌐 KlingAI 웹사이트 접속 중...")
                    await page.goto(f"{self.base_url}/global/", wait_until='networkidle')
                    await page.wait_for_timeout(5000)
                    
                    # 현재 페이지 정보 출력
                    current_url = page.url
                    page_title = await page.title()
                    logger.info(f"📍 현재 페이지: {current_url}")
                    logger.info(f"📖 페이지 제목: {page_title}")
                    
                    # 2. 로그인 확인 및 로그인
                    logger.info("🔐 로그인 상태 확인...")
                    login_success = await self._handle_login(page)
                    if not login_success:
                        raise Exception("로그인 실패")
                    
                    # 3. Create 버튼 찾기 및 클릭 (개선된 방법)
                    logger.info("🎬 Create 버튼 찾기 시작...")
                    create_success = await self._find_and_click_create_button(page)
                    if not create_success:
                        raise Exception("Create 버튼을 찾을 수 없습니다")
                    
                    # 4. Video 옵션 선택 (개선된 방법)
                    logger.info("📹 Video 옵션 선택...")
                    video_success = await self._select_video_option(page)
                    if not video_success:
                        raise Exception("Video 옵션을 찾을 수 없습니다")
                    
                    # 5. Image to Video 탭 선택 확인
                    logger.info("📹 Image to Video 탭 확인...")
                    await self._select_image_to_video_tab(page)
                    
                    # 6. 이미지 업로드
                    logger.info("📸 이미지 업로드 중...")
                    upload_success = await self._upload_image_to_kling(page, image_path)
                    if not upload_success:
                        logger.warning("⚠️ 이미지 업로드 실패, 수동으로 업로드해주세요.")
                    
                    # 7. 프롬프트 입력
                    logger.info("✏️ 프롬프트 설정 중...")
                    await self._set_kling_prompts(page, prompt, negative_prompt)
                    
                    # 🛑 Generate 버튼은 누르지 않음 - 설정까지만 진행
                    logger.info("⏸️ 모든 설정 완료! Generate 버튼을 누르지 않고 대기...")
                    logger.info("👀 브라우저에서 KlingAI 페이지를 확인하세요.")
                    logger.info("🎬 수동으로 Generate 버튼을 눌러 비디오를 생성할 수 있습니다.")
                    
                    # 브라우저를 열어둔 상태로 대기
                    logger.info("⏳ 120초 동안 브라우저를 열어둡니다...")
                    await page.wait_for_timeout(120000)  # 2분 대기
                    
                    # 성공 응답 반환
                    return {
                        'status': 'success',
                        'filename': 'kling_setup_completed.txt',
                        'filepath': os.path.join(self.download_dir, 'kling_setup_completed.txt'),
                        'prompt': prompt,
                        'negative_prompt': negative_prompt,
                        'duration': duration,
                        'mode': mode,
                        'output_count': output_count,
                        'generator': 'klingai_web',
                        'message': 'KlingAI 비디오 생성 설정이 완료되었습니다.',
                        'note': 'Generate 버튼을 누르지 않고 설정까지만 완료됨'
                    }
                    
                finally:
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
            # 로그인 버튼 찾기
            login_selectors = [
                'text="Sign in"',
                'text="Login"',
                'text="log in"',
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
                email_input = page.locator('input[type="email"], input[placeholder*="email" i]').first
                if await email_input.is_visible(timeout=3000):
                    await email_input.fill(self.email)
                    await page.wait_for_timeout(1000)
                
                # 비밀번호 입력
                password_input = page.locator('input[type="password"]').first
                if await password_input.is_visible(timeout=3000):
                    await password_input.fill(self.password)
                    await page.wait_for_timeout(1000)
                
                # 로그인 제출 버튼 클릭
                submit_btn = page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Login")').first
                if await submit_btn.is_visible(timeout=3000):
                    await submit_btn.click()
                    await page.wait_for_timeout(5000)
            
            return True
            
        except Exception as e:
            logger.error(f"로그인 처리 중 오류: {str(e)}")
            return False
    
    async def _find_and_click_create_button(self, page):
        """Create 버튼을 안정적으로 찾아서 클릭 - 개선된 버전"""
        try:
            current_url = page.url
            
            # 충분한 대기 시간
            logger.info("⏳ 페이지 로딩 완료 대기...")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(5000)
            
            # 페이지 내용 확인
            page_text = await page.text_content('body')
            if 'Create' in page_text:
                logger.info("✅ 페이지에 'Create' 텍스트 존재")
            else:
                logger.warning("⚠️ 페이지에 'Create' 텍스트 없음")
            
            logger.info("🎯 Create 버튼 찾기...")
            
            # JavaScript로 정확한 Create 버튼 찾기
            create_success = await page.evaluate("""
                () => {
                    console.log('🎯 Create 버튼 찾기 시작...');
                    
                    // 방법 1: 정확히 'Create' 텍스트를 가진 클릭 가능한 요소
                    const allElements = document.querySelectorAll('*');
                    for (const el of allElements) {
                        const text = el.textContent ? el.textContent.trim() : '';
                        if (text.toLowerCase() === 'create' && 
                            el.offsetParent !== null &&  // 보이는 요소
                            (el.tagName === 'BUTTON' || el.tagName === 'A' || 
                             el.getAttribute('role') === 'button' ||
                             window.getComputedStyle(el).cursor === 'pointer')) {
                            
                            console.log('Create 버튼 발견:', el.tagName, el.className);
                            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            el.click();
                            console.log('Create 버튼 클릭 완료');
                            return true;
                        }
                    }
                    
                    // 방법 2: Create을 포함하는 클릭 가능한 요소 (더 관대한 검색)
                    for (const el of allElements) {
                        const text = el.textContent ? el.textContent.trim() : '';
                        if (text.toLowerCase().includes('create') && text.length < 20 &&
                            el.offsetParent !== null &&
                            (el.tagName === 'BUTTON' || el.tagName === 'A' || 
                             el.getAttribute('role') === 'button' ||
                             window.getComputedStyle(el).cursor === 'pointer')) {
                            
                            console.log('Create 포함 버튼 발견:', text, el.tagName, el.className);
                            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            el.click();
                            console.log('Create 포함 버튼 클릭 완료');
                            return true;
                        }
                    }
                    
                    console.log('Create 버튼을 찾을 수 없습니다');
                    return false;
                }
            """)
            
            if create_success:
                logger.info("✅ Create 버튼 클릭 성공!")
                await page.wait_for_timeout(5000)
                
                # URL 변화 확인
                new_url = page.url
                if new_url != current_url:
                    logger.info(f"✅ Create 클릭으로 페이지 이동: {current_url} → {new_url}")
                    return True
                else:
                    logger.info("⚠️ URL 변화 없음, 페이지 내용 변화 확인...")
                    # 페이지 내용이 변했을 수도 있으므로 성공으로 처리
                    return True
            
            # 실패 시 수동 대기
            logger.warning("❌ Create 버튼 자동 클릭 실패")
            logger.info("💡 수동으로 Create 버튼을 클릭해주세요")
            logger.info("⏳ 15초 대기...")
            
            await page.wait_for_timeout(15000)
            
            # 수동 클릭 후 URL 변화 확인
            final_url = page.url
            if final_url != current_url:
                logger.info(f"✅ 수동 클릭으로 페이지 이동: {current_url} → {final_url}")
                return True
            else:
                logger.info("⚠️ 페이지 변화 없음, 계속 진행")
                return True
            
        except Exception as e:
            logger.error(f"Create 버튼 처리 중 오류: {str(e)}")
            return False
    
    async def _select_video_option(self, page):
        """Video 옵션 선택 - 개선된 방법"""
        try:
            current_url = page.url
            logger.info(f"📍 현재 URL: {current_url}")
            
            # 이미 Video 페이지에 있는지 확인
            if 'video' in current_url.lower() or 'generation' in current_url.lower():
                logger.info("✅ 이미 Video Generation 페이지에 있습니다.")
                return True
            
            logger.info("🎬 Video 메뉴/버튼 찾기 시작...")
            
            # JavaScript로 정확한 Video 버튼 찾기
            video_success = await page.evaluate("""
                () => {
                    console.log('🎯 Video 버튼 찾기 시작...');
                    
                    // 방법 1: menu-item 클래스 내에서 Video 텍스트 찾기
                    const menuItems = document.querySelectorAll('.menu-item, [class*="menu"]');
                    console.log(`menu-item 요소 ${menuItems.length}개 검색`);
                    
                    for (const menuItem of menuItems) {
                        const text = menuItem.textContent ? menuItem.textContent.trim() : '';
                        if (text.includes('Video') && menuItem.offsetParent !== null) {
                            console.log('Video menu-item 발견:', text);
                            menuItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            menuItem.click();
                            console.log('Video menu-item 클릭 완료');
                            return true;
                        }
                    }
                    
                    // 방법 2: 모든 요소에서 정확히 'Video' 텍스트 찾기
                    const allElements = document.querySelectorAll('*');
                    for (const el of allElements) {
                        const text = el.textContent ? el.textContent.trim() : '';
                        if (text === 'Video' && el.offsetParent !== null) {
                            console.log('Video 텍스트 발견:', el.tagName, el.className);
                            
                            // 클릭 가능한 부모 찾기
                            let clickableParent = el;
                            while (clickableParent && clickableParent !== document.body) {
                                if (clickableParent.tagName === 'A' || clickableParent.tagName === 'BUTTON' ||
                                    clickableParent.getAttribute('role') === 'button' ||
                                    clickableParent.classList.contains('menu-item') ||
                                    window.getComputedStyle(clickableParent).cursor === 'pointer') {
                                    
                                    console.log('Video 클릭 가능 부모 발견:', clickableParent.tagName, clickableParent.className);
                                    clickableParent.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                    clickableParent.click();
                                    console.log('Video 부모 클릭 완료');
                                    return true;
                                }
                                clickableParent = clickableParent.parentElement;
                            }
                        }
                    }
                    
                    // 방법 3: Video가 포함된 링크나 버튼 찾기
                    const links = document.querySelectorAll('a, button, [role="button"]');
                    for (const link of links) {
                        const text = link.textContent ? link.textContent.trim() : '';
                        const href = link.href || '';
                        if ((text.includes('Video') || href.includes('video')) && 
                            link.offsetParent !== null) {
                            console.log('Video 링크/버튼 발견:', text, href);
                            link.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            link.click();
                            console.log('Video 링크/버튼 클릭 완료');
                            return true;
                        }
                    }
                    
                    console.log('Video 버튼을 찾을 수 없습니다');
                    return false;
                }
            """)
            
            if video_success:
                logger.info("✅ Video 버튼 클릭 성공!")
                await page.wait_for_timeout(5000)
                
                # URL 변화 확인
                new_url = page.url
                if new_url != current_url:
                    logger.info(f"✅ Video 클릭으로 페이지 이동: {current_url} → {new_url}")
                    return True
                
                # 페이지 내용 변화 확인
                indicators = [
                    'text="Video Generation"',
                    'text="Image to Video"',
                    'text="Click / Drop / Paste"'
                ]
                
                for indicator in indicators:
                    if await page.locator(indicator).count() > 0:
                        logger.info(f"✅ Video Generation 페이지 요소 발견: {indicator}")
                        return True
            
            # 실패 시 수동 대기
            logger.warning("❌ Video 버튼 자동 클릭 실패")
            logger.info("💡 수동으로 Video 버튼을 클릭해주세요")
            logger.info("⏳ 15초 대기...")
            
            await page.wait_for_timeout(15000)
            return True
            
        except Exception as e:
            logger.error(f"Video 옵션 선택 중 오류: {str(e)}")
            return False
    
    async def _select_image_to_video_tab(self, page):
        """Image to Video 탭 선택"""
        try:
            tab_selectors = [
                'text="Image to Video"',
                'button:has-text("Image to Video")',
                'div:has-text("Image to Video")'
            ]
            
            for selector in tab_selectors:
                try:
                    tab_element = page.locator(selector).first
                    if await tab_element.is_visible(timeout=3000):
                        logger.info(f"✅ Image to Video 탭 발견")
                        await tab_element.click()
                        await page.wait_for_timeout(2000)
                        return True
                except:
                    continue
            
            logger.info("⚠️ Image to Video 탭이 이미 선택되어 있을 수 있음")
            return True
            
        except Exception as e:
            logger.error(f"Image to Video 탭 선택 중 오류: {str(e)}")
            return False
    
    async def _upload_image_to_kling(self, page, image_path):
        """이미지 업로드"""
        try:
            logger.info(f"📸 이미지 업로드: {image_path}")
            
            if not os.path.exists(image_path):
                raise Exception(f"이미지 파일이 존재하지 않습니다: {image_path}")
            
            # 파일 input 요소 찾기
            file_input_selectors = [
                'input[type="file"]',
                'input[accept*="image"]'
            ]
            
            for selector in file_input_selectors:
                try:
                    file_inputs = page.locator(selector)
                    count = await file_inputs.count()
                    
                    logger.info(f"파일 input {count}개 발견: {selector}")
                    
                    for i in range(count):
                        try:
                            file_input = file_inputs.nth(i)
                            await file_input.set_input_files(image_path)
                            logger.info(f"✅ 파일 업로드 시도 완료")
                            
                            await page.wait_for_timeout(5000)
                            
                            # 업로드 성공 확인
                            success_indicators = [
                                'img[src*="blob:"]',
                                'img[src*="data:"]',
                                'canvas'
                            ]
                            
                            for indicator in success_indicators:
                                if await page.locator(indicator).count() > 0:
                                    logger.info(f"✅ 이미지 업로드 성공")
                                    return True
                                    
                        except:
                            continue
                except:
                    continue
            
            logger.warning("❌ 이미지 업로드 실패")
            return False
            
        except Exception as e:
            logger.error(f"이미지 업로드 중 오류: {str(e)}")
            return False
    
    async def _set_kling_prompts(self, page, prompt, negative_prompt):
        """프롬프트 입력"""
        try:
            logger.info("✏️ 프롬프트 입력...")
            
            # 메인 프롬프트 입력
            prompt_selectors = [
                'textarea[placeholder*="describe"]',
                'textarea[placeholder*="creative"]',
                'textarea:first-of-type'
            ]
            
            for selector in prompt_selectors:
                try:
                    prompt_input = page.locator(selector).first
                    if await prompt_input.is_visible(timeout=3000):
                        logger.info(f"✅ 프롬프트 필드 발견")
                        
                        await prompt_input.click()
                        await page.wait_for_timeout(500)
                        await prompt_input.fill(prompt)
                        await page.wait_for_timeout(1000)
                        
                        logger.info(f"✅ 프롬프트 입력 완료: {prompt[:50]}...")
                        break
                except:
                    continue
            
            # 네거티브 프롬프트 입력 (있는 경우)
            if negative_prompt:
                logger.info("✏️ 네거티브 프롬프트 입력...")
                
                negative_selectors = [
                    'textarea[placeholder*="negative"]',
                    'textarea:last-of-type'
                ]
                
                for selector in negative_selectors:
                    try:
                        negative_input = page.locator(selector).first
                        if await negative_input.is_visible(timeout=3000):
                            logger.info(f"✅ 네거티브 프롬프트 필드 발견")
                            
                            await negative_input.click()
                            await page.wait_for_timeout(500)
                            await negative_input.fill(negative_prompt)
                            await page.wait_for_timeout(1000)
                            
                            logger.info(f"✅ 네거티브 프롬프트 입력 완료: {negative_prompt[:50]}...")
                            break
                    except:
                        continue
            
            return True
            
        except Exception as e:
            logger.error(f"프롬프트 설정 중 오류: {str(e)}")
            return False
