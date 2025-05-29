import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PlaceholderGenerator:
    """
    개발/테스트용 플레이스홀더 이미지 생성기
    실제 API가 준비되지 않았을 때 사용
    """
    def __init__(self):
        self.download_dir = os.path.join(os.path.dirname(__file__), '../../../../uploads/images')
        os.makedirs(self.download_dir, exist_ok=True)
    
    async def generate_image(self, prompt, aspect_ratio="9:16"):
        """
        플레이스홀더 이미지를 생성합니다.
        
        Args:
            prompt (str): 이미지 생성 프롬프트
            aspect_ratio (str): 가로세로 비율
            
        Returns:
            dict: 생성된 이미지 정보
        """
        try:
            # 비율에 따른 이미지 크기 설정
            sizes = {
                "9:16": (720, 1280),
                "16:9": (1280, 720),
                "1:1": (1024, 1024),
                "4:3": (1024, 768),
                "3:4": (768, 1024)
            }
            
            width, height = sizes.get(aspect_ratio, (1024, 1024))
            
            # 이미지 생성
            image = Image.new('RGB', (width, height), color=(60, 60, 60))
            draw = ImageDraw.Draw(image)
            
            # 배경 그라데이션 효과
            for i in range(height):
                color = int(60 + (i / height) * 40)
                draw.line([(0, i), (width, i)], fill=(color, color, color + 10))
            
            # 텍스트 추가
            try:
                # 시스템 폰트 사용 시도
                title_font = ImageFont.truetype("arial.ttf", 48)
                text_font = ImageFont.truetype("arial.ttf", 24)
            except:
                # 기본 폰트 사용
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # 제목
            title = "AI Generated Placeholder"
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            draw.text((title_x, height // 4), title, font=title_font, fill=(255, 255, 255))
            
            # 프롬프트 표시 (줄바꿈 처리)
            prompt_lines = []
            words = prompt.split()
            current_line = ""
            max_width = width - 100
            
            for word in words:
                test_line = f"{current_line} {word}".strip()
                bbox = draw.textbbox((0, 0), test_line, font=text_font)
                if bbox[2] - bbox[0] <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        prompt_lines.append(current_line)
                    current_line = word
            
            if current_line:
                prompt_lines.append(current_line)
            
            # 프롬프트 텍스트 그리기
            y_offset = height // 2
            for line in prompt_lines[:5]:  # 최대 5줄까지만 표시
                bbox = draw.textbbox((0, 0), line, font=text_font)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) // 2
                draw.text((x, y_offset), line, font=text_font, fill=(200, 200, 200))
                y_offset += 30
            
            # 하단에 정보 추가
            info_text = f"Size: {width}x{height} | Ratio: {aspect_ratio}"
            info_bbox = draw.textbbox((0, 0), info_text, font=text_font)
            info_width = info_bbox[2] - info_bbox[0]
            draw.text(((width - info_width) // 2, height - 60), info_text, font=text_font, fill=(150, 150, 150))
            
            # 타임스탬프
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ts_bbox = draw.textbbox((0, 0), timestamp, font=text_font)
            ts_width = ts_bbox[2] - ts_bbox[0]
            draw.text(((width - ts_width) // 2, height - 30), timestamp, font=text_font, fill=(150, 150, 150))
            
            # 파일 저장
            timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"placeholder_{timestamp_file}.png"
            filepath = os.path.join(self.download_dir, filename)
            
            image.save(filepath, 'PNG')
            
            logger.info(f"플레이스홀더 이미지 생성 완료: {filename}")
            
            return {
                'status': 'success',
                'filename': filename,
                'filepath': filepath,
                'prompt': prompt,
                'aspect_ratio': aspect_ratio,
                'generator': 'placeholder'
            }
            
        except Exception as e:
            logger.error(f"플레이스홀더 이미지 생성 중 오류: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
