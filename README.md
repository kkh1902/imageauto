# 🎨 ImageAuto - AI 미디어 생성 플랫폼

ImageFX와 KlingAI를 활용한 이미지 생성부터 동영상 편집까지 통합 플랫폼

## ✨ 주요 기능

- 🖼️ **ImageFX 이미지 생성**: Google ImageFX를 활용한 고품질 이미지 생성
- 🎬 **KlingAI 동영상 생성**: 이미지에서 동영상으로 변환  
- ✂️ **동영상 편집**: FFmpeg 기반 자막, 트리밍, 워터마크 등
- 🔄 **통합 워크플로우**: 이미지 생성부터 편집까지 한번에
- 🌐 **웹 인터페이스**: 직관적인 SPA(Single Page Application)

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/imageauto.git
cd imageauto
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. Playwright 브라우저 설치
```bash
playwright install chromium
```

### 5. 환경 설정
```bash
cp .env.example .env
# .env 파일에서 필요한 설정 수정
```

### 6. 실행
```bash
python run.py
```

브라우저에서 `http://localhost:5000` 접속

## 📝 환경 설정

`.env` 파일에서 다음 설정을 구성하세요:

### 필수 설정
- `SECRET_KEY`: Flask 보안을 위한 시크릿 키
- `GOOGLE_EMAIL`, `GOOGLE_PASSWORD`: ImageFX 사용을 위한 Google 계정

### 선택 설정  
- `KLINGAI_API_KEY`: KlingAI 동영상 생성을 위한 API 키 (없으면 플레이스홀더 사용)
- `IMAGEFX_HEADLESS`: 브라우저 창 표시 여부 (true=숨김, false=표시)
- `FFMPEG_PATH`: FFmpeg 실행 파일 경로 (기본: ffmpeg)

## 🎯 사용법

### 이미지 생성
1. "이미지 생성" 탭 선택
2. 원하는 이미지 설명 입력
3. 가로세로 비율 선택
4. "이미지 생성" 버튼 클릭

### 동영상 생성
1. "동영상 생성" 탭 선택
2. 소스 이미지 업로드 또는 생성된 이미지 사용
3. 동영상 움직임 설명 입력
4. "동영상 생성" 버튼 클릭

### 동영상 편집
1. "동영상 편집" 탭 선택
2. 편집할 동영상 업로드
3. 편집 작업 선택 (자막, 트리밍, 워터마크 등)
4. "편집 시작" 버튼 클릭

### 통합 워크플로우
1. "워크플로우" 탭 선택
2. 이미지 프롬프트와 동영상 프롬프트 입력
3. 편집 옵션 선택 (선택사항)
4. "워크플로우 시작" 버튼 클릭

## 🛠️ 기술 스택

- **Backend**: Flask, Python
- **Frontend**: HTML, CSS, JavaScript
- **Browser Automation**: Playwright
- **Video Processing**: FFmpeg
- **APIs**: Google ImageFX, KlingAI

## 📁 프로젝트 구조

```
imageauto/
├── 📁 app/                    # Flask 애플리케이션
│   ├── 📁 routes/            # API 라우트
│   ├── 📁 services/          # 비즈니스 로직
│   ├── 📁 static/            # CSS, JS 파일
│   └── 📁 templates/         # HTML 템플릿
├── 📁 uploads/               # 업로드된 미디어 파일
├── .env.example              # 환경 설정 예시
├── config.py                 # Flask 설정
├── requirements.txt          # Python 의존성
└── run.py                   # 애플리케이션 실행 파일
```

## ⚙️ 고급 설정

### Headless 모드
브라우저 창을 숨기려면:
```env
IMAGEFX_HEADLESS=true
```

### 플레이스홀더 모드
API 키 없이 테스트하려면:
```env
USE_PLACEHOLDER_GENERATOR=true
```

## 🔧 문제 해결

### 브라우저 관련 오류
```bash
playwright install chromium
```

### FFmpeg 오류  
FFmpeg가 설치되어 있는지 확인하세요:
```bash
ffmpeg -version
```

### Google 로그인 오류
- 2단계 인증이 설정된 계정은 앱 비밀번호 사용
- 처음 로그인 시 `IMAGEFX_HEADLESS=false`로 설정

## 📜 라이선스

MIT License

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 지원

문제가 발생하면 GitHub Issues에 보고해주세요.
