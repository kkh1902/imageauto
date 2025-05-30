# ImageAuto 가상환경 서버 시작 스크립트
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "    ImageAuto 가상환경 서버 시작" -ForegroundColor Cyan  
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 디렉토리 이동
Set-Location "C:\DEV\imageauto"

# 가상환경 확인 및 생성
if (!(Test-Path "venv")) {
    Write-Host "❌ 가상환경이 없습니다. 가상환경을 생성합니다..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ 가상환경 생성 완료" -ForegroundColor Green
    Write-Host ""
}

# 가상환경 활성화
Write-Host "🔄 가상환경 활성화 중..." -ForegroundColor Blue
& "venv\Scripts\Activate.ps1"

# Python 버전 확인
Write-Host "📍 Python 버전:" -ForegroundColor Magenta
python --version
Write-Host ""

# 패키지 설치
Write-Host "📦 패키지 설치/업데이트 중..." -ForegroundColor Blue
pip install -r requirements.txt

Write-Host ""
Write-Host "🚀 서버 시작 중..." -ForegroundColor Green
Write-Host "📱 브라우저에서 http://localhost:5000 으로 접속하세요" -ForegroundColor Yellow
Write-Host "⏹️  서버를 중지하려면 Ctrl+C를 누르세요" -ForegroundColor Yellow
Write-Host ""

# 서버 실행
python run.py

Write-Host ""
Write-Host "서버가 종료되었습니다." -ForegroundColor Red
Read-Host "아무 키나 누르세요"
