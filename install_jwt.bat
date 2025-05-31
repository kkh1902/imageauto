@echo off
echo PyJWT 패키지 설치 중...
echo.

REM 가상환경 활성화
call venv\Scripts\activate

REM PyJWT 설치
echo PyJWT 설치 중...
pip install PyJWT==2.8.0

REM 설치 확인
echo.
echo 설치된 패키지 확인:
pip list | findstr PyJWT

echo.
echo PyJWT 설치 완료!
pause
