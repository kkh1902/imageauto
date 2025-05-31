#!/usr/bin/env python3
"""
KlingAI 사이트 구조 분석 및 Create/Video 버튼 클릭 스크립트
"""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_and_click_kling():
    """KlingAI 사이트 분석 및 Create/Video 버튼 클릭"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # 브라우저 창 표시
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # 브라우저 콘솔 로그 출력
            page.on('console', lambda msg: logger.info(f"🌐 브라우저: {msg.text}"))
            
            try:
                # 1. KlingAI 페이지로 이동
                logger.info("🌐 KlingAI 웹사이트 접속 중...")
                await page.goto("https://klingai.com/global/", wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                logger.info(f"📍 현재 페이지: {page.url}")
                logger.info(f"📖 페이지 제목: {await page.title()}")
                
                # 2. 페이지 구조 분석
                logger.info("🔍 페이지 구조 분석 중...")
                
                analysis_result = await page.evaluate("""
                    () => {
                        const result = {
                            createButtons: [],
                            videoElements: [],
                            menuItems: [],
                            allClickableElements: []
                        };
                        
                        // Create 버튼 찾기
                        const createElements = document.querySelectorAll('*');
                        createElements.forEach((el, index) => {
                            const text = el.textContent || '';
                            if (text.toLowerCase().includes('create') && text.length < 50) {
                                result.createButtons.push({
                                    index,
                                    text: text.trim(),
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    isVisible: el.offsetParent !== null,
                                    isClickable: el.tagName === 'BUTTON' || el.tagName === 'A' || 
                                                el.getAttribute('role') === 'button' ||
                                                window.getComputedStyle(el).cursor === 'pointer'
                                });
                            }
                        });
                        
                        // Video 관련 요소 찾기
                        const videoElements = document.querySelectorAll('*');
                        videoElements.forEach((el, index) => {
                            const text = el.textContent || '';
                            if (text.toLowerCase().includes('video') && text.length < 50) {
                                result.videoElements.push({
                                    index,
                                    text: text.trim(),
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    isVisible: el.offsetParent !== null,
                                    isClickable: el.tagName === 'BUTTON' || el.tagName === 'A' || 
                                                el.getAttribute('role') === 'button' ||
                                                window.getComputedStyle(el).cursor === 'pointer'
                                });
                            }
                        });
                        
                        // menu-item 클래스 요소들
                        const menuItems = document.querySelectorAll('.menu-item, [class*="menu"]');
                        menuItems.forEach((el, index) => {
                            result.menuItems.push({
                                index,
                                text: el.textContent ? el.textContent.trim() : '',
                                className: el.className,
                                id: el.id,
                                isVisible: el.offsetParent !== null
                            });
                        });
                        
                        // 모든 클릭 가능한 요소
                        const clickableElements = document.querySelectorAll('button, a, [role="button"], [onclick]');
                        clickableElements.forEach((el, index) => {
                            if (el.offsetParent !== null) {  // 보이는 요소만
                                result.allClickableElements.push({
                                    index,
                                    text: el.textContent ? el.textContent.trim().substring(0, 100) : '',
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id
                                });
                            }
                        });
                        
                        return result;
                    }
                """)
                
                # 분석 결과 출력
                logger.info("📊 사이트 구조 분석 결과:")
                
                logger.info(f"🎯 Create 관련 요소 {len(analysis_result['createButtons'])}개:")
                for btn in analysis_result['createButtons']:
                    if btn['isVisible'] and btn['isClickable']:
                        logger.info(f"   ✅ '{btn['text']}' - {btn['tagName']}.{btn['className']}")
                    else:
                        logger.info(f"   ⚪ '{btn['text']}' - {btn['tagName']}.{btn['className']} (숨김/클릭불가)")
                
                logger.info(f"🎯 Video 관련 요소 {len(analysis_result['videoElements'])}개:")
                for vid in analysis_result['videoElements']:
                    if vid['isVisible'] and vid['isClickable']:
                        logger.info(f"   ✅ '{vid['text']}' - {vid['tagName']}.{vid['className']}")
                    else:
                        logger.info(f"   ⚪ '{vid['text']}' - {vid['tagName']}.{vid['className']} (숨김/클릭불가)")
                
                logger.info(f"🎯 메뉴 아이템 {len(analysis_result['menuItems'])}개:")
                for menu in analysis_result['menuItems']:
                    if menu['isVisible']:
                        logger.info(f"   📋 '{menu['text'][:50]}...' - {menu['className']}")
                
                # 3. Create 버튼 클릭 시도
                logger.info("🎬 Create 버튼 클릭 시도...")
                
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
                    logger.info(f"📍 Create 클릭 후 URL: {new_url}")
                    
                    # 4. Video 버튼 클릭 시도
                    logger.info("🎬 Video 버튼 클릭 시도...")
                    
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
                        
                        final_url = page.url
                        logger.info(f"📍 Video 클릭 후 URL: {final_url}")
                        
                        # Video Generation 페이지 요소 확인
                        indicators = [
                            'text="Video Generation"',
                            'text="Image to Video"',
                            'text="Click / Drop / Paste"',
                            'input[type="file"]',
                            'textarea'
                        ]
                        
                        for indicator in indicators:
                            count = await page.locator(indicator).count()
                            if count > 0:
                                logger.info(f"✅ Video Generation 페이지 요소 발견: {indicator} ({count}개)")
                    else:
                        logger.warning("❌ Video 버튼 자동 클릭 실패")
                        logger.info("💡 수동으로 Video 버튼을 클릭해보세요")
                else:
                    logger.warning("❌ Create 버튼 자동 클릭 실패")
                    logger.info("💡 수동으로 Create 버튼을 클릭해보세요")
                
                # 5. 브라우저를 열어둔 상태로 대기
                logger.info("✅ 분석 및 클릭 시도 완료!")
                logger.info("👀 브라우저를 확인하고 필요시 수동으로 클릭하세요")
                logger.info("⏳ 60초 후 자동으로 닫힙니다...")
                await page.wait_for_timeout(60000)
                
            finally:
                await browser.close()
                
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    asyncio.run(analyze_and_click_kling())
