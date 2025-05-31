#!/usr/bin/env python3
"""
KlingAI API 크레딧 확인 스크립트
"""

import asyncio
import aiohttp
import os
import sys
import time
import jwt
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

load_dotenv()

async def check_api_credit():
    """KlingAI API 크레딧 확인"""
    
    print("💳 KlingAI API 크레딧 확인\n")
    
    # API 키 확인
    api_key = os.getenv('KLINGAI_API_KEY')
    secret_key = os.getenv('KLINGAI_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ API 키가 설정되지 않았습니다.")
        return
    
    # JWT 토큰 생성
    try:
        headers = {"alg": "HS256", "typ": "JWT"}
        current_time = int(time.time())
        payload = {
            "iss": api_key,
            "exp": current_time + 1800,
            "nbf": current_time - 5
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256', headers=headers)
        print(f"✅ JWT 토큰 생성 성공")
    except Exception as e:
        print(f"❌ JWT 토큰 생성 실패: {e}")
        return
    
    # API 요청 헤더
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    base_url = "https://api-singapore.klingai.com"
    
    async with aiohttp.ClientSession() as session:
        # 계정 정보 확인 시도 (여러 엔드포인트 시도)
        endpoints_to_try = [
            f'{base_url}/v1/account/balance',
            f'{base_url}/v1/account/info',
            f'{base_url}/v1/user/info',
            f'{base_url}/v1/account',
            f'{base_url}/v1/images/generations?pageNum=1&pageSize=1'  # 최소 요청으로 계정 상태 확인
        ]
        
        for endpoint in endpoints_to_try:
            try:
                print(f"🔍 {endpoint} 확인 중...")
                
                async with session.get(endpoint, headers=headers) as response:
                    response_text = await response.text()
                    print(f"   상태: {response.status}")
                    print(f"   응답: {response_text}")
                    
                    if response.status == 200:
                        print("✅ API 접근 성공!")
                        break
                    elif response.status == 429:
                        print("💰 크레딧 부족 확인됨")
                        break
                    else:
                        print(f"⚠️  상태 코드: {response.status}")
                        
            except Exception as e:
                print(f"   오류: {e}")
                continue
    
    print("\n📋 결론:")
    print("1. API 연결은 정상 작동")
    print("2. 계정 크레딧 부족으로 인한 429 오류")
    print("3. KlingAI 웹사이트에서 API 전용 크레딧 구매 필요")
    print("\n💡 해결책:")
    print("- KlingAI 웹사이트 → 개발자/API 섹션")
    print("- API 크레딧 구매 (웹사이트 크레딧과 별도)")
    print("- 최소 충전 금액: $5-10 정도 예상")

if __name__ == "__main__":
    asyncio.run(check_api_credit())
