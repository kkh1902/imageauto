@echo off
echo ============================================
echo    ImageAuto 가상환경 서버 시작
echo ============================================
echo.

REM 현재 디렉토리를 imageauto로 변경
cd /d C:\DEV\imageauto

REM 가상환경이 있는지 확인
if not exist "venv" (
    echo ❌ 가상환경이 없습니다. 가상환경을 생성합니다...
    python -m venv venv
    echo ✅ 가상환경 생성 완료
    echo.
)

REM 가상환경 활성화
echo 🔄 가상환경 활성화 중...
call venv\Scripts\activate

REM Python 버전 확인
echo 📍 Python 버전:
python --version
echo.

REM 필요한 패키지 설치
echo 📦 패키지 설치/업데이트 중...
pip install -r requirements.txt

echo.
echo 🚀 서버 시작 중...
echo 📱 브라우저에서 http://localhost:5000 으로 접속하세요
echo ⏹️  서버를 중지하려면 Ctrl+C를 누르세요
echo.

REM 서버 실행
python run.py

echo.
echo 서버가 종료되었습니다.
pause
