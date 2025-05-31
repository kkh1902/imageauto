#!/usr/bin/env python3
"""
PyJWT 설치 스크립트
"""

import subprocess
import sys
import os

def install_pyjwt():
    """PyJWT 패키지 설치"""
    
    print("🔧 PyJWT 패키지 설치 중...")
    
    try:
        # pip를 사용하여 PyJWT 설치
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'PyJWT==2.8.0'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PyJWT 설치 성공!")
            print(result.stdout)
        else:
            print("❌ PyJWT 설치 실패:")
            print(result.stderr)
            return False
            
        # 설치 확인
        try:
            import jwt
            print(f"✅ PyJWT 설치 확인 완료! 버전: {jwt.__version__}")
            return True
        except ImportError:
            print("❌ PyJWT import 실패")
            return False
            
    except Exception as e:
        print(f"❌ 설치 중 오류: {e}")
        return False

if __name__ == "__main__":
    if install_pyjwt():
        print("\n🎉 PyJWT 설치가 완료되었습니다!")
        print("이제 서버를 다시 시작해주세요: python run.py")
    else:
        print("\n⚠️ PyJWT 설치에 실패했습니다.")
        print("수동으로 다음 명령어를 실행해주세요:")
        print("pip install PyJWT==2.8.0")
