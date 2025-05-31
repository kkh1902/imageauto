@echo off
echo.
echo ============================================
echo   ImageAuto PyJWT 설치 및 서버 재시작
echo ============================================
echo.

echo 1단계: 가상환경 활성화...
call venv\Scripts\activate

echo.
echo 2단계: PyJWT 패키지 설치...
pip install PyJWT==2.8.0

echo.
echo 3단계: 설치 확인...
python -c "import jwt; print('✅ PyJWT 설치 성공! 버전:', jwt.__version__)"

echo.
echo 4단계: 필요한 패키지 모두 설치...
pip install -r requirements.txt

echo.
echo ============================================
echo   설치 완료! 이제 서버를 재시작하세요
echo ============================================
echo.
echo 서버 시작: python run.py
echo.
pause
