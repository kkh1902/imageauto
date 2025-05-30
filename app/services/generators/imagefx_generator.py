import os
import asyncio
from playwright.async_api import async_playwright
import aiofiles
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class ImageFXGenerator:
    def __init__(self):
        # 절대 경로로 수정하여 경로 문제 해결
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.download_dir = os.path.join(project_root, 'uploads', 'images')
        os.makedirs(self.download_dir, exist_ok=True)
        logger.info(f"이미지 다운로드 디렉토리: {self.download_dir}")
        
        self.user_data_dir = os.path.join(project_root, 'browser_data', 'imagefx')
        os.makedirs(self.user_data_dir, exist_ok=True)
        logger.info(f"브라우저 데이터 디렉토리: {self.user_data_dir}")
        
    async def generate_image(self, prompt, aspect_ratio="9:16"):
        """
        ImageFX를 사용하여 이미지를 생성합니다.
        
        Args:
            prompt (str): 이미지 생성 프롬프트
            aspect_ratio (str): 가로세로 비율 (기본값: 9:16)
            
        Returns:
            dict: 생성된 이미지 정보
        """
        async with async_playwright() as p:
            try:
                # headless 모드 설정 (환경변수로 제어 가능)
                headless_mode = os.environ.get('IMAGEFX_HEADLESS', 'true').lower() == 'true'
                logger.info(f"Headless 모드: {headless_mode}")
                
                # 브라우저 실행 (사용자 데이터 유지)
                browser = await p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=headless_mode,
                    viewport={'width': 1920, 'height': 1080},
                    accept_downloads=True,
                    downloads_path=self.download_dir,  # 다운로드 경로 명시적 설정
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        f'--download-path={self.download_dir}',  # 추가 다운로드 경로 설정
                    ]
                )
                
                # 자동화 감지 우회를 위한 스크립트 추가
                await browser.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                """)
                
                page = browser.pages[0] if browser.pages else await browser.new_page()
                
                # ImageFX 페이지로 이동
                logger.info("ImageFX 페이지로 이동 중...")
                await page.goto('https://aitestkitchen.withgoogle.com/tools/image-fx', 
                              wait_until='domcontentloaded', timeout=30000)
                
                # 페이지 로드 대기
                await page.wait_for_timeout(5000)
                
                # URL 확인 - 로그인 페이지로 리다이렉트되었는지 체크
                current_url = page.url
                logger.info(f"현재 URL: {current_url}")
                
                if 'accounts.google.com' in current_url or 'signin' in current_url:
                    logger.info("Google 로그인이 필요합니다.")
                    await self._handle_google_login(page)
                    
                    # 로그인 후 ImageFX 페이지로 다시 이동
                    logger.info("로그인 완료 후 ImageFX 페이지로 이동...")
                    await page.goto('https://aitestkitchen.withgoogle.com/tools/image-fx', 
                                  wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(3000)
                
                # ImageFX 페이지가 로드되었는지 최종 확인
                current_url = page.url
                if 'image-fx' not in current_url:
                    raise Exception(f"ImageFX 페이지 로드 실패. 현재 URL: {current_url}")
                
                logger.info("ImageFX 페이지 로드 완료")
                
                # 프롬프트 입력
                await self._input_prompt(page, prompt)
                
                # 가로세로 비율 설정 (가능한 경우)
                await self._set_aspect_ratio(page, aspect_ratio)
                
                # 이미지 생성 실행
                await self._start_generation(page)
                
                # 생성 완료 대기 및 이미지 다운로드
                result = await self._wait_and_download_image(page, prompt, aspect_ratio)
                
                return result
                
            except Exception as e:
                logger.error(f"이미지 생성 중 오류 발생: {str(e)}")
                return {
                    'status': 'error',
                    'error': str(e)
                }
                
            finally:
                if 'browser' in locals():
                    await browser.close()

    async def _handle_google_login(self, page):
        """Google 로그인 처리"""
        logger.info("Google 로그인 처리 시작...")
        
        # 환경변수에서 계정 정보 가져오기
        email = os.environ.get('GOOGLE_EMAIL')
        password = os.environ.get('GOOGLE_PASSWORD')
        
        if not email or not password:
            logger.info("자동 로그인 정보가 없습니다. 수동 로그인을 진행하세요.")
            await self._manual_login_guidance(page)
            return
        
        try:
            # 이메일 입력
            logger.info("이메일 입력 중...")
            email_selectors = [
                'input[type="email"]',
                'input[name="identifier"]',
                'input[aria-label*="이메일"]',
                'input[aria-label*="email"]'
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = await page.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        break
                except:
                    continue
            
            if email_input:
                await email_input.fill(email)
                await page.keyboard.press('Enter')
                logger.info("이메일 입력 완료")
                
                # 비밀번호 페이지로 이동 대기
                await page.wait_for_timeout(3000)
                
                # 비밀번호 입력
                logger.info("비밀번호 입력 중...")
                password_selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[aria-label*="비밀번호"]',
                    'input[aria-label*="password"]'
                ]
                
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = await page.wait_for_selector(selector, timeout=5000)
                        if password_input:
                            break
                    except:
                        continue
                
                if password_input:
                    await password_input.fill(password)
                    await page.keyboard.press('Enter')
                    logger.info("비밀번호 입력 완료")
                    
                    # 로그인 완료 대기
                    await page.wait_for_timeout(5000)
                    
                    # 추가 인증이 필요한지 확인
                    current_url = page.url
                    if 'accounts.google.com' in current_url:
                        logger.warning("추가 인증이 필요할 수 있습니다. 수동으로 완료해주세요.")
                        await self._manual_login_guidance(page)
                    else:
                        logger.info("자동 로그인 성공")
                else:
                    logger.error("비밀번호 입력 필드를 찾을 수 없습니다.")
                    await self._manual_login_guidance(page)
            else:
                logger.error("이메일 입력 필드를 찾을 수 없습니다.")
                await self._manual_login_guidance(page)
                
        except Exception as e:
            logger.error(f"자동 로그인 중 오류: {e}")
            await self._manual_login_guidance(page)

    async def _manual_login_guidance(self, page):
        """수동 로그인 안내"""
        logger.info("="*60)
        logger.info("🔐 수동 로그인이 필요합니다")
        logger.info("="*60)
        logger.info("브라우저에서 다음 단계를 수행해주세요:")
        logger.info("1. Google 계정으로 로그인")
        logger.info("2. 2단계 인증이 있다면 완료")
        logger.info("3. ImageFX 페이지가 나타날 때까지 대기")
        logger.info("4. 로그인이 완료되면 아무 키나 눌러주세요...")
        logger.info("="*60)
        
        # 사용자 입력 대기
        input("로그인 완료 후 Enter를 눌러주세요...")
        
        # 로그인 완료 확인
        max_wait = 60  # 1분 대기
        for i in range(max_wait):
            current_url = page.url
            if 'accounts.google.com' not in current_url:
                logger.info("로그인 완료 확인됨!")
                return
            await asyncio.sleep(1)
        
        logger.warning("로그인 확인 시간이 초과되었습니다. 계속 진행합니다.")

    async def _input_prompt(self, page, prompt):
        """프롬프트 입력"""
        logger.info(f"프롬프트 입력: {prompt}")
        
        # 2025년 최신 ImageFX 선택자들
        prompt_selectors = [
            # 기본 프롬프트 선택자
            'textarea[placeholder*="prompt"]',
            'textarea[placeholder*="Prompt"]',
            'textarea[placeholder*="Describe"]',
            'textarea[placeholder*="describe"]',
            'input[placeholder*="prompt"]',
            'input[placeholder*="Prompt"]',
            
            # Google AI Labs 특화 선택자
            'textarea[data-testid*="prompt"]',
            'textarea[data-testid*="input"]',
            'input[data-testid*="prompt"]',
            'textarea[aria-label*="prompt"]',
            'textarea[aria-label*="input"]',
            
            # 일반적인 텍스트 입력 필드
            'textarea:not([style*="display: none"])',
            'input[type="text"]:not([style*="display: none"])',
            '[contenteditable="true"]',
            
            # 클래스 기반 선택자
            'textarea.prompt-input',
            'input.prompt-input',
            'textarea[class*="prompt"]',
            'input[class*="prompt"]',
            
            # 넓이 기반 선택자 (프롬프트 필드는 보통 넓음)
            'textarea',
            'input[type="text"]',
        ]
        
        prompt_input = None
        
        # 순차적으로 선택자 시도
        for i, selector in enumerate(prompt_selectors):
            try:
                logger.debug(f"선택자 시도 {i+1}/{len(prompt_selectors)}: {selector}")
                elements = await page.query_selector_all(selector)
                
                if elements:
                    logger.debug(f"선택자 '{selector}'로 {len(elements)}개 요소 발견")
                    
                    for j, element in enumerate(elements):
                        try:
                            # 요소가 보이고 활성화되어 있는지 확인
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            
                            if not (is_visible and is_enabled):
                                logger.debug(f"요소 {j+1} 사용 불가: visible={is_visible}, enabled={is_enabled}")
                                continue
                            
                            # 요소 크기 확인 (너무 작은 요소 제외)
                            box = await element.bounding_box()
                            if not box:
                                logger.debug(f"요소 {j+1} 바운딩 박스 없음")
                                continue
                                
                            # 프롬프트 필드는 보통 넓고 적당한 높이를 가짐
                            if box['width'] < 200 or box['height'] < 30:
                                logger.debug(f"요소 {j+1} 너무 작음: {box['width']}x{box['height']}")
                                continue
                            
                            # 요소 속성 확인 (디버깅)
                            placeholder = await element.get_attribute('placeholder') or ''
                            aria_label = await element.get_attribute('aria-label') or ''
                            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                            
                            logger.debug(f"요소 {j+1} 정보: tag={tag_name}, placeholder='{placeholder}', aria-label='{aria_label}', size={box['width']}x{box['height']}")
                            
                            # 적합한 요소 발견
                            prompt_input = element
                            logger.info(f"프롬프트 입력 필드 발견: 선택자 '{selector}', 요소 {j+1}")
                            break
                            
                        except Exception as e:
                            logger.debug(f"요소 {j+1} 처리 중 오류: {e}")
                            continue
                
                if prompt_input:
                    break
                    
            except Exception as e:
                logger.debug(f"선택자 '{selector}' 시도 중 오류: {e}")
                continue
        
        if not prompt_input:
            # 페이지 스크린샷 저장 (디버깅용)
            screenshot_path = os.path.join(self.download_dir, f"debug_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path)
            logger.info(f"디버깅을 위해 스크린샷 저장: {screenshot_path}")
            
            raise Exception("프롬프트 입력 필드를 찾을 수 없습니다. 페이지가 완전히 로드되지 않았거나 구조가 변경되었을 수 있습니다.")
        
        # 기존 텍스트 지우고 새 프롬프트 입력
        await prompt_input.click()
        await prompt_input.fill(prompt)  # fill()이 가장 빠름
        
        # 프롬프트 입력 후 충분한 대기 시간
        await page.wait_for_timeout(3000)
        
        logger.info("프롬프트 입력 완료 및 대기")

    async def _set_aspect_ratio(self, page, aspect_ratio):
        """가로세로 비율 설정"""
        try:
            logger.info(f"가로세로 비율 설정 시도: {aspect_ratio}")
            
            # 전체 페이지에서 가로세로 비율 관련 요소 찾기
            logger.info("페이지에서 가로세로 비율 관련 요소 검색 중...")
            
            # 더 단순하고 확실한 방법들
            ratio_selectors = [
                # 텍스트 기반 검색 (가장 확실)
                'text="가로세로 비율"',
                'text="가로 모드"',  
                'text="16:9"',
                ':has-text("가로세로")',
                ':has-text("비율")',
                ':has-text("16:9")',
                
                # 버튼 요소 찾기
                'button:has-text("가로")',
                'button:has-text("비율")', 
                'button:has-text("16:9")',
                'button:has-text("가로세로")',
                
                # 버튼 역할을 가진 요소
                'button[role="combobox"]',
                '[role="combobox"]',
                'button[aria-expanded]',
                
                # 클래스 기반 (제공해주신 정보)
                '.sc-65325eee-9',
                '.dEidLo',
                'button.sc-65325eee-9',
                'button.dEidLo',
                
                # 일반적인 드롭다운 선택자
                'select',
                '.dropdown',
                '.select'
            ]
            
            ratio_button = None
            
            # 각 선택자를 순차적으로 시도
            for i, selector in enumerate(ratio_selectors):
                try:
                    logger.debug(f"선택자 시도 {i+1}/{len(ratio_selectors)}: {selector}")
                    
                    # 요소 찾기 (짧은 타임아웃)
                    elements = await page.locator(selector).all()
                    logger.debug(f"  -> {len(elements)}개 요소 발견")
                    
                    for j, element in enumerate(elements):
                        try:
                            # 요소가 보이고 클릭 가능한지 확인
                            is_visible = await element.is_visible()
                            if not is_visible:
                                continue
                                
                            # 요소 텍스트 확인
                            element_text = await element.inner_text()
                            logger.debug(f"  -> 요소 {j+1} 텍스트: '{element_text.strip()}'")
                            
                            # 가로세로 비율과 관련된 텍스트인지 확인
                            text_lower = element_text.lower()
                            if any(keyword in text_lower for keyword in ['가로세로', '비율', '16:9', '가로', '세로', 'aspect', 'ratio']):
                                logger.info(f"✅ 가로세로 비율 요소 발견: '{element_text.strip()}'")
                                ratio_button = element
                                break
                                
                        except Exception as e:
                            logger.debug(f"  -> 요소 {j+1} 처리 중 오류: {e}")
                            continue
                    
                    if ratio_button:
                        logger.info(f"✅ 선택자 '{selector}'로 가로세로 비율 요소 찾음!")
                        break
                        
                except Exception as e:
                    logger.debug(f"선택자 '{selector}' 시도 중 오류: {e}")
                    continue
                    
            if not ratio_button:
                logger.warning("❌ 가로세로 비율 요소를 찾을 수 없습니다.")
                
                # 디버깅: 현재 페이지의 모든 버튼 나열
                try:
                    logger.info("디버깅: 현재 페이지의 모든 버튼들:")
                    all_buttons = await page.locator('button').all()
                    for i, btn in enumerate(all_buttons[:10]):  # 최대 10개만
                        try:
                            if await btn.is_visible():
                                btn_text = await btn.inner_text()
                                if btn_text.strip():
                                    logger.info(f"  버튼 {i+1}: '{btn_text.strip()}'")
                        except:
                            pass
                except:
                    pass
                    
                return False
            
            # 가로세로 비율 요소 클릭
            logger.info(f"클릭 시도: 가로세로 비율 요소")
            await ratio_button.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)
            
            try:
                await ratio_button.click()
                logger.info("✅ 가로세로 비율 요소 클릭 성공")
            except Exception as e:
                logger.warning(f"일반 클릭 실패, JavaScript 클릭 시도: {e}")
                await page.evaluate('arguments[0].click()', ratio_button)
                logger.info("✅ JavaScript로 클릭 성공")
            
            # 드롭다운/메뉴 열림 대기
            await page.wait_for_timeout(3000)
            logger.info("드롭다운/메뉴 열림 대기 완료")
            
            # 세로모드(9:16) 옵션 찾기
            if aspect_ratio == "9:16":
                logger.info("세로모드(9:16) 옵션 검색 시작...")
                
                # 세로모드 옵션 찾기
                vertical_selectors = [
                    'text="세로 모드(9:16)"',
                    'text="9:16"', 
                    'text="세로 모드"',
                    'text="세로"',
                    ':has-text("9:16")',
                    ':has-text("세로")',
                    '*:has-text("9:16")',
                    'div:has-text("9:16")',
                    'span:has-text("9:16")',
                    'li:has-text("9:16")',
                    '[role="option"]:has-text("9:16")',
                    'button:has-text("9:16")'
                ]
                
                vertical_option = None
                for i, selector in enumerate(vertical_selectors):
                    try:
                        logger.debug(f"세로모드 선택자 시도 {i+1}: {selector}")
                        
                        elements = await page.locator(selector).all()
                        for j, element in enumerate(elements):
                            try:
                                if await element.is_visible():
                                    element_text = await element.inner_text()
                                    logger.debug(f"  -> 세로모드 옵션 {j+1}: '{element_text.strip()}'")
                                    
                                    # 9:16 또는 세로 관련 텍스트인지 확인
                                    if '9:16' in element_text or '세로' in element_text:
                                        logger.info(f"✅ 세로모드 옵션 발견: '{element_text.strip()}'")
                                        vertical_option = element
                                        break
                            except:
                                continue
                        
                        if vertical_option:
                            break
                            
                    except Exception as e:
                        logger.debug(f"세로모드 선택자 '{selector}' 시도 중 오류: {e}")
                        continue
                
                if vertical_option:
                    # 세로모드 옵션 클릭
                    logger.info("세로모드(9:16) 옵션 클릭 시도...")
                    await vertical_option.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    
                    try:
                        await vertical_option.click()
                        logger.info("✅ 세로모드(9:16) 선택 완료!")
                    except Exception as e:
                        logger.warning(f"일반 클릭 실패, JavaScript 클릭 시도: {e}")
                        await page.evaluate('arguments[0].click()', vertical_option)
                        logger.info("✅ JavaScript로 세로모드 선택 완료!")
                        
                    await page.wait_for_timeout(1000)
                    return True
                    
                else:
                    logger.warning("❌ 세로모드(9:16) 옵션을 찾을 수 없습니다.")
                    
                    # 디버깅: 현재 보이는 모든 옵션 나열
                    try:
                        logger.info("디버깅: 현재 보이는 모든 옵션들:")
                        all_options = await page.locator('*:visible').all()
                        option_count = 0
                        for opt in all_options:
                            try:
                                opt_text = await opt.inner_text()
                                if opt_text.strip() and len(opt_text.strip()) < 50:  # 짧은 텍스트만
                                    option_count += 1
                                    logger.info(f"  옵션 {option_count}: '{opt_text.strip()}'")
                                    if option_count >= 15:  # 최대 15개
                                        break
                            except:
                                pass
                    except:
                        pass
                        
                    # ESC로 드롭다운 닫기
                    await page.keyboard.press('Escape')
                    return False
            
            logger.info("가로세로 비율 설정 완료")
            return True
            
        except Exception as e:
            logger.error(f"가로세로 비율 설정 중 오류: {e}")
            # 오류 시 ESC로 정리
            try:
                await page.keyboard.press('Escape')
            except:
                pass
            return False

    async def _start_generation(self, page):
        """이미지 생성 시작"""
        logger.info("이미지 생성 시작...")
        
        # 실제 ImageFX 만들기 버튼 선택자들
        generate_selectors = [
            # 제공된 HTML 구조 기반
            'button.sc-7d2e2cf5-1.hhaFVo.sc-2519865f-4.kdkDdJ',
            'button:has-text("만들기")',
            'button:has(div:has-text("만들기"))',
            
            # 일반적인 생성 버튼들
            'button:has-text("Generate")',
            'button:has-text("Create")',
            'button:has-text("생성")',
            'button[type="submit"]',
            'button[data-testid*="generate"]',
            'button[aria-label*="generate"]',
            'button[aria-label*="Generate"]',
            
            # 아이콘과 함께 있는 버튼
            'button:has(i.material-icons)',
            'button:has(i:has-text("spark"))',
            'button:has(i.google-symbols)',
        ]
        
        generate_button = None
        for i, selector in enumerate(generate_selectors):
            try:
                logger.debug(f"생성 버튼 선택자 시도 {i+1}: {selector}")
                buttons = await page.query_selector_all(selector)
                
                for j, button in enumerate(buttons):
                    try:
                        # 버튼이 활성화되고 보이는지 확인
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        is_disabled = await button.get_attribute('disabled')
                        
                        if not (is_visible and is_enabled and not is_disabled):
                            logger.debug(f"버튼 {j+1} 사용 불가: visible={is_visible}, enabled={is_enabled}, disabled={is_disabled}")
                            continue
                        
                        # 버튼 텍스트 확인 (디버깅)
                        button_text = await button.text_content() or ''
                        button_html = await button.inner_html()
                        logger.debug(f"버튼 {j+1} 정보: text='{button_text.strip()}', html 일부: {button_html[:100]}...")
                        
                        # 적합한 버튼 발견
                        generate_button = button
                        logger.info(f"생성 버튼 발견: 선택자 '{selector}', 버튼 {j+1}")
                        break
                        
                    except Exception as e:
                        logger.debug(f"버튼 {j+1} 처리 중 오류: {e}")
                        continue
                
                if generate_button:
                    break
                    
            except Exception as e:
                logger.debug(f"선택자 '{selector}' 시도 중 오류: {e}")
                continue
        
        if generate_button:
            try:
                await generate_button.click()
                logger.info("생성 버튼 클릭 완료")
            except Exception as e:
                logger.error(f"생성 버튼 클릭 중 오류: {e}")
                # Enter 키로 대체 시도
                logger.info("Enter 키로 대체 시도")
                await page.keyboard.press('Enter')
        else:
            # Enter 키로 시도
            logger.info("생성 버튼을 찾을 수 없어 Enter 키로 시도")
            await page.keyboard.press('Enter')
        
        # 생성 시작 확인을 위한 충분한 대기
        await page.wait_for_timeout(10000)

    async def _wait_and_download_image(self, page, prompt, aspect_ratio):
        """생성 완료 대기 및 이미지 다운로드"""
        logger.info("🎨 이미지 생성 완료 대기 중...")
        
        # 생성 완료까지 최대 대기 시간 (10분)
        max_wait_time = 600
        check_interval = 10
        
        # 다운로드 이벤트를 위한 Promise 설정
        download_promise = None
        downloaded_file = None
        
        for elapsed in range(0, max_wait_time, check_interval):
            try:
                # 진행 상황 로그
                if elapsed % 60 == 0 and elapsed > 0:
                    logger.info(f"⏳ 이미지 생성 대기 중... ({elapsed}/{max_wait_time}초)")
                elif elapsed % 30 == 0:
                    logger.debug(f"⏳ 생성 대기 중... ({elapsed}초)")
                
                # 다운로드 아이콘 찾기
                if elapsed % 30 == 0:
                    logger.debug(f"🔍 다운로드 아이콘 검색 시도 {elapsed}초...")
                
                # 1단계: 더보기 버튼 찾기
                more_button_selectors = [
                    'button:has(i.material-icons:has-text("more_vert"))',
                    'button:has(i:has-text("more_vert"))',
                    'button[aria-label*="더보기"]',
                    'button[aria-label*="옵션"]',
                    'i.material-icons:has-text("more_vert")',
                    'i:has-text("more_vert")',
                ]
                
                # 2단계: 다운로드 메뉴 아이템 찾기 (더보기 클릭 후)
                download_menu_selectors = [
                    # 메뉴 아이템 with 다운로드 아이콘과 텍스트
                    'div[role="menuitem"]:has(i.google-symbols:has-text("download"))',
                    'div[role="menuitem"]:has(i:has-text("download"))',
                    'div[role="menuitem"]:has-text("다운로드")',
                    '[role="menuitem"]:has(i:has-text("download"))',
                    '[role="menuitem"]:has-text("다운로드")',
                    
                    # 일반적인 다운로드 요소들 (폴백)
                    'i:has-text("download")',
                    'i.material-icons:has-text("download")',
                    'i.material-symbols-outlined:has-text("download")',
                    'i.google-symbols:has-text("download")',
                    'button:has(i:has-text("download"))',
                    'button[aria-label*="download"]',
                    'button[aria-label*="Download"]',
                    'button[aria-label*="다운로드"]',
                ]
                
                download_button = None
                
                # 1단계: 더보기 버튼 찾기 및 클릭
                more_button = None
                for i, selector in enumerate(more_button_selectors):
                    try:
                        logger.debug(f"더보기 버튼 선택자 시도 {i+1}/{len(more_button_selectors)}: {selector}")
                        
                        elements = await page.locator(selector).all()
                        logger.debug(f"  -> {len(elements)}개 요소 발견")
                        
                        for j, element in enumerate(elements):
                            try:
                                # 요소가 보이고 클릭 가능한지 확인
                                is_visible = await element.is_visible()
                                if not is_visible:
                                    continue
                                
                                # 요소가 실제로 클릭 가능한지 확인
                                try:
                                    box = await element.bounding_box()
                                    if not box or box['width'] < 10 or box['height'] < 10:
                                        continue
                                except:
                                    continue
                                
                                more_button = element
                                logger.info(f"✅ 더보기 버튼 발견: 선택자 '{selector}', 요소 {j+1}")
                                break
                                
                            except Exception as e:
                                logger.debug(f"  -> 요소 {j+1} 처리 중 오류: {e}")
                                continue
                        
                        if more_button:
                            break
                            
                    except Exception as e:
                        logger.debug(f"선택자 '{selector}' 시도 중 오류: {e}")
                        continue
                
                # 더보기 버튼을 찾았으면 클릭
                if more_button:
                    try:
                        # ESC 키로 이전 메뉴 닫기 (있다면)
                        try:
                            await page.keyboard.press('Escape')
                            await page.wait_for_timeout(500)
                        except:
                            pass
                        
                        logger.info("📋 더보기 버튼 클릭 시도...")
                        await more_button.scroll_into_view_if_needed()
                        await page.wait_for_timeout(1500)  # 더 긴 대기
                        
                        # 더보기 버튼 클릭 시도
                        more_click_success = False
                        
                        # 1. 일반 클릭
                        try:
                            await more_button.click(timeout=10000)
                            more_click_success = True
                            logger.info("✅ 더보기 버튼 일반 클릭 성공")
                        except Exception as e:
                            logger.warning(f"더보기 버튼 일반 클릭 실패: {e}")
                        
                        # 2. JavaScript 클릭
                        if not more_click_success:
                            try:
                                await page.evaluate('arguments[0].click()', more_button)
                                more_click_success = True
                                logger.info("✅ 더보기 버튼 JavaScript 클릭 성공")
                            except Exception as e:
                                logger.warning(f"더보기 버튼 JavaScript 클릭 실패: {e}")
                        
                        # 3. 포스 클릭
                        if not more_click_success:
                            try:
                                box = await more_button.bounding_box()
                                if box:
                                    x = box['x'] + box['width'] / 2
                                    y = box['y'] + box['height'] / 2
                                    await page.mouse.click(x, y)
                                    more_click_success = True
                                    logger.info("✅ 더보기 버튼 포스 클릭 성공")
                            except Exception as e:
                                logger.error(f"더보기 버튼 포스 클릭 실패: {e}")
                        
                        if not more_click_success:
                            logger.error("❌ 더보기 버튼 모든 클릭 방법 실패!")
                            continue
                        
                        # 드롭다운 메뉴 나타날 때까지 대기 및 확인
                        logger.info("드롭다운 메뉴 로딩 대기 중...")
                        await page.wait_for_timeout(5000)  # 5초로 증가
                        
                        # 메뉴가 실제로 나타났는지 확인 (최대 10초간 시도)
                        menu_appeared = False
                        for check_attempt in range(10):  # 최대 10번 확인
                            try:
                                # 메뉴 컨테이너 확인
                                menu_containers = await page.locator('[role="menu"], [data-radix-menu-content], .dropdown, .menu').all()
                                visible_menus = []
                                for menu in menu_containers:
                                    if await menu.is_visible():
                                        visible_menus.append(menu)
                                
                                if visible_menus:
                                    logger.info(f"✅ {len(visible_menus)}개의 메뉴 컨테이너 발견됨")
                                    menu_appeared = True
                                    break
                                else:
                                    logger.debug(f"메뉴 확인 시도 {check_attempt + 1}/10 - 메뉴가 아직 나타나지 않음")
                                    await page.wait_for_timeout(1000)
                            except Exception as e:
                                logger.debug(f"메뉴 확인 중 오류: {e}")
                                await page.wait_for_timeout(1000)
                        
                        if not menu_appeared:
                            logger.warning("⚠️ 드롭다운 메뉴가 나타나지 않았을 가능성이 있음")
                        
                        # 현재 페이지의 모든 메뉴 아이템 디버깅
                        try:
                            logger.info("🔍 현재 페이지의 모든 메뉴 관련 요소들:")
                            
                            # 정확한 HTML 구조에 맞는 선택자들 추가
                            precise_selectors = [
                                # 제공된 정확한 HTML 구조 기반
                                'div[role="menuitem"].sc-ef24c21d-2.fcJHxi:has(i.google-symbols:has-text("download"))',
                                'div[role="menuitem"].fcJHxi:has(i.google-symbols:has-text("download"))',
                                'div[role="menuitem"]:has(i.google-symbols:has-text("download"))',
                                
                                # 클래스 기반
                                '.sc-ef24c21d-2.fcJHxi:has(i.google-symbols:has-text("download"))',
                                '.fcJHxi:has(i.google-symbols:has-text("download"))',
                                
                                # data-radix 속성 기반
                                '[data-radix-collection-item]:has(i.google-symbols:has-text("download"))',
                                
                                # 텍스트 기반
                                'div[role="menuitem"]:has-text("다운로드")',
                                '[role="menuitem"]:has-text("다운로드")',
                                
                                # 아이콘 기반
                                'i.google-symbols:has-text("download")',
                                'i.ojlmB.google-symbols:has-text("download")',
                            ]
                            
                            # 정확한 선택자들을 먼저 시도
                            download_found_precise = False
                            for i, selector in enumerate(precise_selectors):
                                try:
                                    logger.info(f"🎯 정밀 선택자 시도 {i+1}/{len(precise_selectors)}: {selector}")
                                    
                                    # 선택자 대기
                                    try:
                                        await page.wait_for_selector(selector, timeout=3000)
                                        logger.info(f"✅ 정밀 선택자 '{selector}'로 요소 발견!")
                                    except:
                                        logger.debug(f"정밀 선택자 '{selector}' 대기 타임아웃")
                                    
                                    elements = await page.locator(selector).all()
                                    logger.info(f"  -> {len(elements)}개 요소 발견")
                                    
                                    for j, element in enumerate(elements):
                                        try:
                                            is_visible = await element.is_visible()
                                            if not is_visible:
                                                logger.debug(f"  -> 요소 {j+1} 보이지 않음")
                                                continue
                                            
                                            # 요소 정보 로깅
                                            try:
                                                element_text = await element.inner_text()
                                                element_html = await element.inner_html()
                                                logger.info(f"  ✅ 정밀 다운로드 요소 {j+1}: text='{element_text.strip()}'")
                                                logger.debug(f"     HTML: {element_html[:200]}...")
                                            except Exception as e:
                                                logger.debug(f"  -> 요소 {j+1} 정보 읽기 실패: {e}")
                                            
                                            # 즉시 다운로드 시도
                                            logger.info(f"📥 정밀 다운로드 요소 클릭 시도...")
                                            
                                            # 스크롤 및 대기
                                            await element.scroll_into_view_if_needed()
                                            await page.wait_for_timeout(1000)
                                            
                                            # 다운로드 폴더의 기존 파일 목록 저장
                                            existing_files = set(os.listdir(self.download_dir))
                                            
                                            # 3단계 클릭 시도
                                            precise_clicked = False
                                            
                                            # 1. 일반 클릭
                                            try:
                                                await element.click(timeout=5000)
                                                precise_clicked = True
                                                logger.info("✅ 정밀 요소 일반 클릭 성공")
                                            except Exception as e:
                                                logger.debug(f"정밀 요소 일반 클릭 실패: {e}")
                                            
                                            # 2. JavaScript 클릭
                                            if not precise_clicked:
                                                try:
                                                    await page.evaluate('arguments[0].click()', element)
                                                    precise_clicked = True
                                                    logger.info("✅ 정밀 요소 JavaScript 클릭 성공")
                                                except Exception as e:
                                                    logger.debug(f"정밀 요소 JavaScript 클릭 실패: {e}")
                                            
                                            # 3. 포스 클릭
                                            if not precise_clicked:
                                                try:
                                                    box = await element.bounding_box()
                                                    if box:
                                                        x = box['x'] + box['width'] / 2
                                                        y = box['y'] + box['height'] / 2
                                                        await page.mouse.click(x, y)
                                                        precise_clicked = True
                                                        logger.info("✅ 정밀 요소 포스 클릭 성공")
                                                except Exception as e:
                                                    logger.debug(f"정밀 요소 포스 클릭 실패: {e}")
                                            
                                            if precise_clicked:
                                                # 파일 시스템 기반 다운로드 대기
                                                logger.info("📥 파일 시스템 기반 다운로드 대기 중...")
                                                
                                                # 대기 시간을 60초로 늘리고 더 자세히 확인
                                                for wait_seconds in range(60):  # 60초 대기
                                                    await page.wait_for_timeout(1000)
                                                    
                                                    # 새 파일 확인
                                                    try:
                                                        current_files = set(os.listdir(self.download_dir))
                                                        new_files = current_files - existing_files
                                                        
                                                        # 다운로드 중인 파일(임시 파일) 포함 대기
                                                        all_potential_files = []
                                                        for f in current_files:
                                                            filepath = os.path.join(self.download_dir, f)
                                                            if (os.path.exists(filepath) and 
                                                                f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.crdownload', '.tmp')) and
                                                                f not in existing_files):
                                                                all_potential_files.append(f)
                                                        
                                                        if wait_seconds % 5 == 0:  # 5초마다 로깅
                                                            logger.info(f"🕐 대기 중... {wait_seconds}/60초 - 새 파일: {len(new_files)}개, 전체 파일: {len(current_files)}개")
                                                            if all_potential_files:
                                                                logger.info(f"   파일 후보: {all_potential_files}")
                                                        
                                                        if new_files:
                                                            # 가장 최근 파일 찾기
                                                            newest_file = None
                                                            newest_time = 0
                                                            
                                                            for filename in new_files:
                                                                filepath = os.path.join(self.download_dir, filename)
                                                                if os.path.exists(filepath):
                                                                    # 다운로드 중인 파일 제외
                                                                    if filename.endswith('.crdownload') or filename.endswith('.tmp'):
                                                                        logger.info(f"🔄 다운로드 중: {filename}")
                                                                        continue
                                                                        
                                                                    file_time = os.path.getctime(filepath)
                                                                    if file_time > newest_time:
                                                                        newest_time = file_time
                                                                        newest_file = filename
                                                            
                                                            if newest_file:
                                                                filepath = os.path.join(self.download_dir, newest_file)
                                                                file_size = os.path.getsize(filepath)
                                                                
                                                                logger.info(f"📁 새 파일 발견: {newest_file} ({file_size:,} bytes)")
                                                                
                                                                if file_size > 5000:  # 5KB 이상
                                                                    # 파일 이름 정리
                                                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                                    name, ext = os.path.splitext(newest_file)
                                                                    if not ext:
                                                                        ext = '.jpg'
                                                                    final_filename = f"imagefx_{timestamp}{ext}"
                                                                    final_filepath = os.path.join(self.download_dir, final_filename)
                                                                    
                                                                    try:
                                                                        if filepath != final_filepath:
                                                                            os.rename(filepath, final_filepath)
                                                                        
                                                                        logger.info(f"✅ 정밀 선택자로 다운로드 성공! 파일 크기: {file_size:,} bytes")
                                                                        return {
                                                                            'status': 'success',
                                                                            'filename': final_filename,
                                                                            'filepath': final_filepath,
                                                                            'prompt': prompt,
                                                                            'aspect_ratio': aspect_ratio,
                                                                            'generator': 'imagefx',
                                                                            'file_size': file_size,
                                                                            'download_method': 'filesystem_detection'
                                                                        }
                                                                    except Exception as rename_error:
                                                                        logger.warning(f"파일 이름 변경 실패: {rename_error}")
                                                                        # 원본 파일 그대로 반환
                                                                        return {
                                                                            'status': 'success',
                                                                            'filename': newest_file,
                                                                            'filepath': filepath,
                                                                            'prompt': prompt,
                                                                            'aspect_ratio': aspect_ratio,
                                                                            'generator': 'imagefx',
                                                                            'file_size': file_size,
                                                                            'download_method': 'filesystem_detection'
                                                                        }
                                                                else:
                                                                    logger.info(f"⚠️ 파일이 너무 작음, 계속 대기: {file_size} bytes")
                                                                    
                                                    except Exception as file_check_error:
                                                        logger.debug(f"파일 확인 오류: {file_check_error}")
                                                
                                                logger.warning("📥 정밀 선택자 다운로드 대기 시간 초과 (60초)")
                                            
                                            download_found_precise = True
                                            break
                                            
                                        except Exception as e:
                                            logger.debug(f"  -> 정밀 요소 {j+1} 처리 중 오류: {e}")
                                            continue
                                    
                                    if download_found_precise:
                                        break
                                        
                                except Exception as e:
                                    logger.debug(f"정밀 선택자 '{selector}' 시도 중 오류: {e}")
                                    continue
                            
                            # 정밀 선택자로 성공하면 일반 스캔 생략
                            if download_found_precise:
                                logger.info("✅ 정밀 선택자로 다운로드 완료, 일반 스캔 생략")
                            else:
                                # 1. 모든 메뉴 아이템 찾기 (정밀 선택자 실패 시만 실행)
                                logger.info("⚠️ 정밀 선택자 실패, 일반 스캔 시작...")
                                
                                # 모든 메뉴 아이템 찾기
                                all_menu_items = await page.locator('[role="menuitem"]').all()
                                logger.info(f"전체 메뉴 아이템 수: {len(all_menu_items)}")
                                
                                for idx, item in enumerate(all_menu_items[:15]):  # 최대 15개만 로깅
                                    try:
                                        is_visible = await item.is_visible()
                                        text_content = await item.inner_text()
                                        html_content = await item.inner_html()
                                        logger.info(f"  메뉴 아이템 {idx+1}: visible={is_visible}")
                                        logger.info(f"    text: '{text_content.strip()}'")
                                        logger.info(f"    html: {html_content[:200]}...")
                                        
                                        # 다운로드 관련 키워드 찾기
                                        if "다운로드" in text_content or "download" in text_content.lower() or "download" in html_content.lower():
                                            logger.info(f"    ⭐ 다운로드 관련 아이템 발견!")
                                    except Exception as e:
                                        logger.debug(f"  메뉴 아이템 {idx+1} 정보 읽기 실패: {e}")
                            
                            # 2. 모든 클릭 가능한 요소 찾기
                            logger.info("\n🔍 모든 클릭 가능한 요소들:")
                            clickable_elements = await page.locator('button, [role="button"], [role="menuitem"], a, div[onclick], span[onclick]').all()
                            logger.info(f"전체 클릭 가능 요소 수: {len(clickable_elements)}")
                            
                            download_candidates = []
                            for idx, elem in enumerate(clickable_elements[:20]):  # 최대 20개
                                try:
                                    is_visible = await elem.is_visible()
                                    if not is_visible:
                                        continue
                                    
                                    text = await elem.inner_text()
                                    html = await elem.inner_html()
                                    
                                    # 다운로드 관련 요소인지 확인
                                    if ("다운로드" in text.lower() or 
                                        "download" in text.lower() or 
                                        "download" in html.lower() or
                                        'google-symbols' in html and 'download' in html):
                                        
                                        download_candidates.append({
                                            'index': idx,
                                            'element': elem,
                                            'text': text.strip(),
                                            'html_preview': html[:150]
                                        })
                                        logger.info(f"  ⭐ 다운로드 후보 {len(download_candidates)}: text='{text.strip()}'")
                                        
                                except Exception as e:
                                    continue
                            
                            logger.info(f"\n🎯 총 {len(download_candidates)}개의 다운로드 후보 발견!")
                            
                            # 3. 다운로드 후보가 있으면 직접 클릭 시도
                            if download_candidates:
                                for candidate in download_candidates:
                                    logger.info(f"\n📥 다운로드 후보 클릭 시도: '{candidate['text']}'")
                                    
                                    try:
                                        # 다운로드 이벤트 리스너 설정
                                        if not download_promise:
                                            try:
                                                # 파일 시스템 기반 다운로드 감지 사용
                                                existing_files = set(os.listdir(self.download_dir))
                                                logger.info("파일 시스템 기반 다운로드 감지 설정 완료")
                                            except Exception as e:
                                                logger.warning(f"다운로드 감지 설정 오류: {e}")
                                        
                                        elem = candidate['element']
                                        
                                        # 스크롤 및 대기
                                        await elem.scroll_into_view_if_needed()
                                        await page.wait_for_timeout(1000)
                                        
                                        # 다양한 방법으로 클릭 시도
                                        clicked = False
                                        
                                        # 1. 일반 클릭
                                        try:
                                            await elem.click(timeout=5000)
                                            clicked = True
                                            logger.info("✅ 일반 클릭 성공")
                                        except Exception as e:
                                            logger.debug(f"일반 클릭 실패: {e}")
                                        
                                        # 2. JavaScript 클릭
                                        if not clicked:
                                            try:
                                                await page.evaluate('arguments[0].click()', elem)
                                                clicked = True
                                                logger.info("✅ JavaScript 클릭 성공")
                                            except Exception as e:
                                                logger.debug(f"JavaScript 클릭 실패: {e}")
                                        
                                        # 3. 포스 클릭
                                        if not clicked:
                                            try:
                                                box = await elem.bounding_box()
                                                if box:
                                                    x = box['x'] + box['width'] / 2
                                                    y = box['y'] + box['height'] / 2
                                                    await page.mouse.click(x, y)
                                                    clicked = True
                                                    logger.info("✅ 포스 클릭 성곳")
                                            except Exception as e:
                                                logger.debug(f"포스 클릭 실패: {e}")
                                        
                                        if clicked:
                                            # 다운로드 대기
                                            logger.info("📥 다운로드 이벤트 대기 중...")
                                            
                                            try:
                                                # 파일 시스템 기반 대기
                                                for wait_seconds in range(30):  # 30초 대기
                                                    await page.wait_for_timeout(1000)
                                                    
                                                    # 새 파일 확인
                                                    current_files = set(os.listdir(self.download_dir))
                                                    new_files = current_files - existing_files
                                                    
                                                    if new_files:
                                                        # 가장 최근 파일 찾기
                                                        newest_file = None
                                                        newest_time = 0
                                                        
                                                        for filename in new_files:
                                                            filepath = os.path.join(self.download_dir, filename)
                                                            if os.path.exists(filepath):
                                                                file_time = os.path.getctime(filepath)
                                                                if file_time > newest_time:
                                                                    newest_time = file_time
                                                                    newest_file = filename
                                                        
                                                        if newest_file:
                                                            filepath = os.path.join(self.download_dir, newest_file)
                                                            file_size = os.path.getsize(filepath)
                                                            
                                                            if file_size > 5000:  # 5KB 이상
                                                                # 파일 이름 정리
                                                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                                name, ext = os.path.splitext(newest_file)
                                                                if not ext:
                                                                    ext = '.jpg'
                                                                final_filename = f"imagefx_{timestamp}{ext}"
                                                                final_filepath = os.path.join(self.download_dir, final_filename)
                                                                
                                                                try:
                                                                    if filepath != final_filepath:
                                                                        os.rename(filepath, final_filepath)
                                                                    
                                                                    logger.info(f"✅ 이미지 다운로드 성공! 파일 크기: {file_size:,} bytes")
                                                                    return {
                                                                        'status': 'success',
                                                                        'filename': final_filename,
                                                                        'filepath': final_filepath,
                                                                        'prompt': prompt,
                                                                        'aspect_ratio': aspect_ratio,
                                                                        'generator': 'imagefx',
                                                                        'file_size': file_size,
                                                                        'download_method': 'direct_candidate_click'
                                                                    }
                                                                except Exception as rename_error:
                                                                    logger.warning(f"파일 이름 변경 실패: {rename_error}")
                                                                    return {
                                                                        'status': 'success',
                                                                        'filename': newest_file,
                                                                        'filepath': filepath,
                                                                        'prompt': prompt,
                                                                        'aspect_ratio': aspect_ratio,
                                                                        'generator': 'imagefx',
                                                                        'file_size': file_size,
                                                                        'download_method': 'direct_candidate_click'
                                                                    }
                                                        
                                                        break
                                                
                                                logger.warning("다운로드 대기 시간 초과")
                                                
                                            except Exception as download_error:
                                                logger.warning(f"다운로드 대기 실패: {download_error}")
                                        
                                    except Exception as e:
                                        logger.warning(f"후보 클릭 실패: {e}")
                                        continue
                                        
                        except Exception as e:
                            logger.debug(f"메뉴 아이템 디버깅 실패: {e}")
                        
                        # 기존 선택자 방식은 상단에서 시도했으므로 생략
                        
                    except Exception as e:
                        logger.warning(f"더보기 버튼 클릭 실패: {e}")
                        
                else:
                    logger.debug("더보기 버튼을 찾지 못함, 직접 다운로드 버튼 검색...")
                    
                    # 더보기 버튼을 찾지 못한 경우 직접 다운로드 버튼 찾기
                    for i, selector in enumerate(download_menu_selectors):
                        try:
                            logger.debug(f"다운로드 선택자 시도 {i+1}/{len(download_menu_selectors)}: {selector}")
                            
                            elements = await page.locator(selector).all()
                            logger.debug(f"  -> {len(elements)}개 요소 발견")
                            
                            for j, element in enumerate(elements):
                                try:
                                    # 요소가 보이고 클릭 가능한지 확인
                                    is_visible = await element.is_visible()
                                    if not is_visible:
                                        continue
                                    
                                    # 요소가 실제로 클릭 가능한지 확인
                                    try:
                                        box = await element.bounding_box()
                                        if not box or box['width'] < 10 or box['height'] < 10:
                                            continue
                                    except:
                                        continue
                                    
                                    download_button = element
                                    logger.info(f"✅ 다운로드 요소 발견: 선택자 '{selector}', 요소 {j+1}")
                                    break
                                    
                                except Exception as e:
                                    logger.debug(f"  -> 요소 {j+1} 처리 중 오류: {e}")
                                    continue
                            
                            if download_button:
                                break
                                
                        except Exception as e:
                            logger.debug(f"선택자 '{selector}' 시도 중 오류: {e}")
                            continue
                
                # 다운로드 메뉴 아이템을 찾았으면 클릭 시도
                if download_button:
                    logger.info("📥 다운로드 메뉴 아이템 클릭 시도...")
                    
                    try:
                        # 다운로드 이벤트 리스너 설정
                        if not download_promise:
                            try:
                                # 파일 시스템 방식으로 대체
                                existing_files_before = set(os.listdir(self.download_dir))
                                logger.info("파일 시스템 기반 다운로드 감지 설정 완료")
                            except Exception as e:
                                logger.warning(f"다운로드 감지 설정 오류: {e}")
                        
                        # 다운로드 버튼 클릭 전 준비
                        logger.info("다운로드 버튼 클릭 준비...")
                        
                        # 요소가 화면에 보이도록 스크롤
                        try:
                            await download_button.scroll_into_view_if_needed()
                            await page.wait_for_timeout(1000)
                            logger.info("요소 스크롤 완료")
                        except Exception as e:
                            logger.warning(f"스크롤 실패: {e}")
                        
                        # 클릭 시도 순서: 일반 클릭 -> JavaScript 클릭 -> 포스 클릭
                        click_success = False
                        
                        # 1. 일반 클릭 시도
                        try:
                            logger.info("🔑 일반 클릭 시도...")
                            await download_button.click(timeout=10000)
                            click_success = True
                            logger.info("✅ 일반 클릭 성공")
                        except Exception as e:
                            logger.warning(f"일반 클릭 실패: {e}")
                        
                        # 2. JavaScript 클릭 시도
                        if not click_success:
                            try:
                                logger.info("🔑 JavaScript 클릭 시도...")
                                await page.evaluate('arguments[0].click()', download_button)
                                click_success = True
                                logger.info("✅ JavaScript 클릭 성공")
                            except Exception as e:
                                logger.warning(f"JavaScript 클릭 실패: {e}")
                        
                        # 3. 포스 클릭 시도 (최후 수단)
                        if not click_success:
                            try:
                                logger.info("🔑 포스 클릭 시도...")
                                box = await download_button.bounding_box()
                                if box:
                                    x = box['x'] + box['width'] / 2
                                    y = box['y'] + box['height'] / 2
                                    await page.mouse.click(x, y)
                                    click_success = True
                                    logger.info("✅ 포스 클릭 성공")
                                else:
                                    logger.error("요소의 바운딩 박스를 가져올 수 없음")
                            except Exception as e:
                                logger.error(f"포스 클릭 실패: {e}")
                        
                        if not click_success:
                            logger.error("❌ 모든 클릭 방법 실패!")
                            # 다음 시도를 위해 download_promise 초기화
                            download_promise = None
                            continue
                        
                        # 다운로드 완료 대기
                        logger.info("📥 다운로드 완료 대기 중...")
                        
                        try:
                            # 파일 시스템 기반 대기
                            for wait_time in range(30):  # 30초 대기
                                await page.wait_for_timeout(1000)
                                
                                # 새 파일 확인
                                current_files = set(os.listdir(self.download_dir))
                                new_files = current_files - existing_files_before
                                
                                if new_files:
                                    # 최신 파일 찾기
                                    newest_file = None
                                    newest_time = 0
                                    
                                    for new_filename in new_files:
                                        new_filepath = os.path.join(self.download_dir, new_filename)
                                        if os.path.exists(new_filepath):
                                            file_time = os.path.getctime(new_filepath)
                                            if file_time > newest_time:
                                                newest_time = file_time
                                                newest_file = new_filename
                                    
                                    if newest_file:
                                        file_path = os.path.join(self.download_dir, newest_file)
                                        file_size = os.path.getsize(file_path)
                                        
                                        if file_size > 1000:  # 1KB 이상
                                            # 파일명 정리
                                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            name, ext = os.path.splitext(newest_file)
                                            if not ext:
                                                ext = '.jpg'
                                            filename = f"imagefx_{timestamp}{ext}"
                                            filepath = os.path.join(self.download_dir, filename)
                                            
                                            try:
                                                if file_path != filepath:
                                                    os.rename(file_path, filepath)
                                                
                                                logger.info(f"✅ 이미지 다운로드 성공! 파일 크기: {file_size:,} bytes")
                                                return {
                                                    'status': 'success',
                                                    'filename': filename,
                                                    'filepath': filepath,
                                                    'prompt': prompt,
                                                    'aspect_ratio': aspect_ratio,
                                                    'generator': 'imagefx',
                                                    'file_size': file_size,
                                                    'download_method': 'download_button'
                                                }
                                            except Exception as rename_error:
                                                logger.warning(f"파일 이름 변경 실패: {rename_error}")
                                                # 원본 파일 그대로 반환
                                                return {
                                                    'status': 'success',
                                                    'filename': newest_file,
                                                    'filepath': file_path,
                                                    'prompt': prompt,
                                                    'aspect_ratio': aspect_ratio,
                                                    'generator': 'imagefx',
                                                    'file_size': file_size,
                                                    'download_method': 'download_button'
                                                }
                                        else:
                                            logger.warning(f"⚠️ 다운로드된 파일이 너무 작음: {file_size} bytes")
                            
                            logger.warning("📥 다운로드 대기 시간 초과")
                                
                        except Exception as download_error:
                            logger.warning(f"다운로드 대기 중 오류: {download_error}")
                            
                    except Exception as e:
                        logger.warning(f"다운로드 버튼 클릭 실패: {e}")
                        
                else:
                    # 다운로드 버튼을 찾지 못한 경우, 기존 스크린샷 방식으로 폴백
                    logger.debug("다운로드 버튼을 찾지 못함, 이미지 확인 중...")
                    
                    # 생성된 이미지가 있는지 확인
                    all_images = await page.locator('img').all()
                    
                    for i, img in enumerate(all_images):
                        try:
                            # 이미지가 보이는지 확인
                            is_visible = await img.is_visible()
                            if not is_visible:
                                continue
                                
                            # 이미지 크기 확인
                            box = await img.bounding_box()
                            if not box:
                                continue
                                
                            # 충분히 큰 이미지인지 확인 (아이콘이나 소형 이미지 제외)
                            if box['width'] > 200 and box['height'] > 200:
                                # 이미지 URL 확인
                                image_url = await img.get_attribute('src') or ''
                                
                                # 기본 이미지 제외
                                excluded_keywords = ['whisk_onboarding', 'onboarding', 'placeholder', 'tutorial', 'sample', 'example']
                                is_excluded = any(keyword in image_url.lower() for keyword in excluded_keywords)
                                
                                if not is_excluded:
                                    logger.info(f"🖼️ 생성된 이미지 발견! 크기: {box['width']}x{box['height']}")
                                    logger.info("다운로드 버튼이 나타날 때까지 계속 대기...")
                                    break
                                    
                        except Exception as e:
                            continue
                
                # 아무것도 찾지 못하면 다음 체크까지 대기
                await page.wait_for_timeout(check_interval * 1000)
                
            except Exception as e:
                logger.debug(f"이미지 대기 중 오류: {e}")
                await page.wait_for_timeout(check_interval * 1000)
        
        # 타임아웃 시 전체 페이지 스크린샷 저장
        logger.warning("⏰ 이미지 생성 대기 시간 초과!")
        
        # 디버깅용 전체 페이지 스크린샷
        screenshot_path = os.path.join(self.download_dir, f"timeout_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"📸 타임아웃 디버깅 스크린샷 저장: {screenshot_path}")
        
        # 마지막으로 스크린샷 방식으로 폴백 시도
        logger.info("🔄 마지막 폴백: 스크린샷 방식으로 시도...")
        try:
            all_images = await page.locator('img').all()
            for i, img in enumerate(all_images):
                try:
                    is_visible = await img.is_visible()
                    if not is_visible:
                        continue
                        
                    box = await img.bounding_box()
                    if not box or box['width'] <= 200 or box['height'] <= 200:
                        continue
                        
                    image_url = await img.get_attribute('src') or ''
                    excluded_keywords = ['whisk_onboarding', 'onboarding', 'placeholder', 'tutorial', 'sample', 'example']
                    is_excluded = any(keyword in image_url.lower() for keyword in excluded_keywords)
                    
                    if not is_excluded:
                        # 스크린샷으로 폴백
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"imagefx_fallback_{timestamp}.png"
                        filepath = os.path.join(self.download_dir, filename)
                        
                        await img.screenshot(path=filepath)
                        
                        if os.path.exists(filepath):
                            file_size = os.path.getsize(filepath)
                            if file_size > 5000:
                                logger.info(f"✅ 폴백 스크린샷 성공! 파일 크기: {file_size:,} bytes")
                                return {
                                    'status': 'success',
                                    'filename': filename,
                                    'filepath': filepath,
                                    'prompt': prompt,
                                    'aspect_ratio': aspect_ratio,
                                    'generator': 'imagefx',
                                    'file_size': file_size,
                                    'download_method': 'screenshot_fallback'
                                }
                        break
                        
                except Exception as e:
                    continue
        except Exception as e:
            logger.error(f"폴백 시도 중 오류: {e}")
        
        raise Exception("이미지 생성 시간 초과. 다운로드 버튼을 찾을 수 없고 생성된 이미지도 확인할 수 없습니다.")
