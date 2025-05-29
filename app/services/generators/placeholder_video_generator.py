import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import logging
import shutil

logger = logging.getLogger(__name__)

class PlaceholderVideoGenerator:
    """
    개발/테스트용 플레이스홀더 비디오 생성기
    실제 API가 준비되지 않았을 때 사용
    """
    def __init__(self):
        self.download_dir = os.path.join(os.path.dirname(__file__), '../../../../uploads/videos')
        os.makedirs(self.download_dir, exist_ok=True)
    
    async def generate_video(self, image_path, prompt, negative_prompt="", cfg_scale=0.5, mode="std", duration=5):
        """
        플레이스홀더 비디오를 생성합니다 (실제로는 GIF 애니메이션)
        
        Args:
            image_path (str): 입력 이미지 경로
            prompt (str): 동영상 생성 프롬프트
            negative_prompt (str): 네거티브 프롬프트
            cfg_scale (float): Creativity Scale
            mode (str): 생성 모드
            duration (int): 동영상 길이
            
        Returns:
            dict: 생성된 동영상 정보
        """
        try:
            # 이미지 로드 또는 생성
            if os.path.exists(image_path):
                base_img = Image.open(image_path)
                # 크기 조정 (너무 크면 처리 시간이 오래 걸림)
                max_size = 800
                if base_img.width > max_size or base_img.height > max_size:
                    base_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            else:
                base_img = Image.new('RGB', (640, 480), color=(60, 60, 60))
            
            width, height = base_img.size
            
            # GIF 프레임 생성
            frames = []
            fps = 10  # GIF는 낮은 프레임레이트 사용
            total_frames = min(fps * duration, 50)  # 최대 50프레임으로 제한
            
            for i in range(total_frames):
                # 프레임 생성
                frame = base_img.copy()
                draw = ImageDraw.Draw(frame)
                
                # 배경에 반투명 오버레이
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 100))
                frame.paste(overlay, (0, 0), overlay)
                
                # 진행 상태 바
                progress = i / total_frames
                bar_height = 10
                bar_width = int(width * progress)
                draw.rectangle([0, height-bar_height, bar_width, height], fill=(0, 255, 0))
                
                # 텍스트 추가
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                    small_font = ImageFont.truetype("arial.ttf", 14)
                except:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
                
                # 제목
                title = "AI Video Generation (Test)"
                draw.text((10, 10), title, font=font, fill=(255, 255, 255))
                
                # 프레임 정보
                frame_text = f"Frame {i+1}/{total_frames} | Duration: {duration}s | Mode: {mode}"
                draw.text((10, 40), frame_text, font=small_font, fill=(200, 200, 200))
                
                # 프롬프트 표시
                prompt_text = f"Prompt: {prompt[:60]}..."
                draw.text((10, height-40), prompt_text, font=small_font, fill=(180, 180, 180))
                
                # 애니메이션 효과 (간단한 펄스)
                pulse = int(10 * abs(progress - 0.5))
                draw.ellipse([width//2-20-pulse, height//2-20-pulse, 
                             width//2+20+pulse, height//2+20+pulse], 
                            outline=(255, 255, 255), width=2)
                
                frames.append(frame)
            
            # GIF로 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_video_{timestamp}.gif"
            filepath = os.path.join(self.download_dir, filename)
            
            # GIF 저장
            frames[0].save(
                filepath,
                save_all=True,
                append_images=frames[1:],
                duration=100,  # 각 프레임 100ms (10fps)
                loop=0
            )
            
            # MP4처럼 보이도록 파일명 변경 (선택사항)
            # 실제로는 GIF이지만 사용자 경험을 위해
            mp4_filename = filename.replace('.gif', '_test.mp4')
            mp4_filepath = filepath.replace('.gif', '_test.mp4')
            
            # 참고용 텍스트 파일 생성
            info_path = filepath.replace('.gif', '_info.txt')
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(f"Test Video Information\n")
                f.write(f"===================\n")
                f.write(f"Type: Placeholder (GIF Animation)\n")
                f.write(f"Original Image: {os.path.basename(image_path)}\n")
                f.write(f"Prompt: {prompt}\n")
                f.write(f"Negative Prompt: {negative_prompt}\n")
                f.write(f"Duration: {duration} seconds\n")
                f.write(f"Mode: {mode}\n")
                f.write(f"CFG Scale: {cfg_scale}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"\nNote: This is a test placeholder. Use KlingAI API for real video generation.\n")
            
            logger.info(f"플레이스홀더 비디오(GIF) 생성 완료: {filename}")
            
            return {
                'status': 'success',
                'filename': filename,
                'filepath': filepath,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'duration': duration,
                'mode': mode,
                'generator': 'placeholder',
                'note': 'This is a test GIF animation, not a real video'
            }
            
        except Exception as e:
            logger.error(f"플레이스홀더 비디오 생성 중 오류: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
