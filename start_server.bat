@echo off
echo ImageAuto 서버 시작...
echo.

REM 가상환경 활성화
call venv\Scripts\activate

REM 필요한 패키지 설치
echo 패키지 설치 중...
pip install -r requirements.txt

REM 서버 실행
echo 서버 시작 중...
python run.py

pause
