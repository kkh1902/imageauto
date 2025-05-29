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
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
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
        await prompt_input.fill("")
        await page.wait_for_timeout(500)
        await prompt_input.type(prompt, delay=50)
        
        logger.info("프롬프트 입력 완료")

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
        
        # 생성 시작 확인을 위한 잠시 대기
        await page.wait_for_timeout(3000)

    async def _wait_and_download_image(self, page, prompt, aspect_ratio):
        """생성 완료 대기 및 이미지 다운로드"""
        logger.info("🎨 이미지 생성 완료 대기 중...")
        
        # 생성 완료까지 최대 대기 시간 (5분)
        max_wait_time = 300
        check_interval = 5
        
        for elapsed in range(0, max_wait_time, check_interval):
            try:
                # 진행 상황 로그
                if elapsed % 30 == 0 and elapsed > 0:
                    logger.info(f"⏳ 이미지 생성 대기 중... ({elapsed}/{max_wait_time}초)")
                
                # 더 간단하고 확실한 이미지 찾기
                logger.debug(f"🔍 이미지 검색 시도 {elapsed}초...")
                
                # 모든 img 요소 찾기
                all_images = await page.locator('img').all()
                logger.debug(f"📷 전체 img 요소 {len(all_images)}개 발견")
                
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
                            
                        logger.debug(f"이미지 {i+1}: 크기 {box['width']}x{box['height']}")
                        
                        # 충분히 큰 이미지인지 확인 (아이콘이나 소형 이미지 제외)
                        if box['width'] > 200 and box['height'] > 200:
                            # 이미지 URL 확인
                            image_url = await img.get_attribute('src') or ''
                            
                            # 기본 이미지 제외 (온보딩 이미지 등)
                            excluded_keywords = ['whisk_onboarding', 'onboarding', 'placeholder', 'tutorial', 'sample', 'example']
                            is_excluded = any(keyword in image_url.lower() for keyword in excluded_keywords)
                            
                            if is_excluded:
                                logger.debug(f"이미지 {i+1} 제외: 기본 이미지 ({image_url[:50]}...)")
                                continue
                            
                            logger.info(f"✨ 큰 이미지 발견! 크기: {box['width']}x{box['height']}, URL: {image_url[:100] if image_url else 'None'}...")
                            
                            # 즉시 스크린샷으로 다운로드 시도 (가장 확실한 방법)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"imagefx_{timestamp}.png"
                            filepath = os.path.join(self.download_dir, filename)
                            
                            try:
                                logger.info(f"📸 스크린샷 다운로드 시도: {filename}")
                                await img.screenshot(path=filepath)
                                
                                # 파일 확인
                                if os.path.exists(filepath):
                                    file_size = os.path.getsize(filepath)
                                    if file_size > 5000:  # 5KB 이상
                                        logger.info(f"✅ 이미지 다운로드 성공! 파일 크기: {file_size:,} bytes")
                                        return {
                                            'status': 'success',
                                            'filename': filename,
                                            'filepath': filepath,
                                            'prompt': prompt,
                                            'aspect_ratio': aspect_ratio,
                                            'generator': 'imagefx',
                                            'file_size': file_size
                                        }
                                    else:
                                        logger.warning(f"⚠️ 파일이 너무 작음: {file_size} bytes")
                                        # 파일 삭제
                                        try:
                                            os.remove(filepath)
                                        except:
                                            pass
                                else:
                                    logger.warning("❌ 스크린샷 파일이 생성되지 않음")
                                    
                            except Exception as e:
                                logger.warning(f"스크린샷 실패: {e}")
                                
                    except Exception as e:
                        logger.debug(f"이미지 {i+1} 처리 중 오류: {e}")
                        continue
                
                # Canvas 요소도 확인
                all_canvas = await page.locator('canvas').all()
                logger.debug(f"🎨 전체 canvas 요소 {len(all_canvas)}개 발견")
                
                for i, canvas in enumerate(all_canvas):
                    try:
                        is_visible = await canvas.is_visible()
                        if not is_visible:
                            continue
                            
                        box = await canvas.bounding_box()
                        if not box:
                            continue
                            
                        logger.debug(f"Canvas {i+1}: 크기 {box['width']}x{box['height']}")
                        
                        if box['width'] > 200 and box['height'] > 200:
                            logger.info(f"✨ 큰 Canvas 발견! 크기: {box['width']}x{box['height']}")
                            
                            # Canvas 스크린샷 시도
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"imagefx_canvas_{timestamp}.png"
                            filepath = os.path.join(self.download_dir, filename)
                            
                            try:
                                await canvas.screenshot(path=filepath)
                                
                                if os.path.exists(filepath):
                                    file_size = os.path.getsize(filepath)
                                    if file_size > 5000:
                                        logger.info(f"✅ Canvas 스크린샷 성공! 파일 크기: {file_size:,} bytes")
                                        return {
                                            'status': 'success',
                                            'filename': filename,
                                            'filepath': filepath,
                                            'prompt': prompt,
                                            'aspect_ratio': aspect_ratio,
                                            'generator': 'imagefx',
                                            'file_size': file_size
                                        }
                                        
                            except Exception as e:
                                logger.warning(f"Canvas 스크린샷 실패: {e}")
                                
                    except Exception as e:
                        logger.debug(f"Canvas {i+1} 처리 중 오류: {e}")
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
        
        # 현재 페이지의 모든 이미지 정보 덤프
        try:
            logger.info("🔍 타임아웃 시 모든 이미지 정보:")
            all_images_final = await page.locator('img').all()
            for i, img in enumerate(all_images_final[:10]):  # 최대 10개
                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt')
                    box = await img.bounding_box()
                    is_visible = await img.is_visible()
                    size_info = f"{box['width']}x{box['height']}" if box else "No box"
                    logger.info(f"  이미지 {i+1}: visible={is_visible}, size={size_info}, src={src[:50] if src else 'None'}..., alt={alt}")
                except:
                    pass
        except:
            pass
        
        raise Exception("이미지 생성 시간 초과. 생성된 이미지를 찾을 수 없습니다.")
