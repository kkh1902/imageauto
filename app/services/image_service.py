import os
from PIL import Image, ImageEnhance, ImageFilter
from flask import current_app
from app.services.file_service import FileService

class ImageService:
    """이미지 처리 관련 서비스"""
    
    @staticmethod
    def process_image(filename, options=None):
        """이미지 처리 메인 함수"""
        try:
            if options is None:
                options = {}
            
            # 원본 이미지 로드
            file_path = FileService.get_file_path(filename)
            image = Image.open(file_path)
            
            # 처리된 이미지 복사본 생성
            processed_image = image.copy()
            processing_info = {}
            
            # 리사이즈
            if 'resize' in options:
                processed_image = ImageService._resize_image(processed_image, options['resize'])
                processing_info['resize'] = options['resize']
            
            # 품질 조정
            if 'enhance' in options:
                processed_image = ImageService._enhance_image(processed_image, options['enhance'])
                processing_info['enhance'] = options['enhance']
            
            # 필터 적용
            if 'filter' in options:
                processed_image = ImageService._apply_filter(processed_image, options['filter'])
                processing_info['filter'] = options['filter']
            
            # 포맷 변환
            output_format = options.get('format', 'JPEG')
            
            # 처리된 이미지 저장
            processed_filename = ImageService._generate_processed_filename(filename, options)
            processed_path = FileService.get_file_path(processed_filename)
            
            # JPEG로 저장할 때 RGB 모드로 변환
            if output_format.upper() == 'JPEG' and processed_image.mode != 'RGB':
                processed_image = processed_image.convert('RGB')
            
            processed_image.save(processed_path, format=output_format, quality=95)
            
            return {
                'success': True,
                'processed_filename': processed_filename,
                'processing_info': processing_info,
                'original_size': image.size,
                'processed_size': processed_image.size
            }
            
        except Exception as e:
            current_app.logger.error(f"이미지 처리 오류: {str(e)}")
            return {
                'success': False,
                'error': f'이미지 처리 중 오류가 발생했습니다: {str(e)}'
            }
    
    @staticmethod
    def _resize_image(image, resize_options):
        """이미지 리사이즈"""
        width = resize_options.get('width')
        height = resize_options.get('height')
        maintain_ratio = resize_options.get('maintain_ratio', True)
        
        if width and height:
            if maintain_ratio:
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
        elif width:
            ratio = width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((width, new_height), Image.Resampling.LANCZOS)
        elif height:
            ratio = height / image.height
            new_width = int(image.width * ratio)
            image = image.resize((new_width, height), Image.Resampling.LANCZOS)
        
        return image
    
    @staticmethod
    def _enhance_image(image, enhance_options):
        """이미지 품질 향상"""
        # 밝기 조정
        if 'brightness' in enhance_options:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(enhance_options['brightness'])
        
        # 대비 조정
        if 'contrast' in enhance_options:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(enhance_options['contrast'])
        
        # 색상 조정
        if 'color' in enhance_options:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(enhance_options['color'])
        
        # 선명도 조정
        if 'sharpness' in enhance_options:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(enhance_options['sharpness'])
        
        return image
    
    @staticmethod
    def _apply_filter(image, filter_type):
        """이미지 필터 적용"""
        filter_map = {
            'blur': ImageFilter.BLUR,
            'sharpen': ImageFilter.SHARPEN,
            'smooth': ImageFilter.SMOOTH,
            'edge_enhance': ImageFilter.EDGE_ENHANCE,
            'contour': ImageFilter.CONTOUR,
            'emboss': ImageFilter.EMBOSS
        }
        
        if filter_type in filter_map:
            return image.filter(filter_map[filter_type])
        
        return image
    
    @staticmethod
    def _generate_processed_filename(original_filename, options):
        """처리된 파일의 이름 생성"""
        name, ext = os.path.splitext(original_filename)
        
        # 옵션에 따른 접미사 생성
        suffix_parts = []
        
        if 'resize' in options:
            resize_opt = options['resize']
            if 'width' in resize_opt and 'height' in resize_opt:
                suffix_parts.append(f"{resize_opt['width']}x{resize_opt['height']}")
            elif 'width' in resize_opt:
                suffix_parts.append(f"w{resize_opt['width']}")
            elif 'height' in resize_opt:
                suffix_parts.append(f"h{resize_opt['height']}")
        
        if 'filter' in options:
            suffix_parts.append(options['filter'])
        
        if 'enhance' in options:
            suffix_parts.append('enhanced')
        
        # 포맷 변경
        output_format = options.get('format', '').lower()
        if output_format and output_format != ext[1:].lower():
            ext = f'.{output_format}'
        
        # 접미사가 있으면 추가
        if suffix_parts:
            suffix = '_' + '_'.join(suffix_parts)
        else:
            suffix = '_processed'
        
        return f"{name}{suffix}{ext}"
    
    @staticmethod
    def get_image_info(filename):
        """이미지 정보 조회"""
        try:
            file_path = FileService.get_file_path(filename)
            if not os.path.exists(file_path):
                return None
            
            with Image.open(file_path) as image:
                info = {
                    'filename': filename,
                    'format': image.format,
                    'mode': image.mode,
                    'size': image.size,
                    'width': image.width,
                    'height': image.height,
                    'file_size': FileService.get_file_size(filename),
                    'file_size_formatted': FileService.format_file_size(FileService.get_file_size(filename))
                }
                
                # EXIF 데이터가 있으면 추가
                if hasattr(image, '_getexif') and image._getexif():
                    info['has_exif'] = True
                else:
                    info['has_exif'] = False
                
                return info
                
        except Exception as e:
            current_app.logger.error(f"이미지 정보 조회 오류: {str(e)}")
            return None
