import os
import ffmpeg
import logging
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)

class VideoEditor:
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(__file__), '../../../../uploads/edited')
        os.makedirs(self.output_dir, exist_ok=True)
        
    def add_subtitles(self, video_path, subtitles, font_size=24, font_color='white', position='bottom'):
        """
        동영상에 자막을 추가합니다.
        
        Args:
            video_path (str): 입력 동영상 경로
            subtitles (list): 자막 정보 리스트 [{'text': '자막', 'start': 0, 'end': 2}, ...]
            font_size (int): 폰트 크기
            font_color (str): 폰트 색상
            position (str): 자막 위치 (top, center, bottom)
            
        Returns:
            dict: 편집된 동영상 정보
        """
        try:
            # SRT 파일 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            srt_filename = f"subtitles_{timestamp}.srt"
            srt_path = os.path.join(self.output_dir, srt_filename)
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                for idx, subtitle in enumerate(subtitles, 1):
                    f.write(f"{idx}\n")
                    f.write(f"{self._seconds_to_srt_time(subtitle['start'])} --> {self._seconds_to_srt_time(subtitle['end'])}\n")
                    f.write(f"{subtitle['text']}\n\n")
            
            # 출력 파일명 생성
            output_filename = f"edited_{timestamp}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # FFmpeg 명령어 생성
            y_position = {
                'top': 50,
                'center': '(h-text_h)/2',
                'bottom': 'h-th-50'
            }.get(position, 'h-th-50')
            
            # 자막 스타일 설정
            subtitle_filter = f"subtitles={srt_path}:force_style='FontSize={font_size},PrimaryColour=&H{self._color_to_hex(font_color)}&,Alignment=2'"
            
            # FFmpeg 실행
            (
                ffmpeg
                .input(video_path)
                .output(output_path, vf=subtitle_filter, codec='libx264', audio_codec='aac')
                .overwrite_output()
                .run()
            )
            
            return {
                'status': 'success',
                'filename': output_filename,
                'filepath': output_path,
                'subtitles_added': len(subtitles)
            }
            
        except Exception as e:
            logger.error(f"자막 추가 중 오류 발생: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def trim_video(self, video_path, start_time, end_time):
        """
        동영상을 자릅니다.
        
        Args:
            video_path (str): 입력 동영상 경로
            start_time (float): 시작 시간 (초)
            end_time (float): 종료 시간 (초)
            
        Returns:
            dict: 편집된 동영상 정보
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"trimmed_{timestamp}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            (
                ffmpeg
                .input(video_path, ss=start_time, t=end_time-start_time)
                .output(output_path, codec='copy')
                .overwrite_output()
                .run()
            )
            
            return {
                'status': 'success',
                'filename': output_filename,
                'filepath': output_path,
                'duration': end_time - start_time
            }
            
        except Exception as e:
            logger.error(f"동영상 자르기 중 오류 발생: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def merge_videos(self, video_paths):
        """
        여러 동영상을 하나로 합칩니다.
        
        Args:
            video_paths (list): 합칠 동영상 경로 리스트
            
        Returns:
            dict: 편집된 동영상 정보
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"merged_{timestamp}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 입력 스트림 생성
            inputs = [ffmpeg.input(path) for path in video_paths]
            
            # 동영상 합치기
            (
                ffmpeg
                .concat(*inputs, v=1, a=1)
                .output(output_path, codec='libx264', audio_codec='aac')
                .overwrite_output()
                .run()
            )
            
            return {
                'status': 'success',
                'filename': output_filename,
                'filepath': output_path,
                'videos_merged': len(video_paths)
            }
            
        except Exception as e:
            logger.error(f"동영상 합치기 중 오류 발생: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def add_watermark(self, video_path, watermark_path, position='bottom-right', opacity=0.5):
        """
        동영상에 워터마크를 추가합니다.
        
        Args:
            video_path (str): 입력 동영상 경로
            watermark_path (str): 워터마크 이미지 경로
            position (str): 워터마크 위치
            opacity (float): 투명도 (0-1)
            
        Returns:
            dict: 편집된 동영상 정보
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"watermarked_{timestamp}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 위치 설정
            positions = {
                'top-left': 'x=10:y=10',
                'top-right': 'x=W-w-10:y=10',
                'bottom-left': 'x=10:y=H-h-10',
                'bottom-right': 'x=W-w-10:y=H-h-10',
                'center': 'x=(W-w)/2:y=(H-h)/2'
            }
            
            overlay_position = positions.get(position, positions['bottom-right'])
            
            # FFmpeg 실행
            (
                ffmpeg
                .input(video_path)
                .overlay(
                    ffmpeg.input(watermark_path),
                    overlay_position,
                    **{'enable': f'between(t,0,20)', 'alpha': opacity}
                )
                .output(output_path, codec='libx264', audio_codec='aac')
                .overwrite_output()
                .run()
            )
            
            return {
                'status': 'success',
                'filename': output_filename,
                'filepath': output_path,
                'watermark_added': True
            }
            
        except Exception as e:
            logger.error(f"워터마크 추가 중 오류 발생: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _seconds_to_srt_time(self, seconds):
        """초를 SRT 시간 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')
    
    def _color_to_hex(self, color):
        """색상 이름을 16진수로 변환"""
        colors = {
            'white': 'FFFFFF',
            'black': '000000',
            'red': 'FF0000',
            'green': '00FF00',
            'blue': '0000FF',
            'yellow': 'FFFF00'
        }
        return colors.get(color.lower(), 'FFFFFF')
