"""
이미지 생성 모듈
강화 및 사냥 결과를 PNG 이미지로 생성
"""
from typing import Optional
import importlib.util
import os
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("⚠️ Pillow가 설치되지 않았습니다. 이미지 생성 기능을 사용할 수 없습니다.")
    print("💡 설치: pip install Pillow")


def hex_to_rgb(hex_color: str) -> tuple:
    """HEX 색상을 RGB 튜플로 변환"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class ImageGenerator:
    """이미지 생성 클래스"""
    
    def __init__(self, output_dir: Optional[str] = None, icons_dir: Optional[str] = None):
        self.output_dir = output_dir or tempfile.gettempdir()
        os.makedirs(self.output_dir, exist_ok=True)
        # 아이콘 디렉토리 (기본값: 프로젝트 루트의 icons 폴더)
        self.icons_dir = icons_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons')
        os.makedirs(self.icons_dir, exist_ok=True)
    
    def _get_font(self, size: int):
        """폰트 가져오기 (한글 + 이모지 지원 폰트 사용)"""
        import platform
        import os
        
        # Windows
        if platform.system() == 'Windows':
            # Galmuri 폰트 (게임톤 폰트) 우선 시도 - 한글 지원
            galmuri_paths = [
                "C:/Windows/Fonts/Galmuri11.ttf",
                "C:/Windows/Fonts/Galmuri11-Regular.ttf",
                "C:/Windows/Fonts/Galmuri.ttf",
                "C:/Windows/Fonts/Galmuri-Regular.ttf",
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/Galmuri11.ttf"),
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/Galmuri11-Regular.ttf"),
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/Galmuri.ttf"),
                os.path.expanduser("~/Fonts/Galmuri11.ttf"),
                os.path.expanduser("~/Fonts/Galmuri.ttf"),
            ]
            for font_path in galmuri_paths:
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, size)
                    except:
                        continue
            
            # Noto Sans CJK (한글 + 이모지 지원) 시도
            noto_paths = [
                "C:/Windows/Fonts/NotoSansCJK-Regular.ttc",
                "C:/Windows/Fonts/NotoSansCJKkr-Regular.otf",
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/NotoSansCJK-Regular.ttc"),
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/NotoSansCJKkr-Regular.otf"),
            ]
            for font_path in noto_paths:
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, size)
                    except:
                        continue
            
            # 한글 지원 폰트 (이모지는 별도 처리)
            try:
                # 맑은 고딕
                return ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", size)
            except:
                try:
                    # 굴림
                    return ImageFont.truetype("C:/Windows/Fonts/gulim.ttc", size)
                except:
                    try:
                        # 나눔고딕
                        return ImageFont.truetype("C:/Windows/Fonts/NanumGothic.ttf", size)
                    except:
                        pass
        
        # Linux
        elif platform.system() == 'Linux':
            # Galmuri 폰트 (게임톤 폰트) 우선 시도
            galmuri_paths = [
                "/usr/share/fonts/truetype/custom/Galmuri11.ttf",  # Docker 컨테이너 경로 (최우선)
                "/usr/share/fonts/truetype/galmuri/Galmuri11.ttf",
                "/usr/share/fonts/truetype/galmuri/Galmuri11-Regular.ttf",
                "/usr/share/fonts/truetype/Galmuri11.ttf",
                "/usr/share/fonts/truetype/Galmuri.ttf",
                "/usr/local/share/fonts/Galmuri11.ttf",
                "/usr/local/share/fonts/Galmuri.ttf",
                os.path.expanduser("~/fonts/Galmuri11.ttf"),
                os.path.expanduser("~/.fonts/Galmuri11.ttf"),
            ]
            for font_path in galmuri_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, size)
                        # 폰트 로드 성공
                        return font
                    except Exception as e:
                        # 폰트 로드 실패 시 다음 경로 시도
                        continue
            
            # Noto Sans CJK (한글 + 이모지 지원) 시도
            noto_paths = [
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            ]
            for font_path in noto_paths:
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, size)
                    except:
                        continue
            
            # 한글 지원 폰트
            try:
                # 나눔고딕
                return ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", size)
            except:
                try:
                    # 나눔고딕 (다른 경로)
                    return ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic-Regular.ttf", size)
                except:
                    try:
                        # DejaVu Sans
                        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
                    except:
                        pass
        
        # macOS
        elif platform.system() == 'Darwin':
            # Galmuri 폰트 (게임톤 폰트) 우선 시도
            galmuri_paths = [
                "/Library/Fonts/Galmuri11.ttf",
                "/Library/Fonts/Galmuri11-Regular.ttf",
                "/Library/Fonts/Galmuri.ttf",
                "/System/Library/Fonts/Galmuri11.ttf",
                os.path.expanduser("~/Library/Fonts/Galmuri11.ttf"),
                os.path.expanduser("~/Library/Fonts/Galmuri.ttf"),
            ]
            for font_path in galmuri_paths:
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, size)
                    except:
                        continue
            
            # AppleGothic (한글 + 이모지 지원)
            try:
                return ImageFont.truetype("/System/Library/Fonts/AppleGothic.ttf", size)
            except:
                try:
                    # NanumGothic
                    return ImageFont.truetype("/Library/Fonts/NanumGothic.ttf", size)
                except:
                    pass
        
        # 기본 폰트 (한글/이모지 미지원)
        return ImageFont.load_default()
    
    def _get_emoji_font(self, size: int):
        """이모지 전용 폰트 가져오기"""
        import platform
        
        if platform.system() == 'Windows':
            try:
                return ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", size)
            except:
                pass
        elif platform.system() == 'Linux':
            try:
                return ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", size)
            except:
                pass
        elif platform.system() == 'Darwin':
            try:
                return ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", size)
            except:
                pass
        return None

    def generate_svg_image(self, svg_code: str, filename_prefix: str = "badge") -> str:
        """SVG 코드를 이미지 파일로 저장 (PNG 우선, 미지원 시 PNG 플레이스홀더)"""
        if not svg_code:
            raise ValueError("SVG 코드가 필요합니다.")

        if self._has_cairosvg():
            return self._write_svg_as_png(svg_code, filename_prefix)

        if HAS_PIL:
            return self._write_placeholder_png(filename_prefix)

        return self._write_svg(svg_code, filename_prefix)

    def _has_cairosvg(self) -> bool:
        return importlib.util.find_spec("cairosvg") is not None

    def _write_svg_as_png(self, svg_code: str, filename_prefix: str) -> str:
        import cairosvg

        with tempfile.NamedTemporaryFile(
            suffix=".png", prefix=f"{filename_prefix}_", dir=self.output_dir, delete=False
        ) as temp_file:
            cairosvg.svg2png(bytestring=svg_code.encode("utf-8"), write_to=temp_file.name)
            return temp_file.name

    def _write_svg(self, svg_code: str, filename_prefix: str) -> str:
        with tempfile.NamedTemporaryFile(
            suffix=".svg", prefix=f"{filename_prefix}_", dir=self.output_dir, delete=False
        ) as temp_file:
            temp_file.write(svg_code.encode("utf-8"))
            return temp_file.name

    def _write_placeholder_png(self, filename_prefix: str) -> str:
        image = Image.new("RGBA", (512, 512), (5, 5, 16, 255))
        draw = ImageDraw.Draw(image)
        font = self._get_font(20)
        text = "SVG 미리보기는\nCairoSVG 필요"
        text_width, text_height = self._get_text_size(draw, text, font)
        x = (512 - text_width) / 2
        y = (512 - text_height) / 2
        draw.multiline_text((x, y), text, font=font, fill=(255, 215, 0, 255), align="center")

        with tempfile.NamedTemporaryFile(
            suffix=".png", prefix=f"{filename_prefix}_", dir=self.output_dir, delete=False
        ) as temp_file:
            image.save(temp_file.name, format="PNG")
            return temp_file.name
    
    def _get_text_size(self, draw, text: str, font) -> tuple:
        """텍스트 크기 가져오기 (호환성 처리)"""
        try:
            # Pillow 9.0.0+
            bbox = draw.textbbox((0, 0), text, font=font)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except AttributeError:
            # 구버전 Pillow
            return draw.textsize(text, font=font)
    
    def _get_fontawesome_font(self, size: int):
        """Font Awesome 폰트 가져오기"""
        import platform
        
        # Font Awesome Free 폰트 경로
        fontawesome_paths = []
        
        if platform.system() == 'Windows':
            fontawesome_paths = [
                # Font Awesome 7
                "C:/Windows/Fonts/Font Awesome 7 Free-Solid-900.otf",
                "C:/Windows/Fonts/FontAwesome7Free-Solid-900.otf",
                "C:/Windows/Fonts/fa-solid-900.ttf",  # 버전 7도 동일한 파일명 사용 가능
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/Font Awesome 7 Free-Solid-900.otf"),
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/fa-solid-900.ttf"),
                os.path.join(self.icons_dir, "fonts", "fa-solid-900.ttf"),
                os.path.join(self.icons_dir, "fonts", "Font Awesome 7 Free-Solid-900.otf"),
                # Font Awesome 6 (하위 호환)
                "C:/Windows/Fonts/Font Awesome 6 Free-Solid-900.otf",
                "C:/Windows/Fonts/FontAwesome6Free-Solid-900.otf",
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/Font Awesome 6 Free-Solid-900.otf"),
                os.path.join(self.icons_dir, "fonts", "Font Awesome 6 Free-Solid-900.otf"),
            ]
        elif platform.system() == 'Linux':
            fontawesome_paths = [
                # Font Awesome 7 (Docker 컨테이너 경로)
                "/usr/share/fonts/truetype/custom/Font Awesome 7 Free-Solid-900.otf",
                "/usr/share/fonts/truetype/fontawesome/fa-solid-900.ttf",
                "/usr/share/fonts/opentype/fontawesome/Font Awesome 7 Free-Solid-900.otf",
                "/usr/local/share/fonts/fa-solid-900.ttf",
                os.path.expanduser("~/fonts/fa-solid-900.ttf"),
                os.path.expanduser("~/.fonts/fa-solid-900.ttf"),
                os.path.join(self.icons_dir, "fonts", "fa-solid-900.ttf"),
                os.path.join(self.icons_dir, "fonts", "Font Awesome 7 Free-Solid-900.otf"),
                # Font Awesome 6 (하위 호환)
                "/usr/share/fonts/opentype/fontawesome/Font Awesome 6 Free-Solid-900.otf",
            ]
        elif platform.system() == 'Darwin':
            fontawesome_paths = [
                # Font Awesome 7
                "/Library/Fonts/Font Awesome 7 Free-Solid-900.otf",
                "/Library/Fonts/fa-solid-900.ttf",
                os.path.expanduser("~/Library/Fonts/fa-solid-900.ttf"),
                os.path.join(self.icons_dir, "fonts", "fa-solid-900.ttf"),
                os.path.join(self.icons_dir, "fonts", "Font Awesome 7 Free-Solid-900.otf"),
                # Font Awesome 6 (하위 호환)
                "/Library/Fonts/Font Awesome 6 Free-Solid-900.otf",
            ]
        
        for font_path in fontawesome_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        
        return None
    
    def _get_fontawesome_icon_char(self, icon_name: str) -> Optional[str]:
        """Font Awesome 아이콘 이름을 유니코드 문자로 변환"""
        # Font Awesome 7 Free Solid 아이콘 유니코드 매핑
        # 참고: https://fontawesome.com/search?ic=free-collection
        icon_map = {
            # 골드/돈 관련
            'coin': '\uf51e',      # fa-coins (동전 여러 개)
            'coins': '\uf51e',      # fa-coins
            'money': '\uf0d6',     # fa-money-bill
            'dollar': '\uf155',     # fa-dollar-sign
            'gold': '\uf51e',      # fa-coins
            'treasure': '\uf531',   # fa-treasure-chest
            'gem': '\uf3a5',       # fa-gem (보석)
            # 성공/실패 관련
            'star': '\uf005',      # fa-star (성공, 별)
            'check': '\uf00c',     # fa-check (체크)
            'check-circle': '\uf058',  # fa-circle-check (체크 원)
            'heart-crack': '\uf7a9', # fa-heart-crack (실패, 깨진 하트)
            'xmark': '\uf00d',     # fa-xmark (X 표시)
            'times': '\uf00d',     # fa-times
            # 몬스터 타입 관련
            'circle-check': '\uf058',  # fa-circle-check (일반몹 - 초록 체크)
            'shield': '\uf3ed',    # fa-shield (방패 - 일반몹)
            'shield-halved': '\uf3ed',  # fa-shield-halved (반 방패)
            'circle-exclamation': '\uf06a',  # fa-circle-exclamation (특수몹 - 노란 경고)
            'gem': '\uf3a5',       # fa-gem (특수몹 - 보석)
            'fire': '\uf06d',      # fa-fire (불 - 특수몹 대체)
            'circle-xmark': '\uf057',  # fa-circle-xmark (보스몹 - 빨간 X)
            'crown': '\uf521',     # fa-crown (보스몹 대체 - 왕관)
            'skull': '\uf54c',     # fa-skull (보스몹 대체 - 해골)
            'dragon': '\uf6d5',     # fa-dragon (보스몹 대체 - 용)
            # 무기/전투 관련
            'sword': '\uf71d',     # fa-sword (검)
            'axe': '\uf6b2',       # fa-axe (도끼)
            'bow-arrow': '\uf6b9',  # fa-bow-arrow (활)
            'crosshairs': '\uf05b',  # fa-crosshairs (조준선)
            # 강화/장비 관련
            'hammer': '\uf6e3',    # fa-hammer (망치)
            'wrench': '\uf0ad',    # fa-wrench (렌치)
            'screwdriver': '\uf54a',  # fa-screwdriver (드라이버)
            'gear': '\uf013',      # fa-gear (기어)
            # 기타
            'user': '\uf007',      # fa-user (사용자)
            'chart-line': '\uf201',  # fa-chart-line (차트)
            'hand-holding-dollar': '\uf4c0',  # fa-hand-holding-dollar (손에 돈)
        }
        return icon_map.get(icon_name.lower())
    
    def _load_icon(self, icon_name: str, size: int = 24, color: Optional[tuple] = None) -> Optional[Image.Image]:
        """아이콘 이미지 로드 (이미지 파일 또는 Font Awesome)
        
        Args:
            icon_name: 아이콘 이름
            size: 아이콘 크기
            color: 아이콘 색상 (R, G, B) 또는 (R, G, B, A), None이면 흰색
        """
        if not HAS_PIL:
            return None
        
        # 색상 기본값 설정
        if color is None:
            icon_color = (255, 255, 255, 255)
        elif len(color) == 3:
            icon_color = color + (255,)  # RGB -> RGBA
        else:
            icon_color = color
        
        # 먼저 이미지 파일 시도
        extensions = ['.png', '.jpg', '.jpeg']
        for ext in extensions:
            icon_path = os.path.join(self.icons_dir, f"{icon_name}{ext}")
            if os.path.exists(icon_path):
                try:
                    icon = Image.open(icon_path)
                    if icon.mode != 'RGBA':
                        icon = icon.convert('RGBA')
                    # 색상 조정 (이미지 파일의 경우)
                    if color is not None:
                        # 이미지의 알파 채널은 유지하고 RGB만 변경
                        icon_array = icon.split()
                        if len(icon_array) == 4:  # RGBA
                            colored_icon = Image.new('RGBA', icon.size)
                            for i in range(icon.width):
                                for j in range(icon.height):
                                    r, g, b, a = icon.getpixel((i, j))
                                    if a > 0:  # 투명하지 않은 픽셀만
                                        # 색상 혼합
                                        new_r = int(r * icon_color[0] / 255)
                                        new_g = int(g * icon_color[1] / 255)
                                        new_b = int(b * icon_color[2] / 255)
                                        colored_icon.putpixel((i, j), (new_r, new_g, new_b, a))
                            icon = colored_icon
                    icon = icon.resize((size, size), Image.Resampling.LANCZOS)
                    return icon
                except Exception as e:
                    print(f"⚠️ 아이콘 로드 실패: {icon_path} - {e}")
                    continue
        
        # Font Awesome 폰트 사용
        fa_font = self._get_fontawesome_font(size)
        if fa_font:
            icon_char = self._get_fontawesome_icon_char(icon_name)
            if icon_char:
                # Font Awesome 아이콘을 이미지로 렌더링
                icon_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                icon_draw = ImageDraw.Draw(icon_img)
                # 아이콘을 중앙에 그리기
                try:
                    bbox = icon_draw.textbbox((0, 0), icon_char, font=fa_font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (size - text_width) // 2
                    y = (size - text_height) // 2
                    # 지정된 색상 사용
                    icon_draw.text((x, y), icon_char, fill=icon_color, font=fa_font)
                    return icon_img
                except:
                    pass
        
        return None
    
    def _get_text_with_icon_width(self, draw, text: str, font, icon_name: str, icon_size: int) -> int:
        """아이콘과 텍스트의 전체 너비 계산 (렌더링 없이)"""
        # 아이콘 존재 여부 확인
        icon_exists = False
        
        # Font Awesome 폰트로 아이콘 확인
        fa_font = self._get_fontawesome_font(icon_size)
        if fa_font and self._get_fontawesome_icon_char(icon_name):
            icon_exists = True
        else:
            # 이미지 파일 확인
            extensions = ['.png', '.jpg', '.jpeg']
            for ext in extensions:
                icon_path = os.path.join(self.icons_dir, f"{icon_name}{ext}")
                if os.path.exists(icon_path):
                    icon_exists = True
                    break
        
        # 텍스트 너비 계산
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
        except:
            try:
                text_width, _ = font.getsize(text)
            except:
                text_width = len(text) * 10
        
        total_width = (icon_size + 5 if icon_exists else 0) + text_width
        return total_width
    
    def _draw_text_with_icon(self, draw, img, position: tuple, text: str, font, icon_name: str, icon_size: int, fill):
        """아이콘과 텍스트를 함께 렌더링
        
        Args:
            fill: 텍스트 색상 (R, G, B) 또는 (R, G, B, A), 아이콘 색상도 이와 동일하게 적용
        """
        x, y = position
        
        # 아이콘 색상을 텍스트 색상과 맞춤
        icon_color = fill if isinstance(fill, tuple) and len(fill) >= 3 else (255, 255, 255)
        
        # 아이콘 로드 (색상 적용)
        icon = self._load_icon(icon_name, icon_size, color=icon_color)
        
        if icon:
            # 아이콘 그리기 (y 위치는 텍스트 중앙에 맞춤)
            icon_y = y - icon_size // 2
            img.paste(icon, (x, icon_y), icon)
            # 텍스트는 아이콘 옆에 배치
            text_x = x + icon_size + 5
        else:
            # 아이콘이 없으면 텍스트만
            text_x = x
        
        # 텍스트 렌더링
        draw.text((text_x, y), text, fill=fill, font=font)
    
    def _draw_text_with_emoji(self, draw, position: tuple, text: str, font, emoji_font, fill):
        """이모지와 일반 텍스트를 함께 렌더링"""
        import re
        
        x, y = position
        # 이모지 유니코드 범위
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        
        if not emoji_font:
            # 이모지 폰트가 없으면 일반 폰트로 렌더링
            draw.text((x, y), text, fill=fill, font=font)
            return
        
        # 텍스트를 이모지와 일반 텍스트로 분리
        parts = emoji_pattern.split(text)
        emojis = emoji_pattern.findall(text)
        
        current_x = x
        for i, part in enumerate(parts):
            if part:
                # 일반 텍스트 렌더링
                draw.text((current_x, y), part, fill=fill, font=font)
                try:
                    bbox = draw.textbbox((0, 0), part, font=font)
                    w = bbox[2] - bbox[0]
                except:
                    try:
                        w, _ = font.getsize(part)
                    except:
                        w = len(part) * 10
                current_x += w
            
            # 이모지 렌더링
            if i < len(emojis):
                emoji = emojis[i]
                draw.text((current_x, y), emoji, fill=fill, font=emoji_font)
                try:
                    bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
                    w = bbox[2] - bbox[0]
                except:
                    try:
                        w, _ = emoji_font.getsize(emoji)
                    except:
                        w = 20
                current_x += w
    
    def generate_enhancement_image(
        self,
        level: int,
        max_level: Optional[int] = None,
        is_success: bool = True,
        previous_level: Optional[int] = None,
        gold: int = 0,
        next_cost: int = 0,
        next_success_rate: float = 0,
        attempts: int = 0,
        successes: int = 0,
        failures: int = 0
    ) -> Optional[str]:
        """강화 결과 PNG 이미지 생성
        
        Args:
            level: 현재 강화 레벨
            max_level: 최대 강화 레벨 (사용 안 함, 호환성 유지)
            is_success: 성공 여부
            previous_level: 이전 레벨 (실패 시)
            gold: 현재 골드
            
        Returns:
            생성된 PNG 파일 경로 (Pillow 없으면 None)
        """
        if not HAS_PIL:
            return None
        
        filename = f"enhancement_{level}_{is_success}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        # 이미지 생성 (더 넓은 여백)
        width, height = 500, 380
        # 세련된 그라데이션 배경 (어두운 보라-파랑 톤)
        bg_color = hex_to_rgb('#0f172a')  # 슬레이트 900
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # 상단 그라데이션 효과 (선택적)
        overlay = Image.new('RGBA', (width, 100), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for i in range(100):
            alpha = int(30 * (1 - i / 100))
            overlay_draw.rectangle([(0, i), (width, i + 1)], fill=(59, 130, 246, alpha))  # 파랑 그라데이션
        img.paste(overlay, (0, 0), overlay)
        
        # 폰트 (크기 조정)
        title_font = self._get_font(28)
        level_font = self._get_font(56)
        gold_font = self._get_font(22)
        small_font = self._get_font(16)
        
        # 여백 설정
        padding_top = 30
        padding_bottom = 30
        padding_sides = 40
        
        # 제목
        title_text = "강화 결과" if is_success else "강화 실패"
        # 더 부드러운 색상
        title_color = hex_to_rgb('#34d399') if is_success else hex_to_rgb('#f87171')  # 에메랄드 400, 빨강 500
        
        # 텍스트 중앙 정렬
        text_width, text_height = self._get_text_size(draw, title_text, title_font)
        draw.text(((width - text_width) // 2, padding_top), title_text, fill=title_color, font=title_font)
        
        # 레벨 표시 (여백 조정)
        level_y = padding_top + text_height + 25
        if is_success:
            level_text = f"+{level}"
            # 더 부드러운 파랑
            level_color = hex_to_rgb('#60a5fa')  # 스카이 400
            text_width, _ = self._get_text_size(draw, level_text, level_font)
            draw.text(((width - text_width) // 2, level_y), level_text, fill=level_color, font=level_font)
        else:
            if previous_level is not None and previous_level > 0:
                level_text = f"+{previous_level} → +{level}"
            else:
                level_text = f"+{level} (변화 없음)"
            level_color = hex_to_rgb('#f87171')  # 빨강 500
            level_font_small = self._get_font(42)
            text_width, _ = self._get_text_size(draw, level_text, level_font_small)
            draw.text(((width - text_width) // 2, level_y), level_text, fill=level_color, font=level_font_small)
        
        # 골드 표시 (여백 조정)
        gold_y = level_y + 80
        if gold > 0:
            gold_text = f"{gold:,}G"
            # 아이콘과 텍스트의 전체 너비 계산
            total_width = self._get_text_with_icon_width(draw, gold_text, gold_font, "coin", 28)
            x_pos = (width - total_width) // 2
            # 더 부드러운 골드 색상
            gold_color = hex_to_rgb('#fbbf24')  # 앰버 400
            # 아이콘과 텍스트 렌더링
            self._draw_text_with_icon(draw, img, (x_pos, gold_y), gold_text, gold_font, "coin", 28, gold_color)
        
        # 재밌는 정보 추가 (골드와 아이콘 사이)
        info_y = gold_y + 60
        info_font = self._get_font(14)
        tip_font = self._get_font(13)
        
        # 다음 강화 정보
        if next_cost > 0:
            next_info = f"다음 강화: {next_cost:,}G"
            text_width, _ = self._get_text_size(draw, next_info, info_font)
            draw.text(((width - text_width) // 2, info_y), next_info, fill=hex_to_rgb('#94a3b8'), font=info_font)
            info_y += 22
        
        # 성공 확률 정보
        if next_success_rate > 0:
            success_info = f"성공 확률: {next_success_rate:.1f}%"
            text_width, _ = self._get_text_size(draw, success_info, info_font)
            draw.text(((width - text_width) // 2, info_y), success_info, fill=hex_to_rgb('#94a3b8'), font=info_font)
            info_y += 22
        
        # 강화 통계 (재밌게)
        if attempts > 0:
            success_rate = (successes / attempts * 100) if attempts > 0 else 0
            stats_text = f"통계: {successes}승 {failures}패 ({success_rate:.1f}%)"
            text_width, _ = self._get_text_size(draw, stats_text, info_font)
            draw.text(((width - text_width) // 2, info_y), stats_text, fill=hex_to_rgb('#94a3b8'), font=info_font)
            info_y += 22
        
        # 재밌는 팁 메시지
        tips = self._get_enhancement_tip(level, is_success, successes, failures)
        if tips:
            tip_y = info_y + 5
            for tip in tips:
                text_width, tip_height = self._get_text_size(draw, tip, tip_font)
                draw.text(((width - text_width) // 2, tip_y), tip, fill=hex_to_rgb('#64748b'), font=tip_font)
                tip_y += tip_height + 3
        
        # Font Awesome 아이콘 표시 (성공/실패) - 하단 여백, 색상 적용
        icon_name = "star" if is_success else "heart-crack"
        icon_size = 48
        # 성공: 에메랄드, 실패: 빨강
        icon_color = hex_to_rgb('#34d399') if is_success else hex_to_rgb('#f87171')
        icon = self._load_icon(icon_name, icon_size, color=icon_color)
        if icon:
            icon_x = (width - icon_size) // 2
            icon_y = height - padding_bottom - icon_size
            img.paste(icon, (icon_x, icon_y), icon)
        
        # GIF 애니메이션 생성
        gif_filepath = filepath.replace('.png', '.gif')
        frames = self._create_enhancement_frames(img, is_success, level, previous_level, gold, next_cost, next_success_rate, attempts, successes, failures, width, height)
        if frames:
            frames[0].save(
                gif_filepath,
                save_all=True,
                append_images=frames[1:],
                duration=100,  # 각 프레임 100ms
                loop=0,  # 무한 반복
                optimize=False
            )
            return gif_filepath
        else:
            # GIF 생성 실패 시 PNG 저장
            img.save(filepath, 'PNG')
            return filepath
    
    def generate_hunt_image(
        self,
        monster_name: str,
        monster_type: str,
        reward: int,
        is_success: bool,
        level: int = 0,
        gold: int = 0
    ) -> Optional[str]:
        """사냥 결과 PNG 이미지 생성
        
        Args:
            monster_name: 몬스터 이름
            monster_type: 몬스터 타입 (일반몹, 특수몹, 보스몹)
            reward: 획득 골드
            is_success: 성공 여부
            level: 강화 레벨
            gold: 현재 골드
            
        Returns:
            생성된 PNG 파일 경로 (Pillow 없으면 None)
        """
        if not HAS_PIL:
            return None
        
        filename = f"hunt_{monster_type}_{is_success}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        # 이미지 생성 (더 넓은 여백)
        width, height = 500, 420
        # 세련된 그라데이션 배경
        bg_color = hex_to_rgb('#0f172a')  # 슬레이트 900
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # 상단 그라데이션 효과
        overlay = Image.new('RGBA', (width, 120), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for i in range(120):
            alpha = int(40 * (1 - i / 120))
            overlay_draw.rectangle([(0, i), (width, i + 1)], fill=(59, 130, 246, alpha))  # 파랑 그라데이션
        img.paste(overlay, (0, 0), overlay)
        
        # 폰트 (크기 조정)
        title_font = self._get_font(28)
        name_font = self._get_font(38)
        type_font = self._get_font(20)
        reward_font = self._get_font(32)
        info_font = self._get_font(18)
        gold_font = self._get_font(20)
        
        # 여백 설정
        padding_top = 35
        padding_bottom = 35
        padding_sides = 40
        
        # 몬스터 타입별 색상 (더 부드러운 색상)
        type_colors = {
            '일반몹': hex_to_rgb('#34d399'),  # 에메랄드 400
            '특수몹': hex_to_rgb('#fbbf24'),  # 앰버 400
            '보스몹': hex_to_rgb('#f87171')   # 빨강 500
        }
        type_color = type_colors.get(monster_type, hex_to_rgb('#60a5fa'))
        
        # 제목
        title_text = "사냥 성공!" if is_success else "사냥 실패..."
        title_color = type_color if is_success else hex_to_rgb('#f87171')
        
        text_width, text_height = self._get_text_size(draw, title_text, title_font)
        draw.text(((width - text_width) // 2, padding_top), title_text, fill=title_color, font=title_font)
        
        # 몬스터 이름 (타입별 색상 적용)
        name_y = padding_top + text_height + 30
        text_width, name_text_height = self._get_text_size(draw, monster_name, name_font)
        # 몬스터 이름도 타입별 색상 사용 (약간 밝게)
        name_color = type_color if is_success else (255, 255, 255)
        draw.text(((width - text_width) // 2, name_y), monster_name, fill=name_color, font=name_font)
        
        # 몬스터 타입 (여백 조정)
        type_y = name_y + name_text_height + 15
        type_text = f"[{monster_type}]"
        text_width, _ = self._get_text_size(draw, type_text, type_font)
        draw.text(((width - text_width) // 2, type_y), type_text, fill=type_color, font=type_font)
        
        if is_success:
            # 획득 골드 (여백 조정)
            reward_y = type_y + 50
            reward_text = f"+{reward:,}G 획득!"
            # 아이콘과 텍스트의 전체 너비 계산
            total_width = self._get_text_with_icon_width(draw, reward_text, reward_font, "coin", 32)
            x_pos = (width - total_width) // 2
            # 아이콘과 텍스트 렌더링
            self._draw_text_with_icon(draw, img, (x_pos, reward_y), reward_text, reward_font, "coin", 32, hex_to_rgb('#fbbf24'))
            
            # 강화 레벨 정보 (여백 조정)
            if level > 0:
                level_y = reward_y + 50
                level_text = f"강화 레벨: +{level}"
                text_width, _ = self._get_text_size(draw, level_text, info_font)
                draw.text(((width - text_width) // 2, level_y), level_text, fill=hex_to_rgb('#60a5fa'), font=info_font)
        else:
            # 실패 메시지 (여백 조정)
            fail_y = type_y + 50
            fail_text = "몬스터가 도망갔습니다..."
            text_width, _ = self._get_text_size(draw, fail_text, info_font)
            draw.text(((width - text_width) // 2, fail_y), fail_text, fill=hex_to_rgb('#f87171'), font=info_font)
        
        # 현재 골드 (여백 조정)
        if gold > 0:
            gold_y = height - padding_bottom - 80
            gold_text = f"현재 골드: {gold:,}G"
            text_width, _ = self._get_text_size(draw, gold_text, gold_font)
            draw.text(((width - text_width) // 2, gold_y), gold_text, fill=hex_to_rgb('#fbbf24'), font=gold_font)
        
        # 몬스터 타입별 Font Awesome 아이콘 (하단 여백)
        # Font Awesome Free Collection에서 선택한 아이콘들
        icon_map = {
            '일반몹': 'shield',           # fa-shield (방패 - 일반몹)
            '특수몹': 'gem',             # fa-gem (보석 - 특수몹)
            '보스몹': 'crown'            # fa-crown (왕관 - 보스몹)
        }
        icon_name = icon_map.get(monster_type, 'sword')
        icon_size = 56
        # 아이콘 색상을 타입별 색상으로 설정
        icon_color = type_color if is_success else hex_to_rgb('#9ca3af')  # 실패 시 회색
        icon = self._load_icon(icon_name, icon_size, color=icon_color)
        if icon:
            icon_x = (width - icon_size) // 2
            icon_y = height - padding_bottom - icon_size
            img.paste(icon, (icon_x, icon_y), icon)
        
        # GIF 애니메이션 생성
        gif_filepath = filepath.replace('.png', '.gif')
        frames = self._create_hunt_frames(img, is_success, monster_type, monster_name, reward, level, gold, width, height)
        if frames:
            frames[0].save(
                gif_filepath,
                save_all=True,
                append_images=frames[1:],
                duration=100,  # 각 프레임 100ms
                loop=0,  # 무한 반복
                optimize=False
            )
            return gif_filepath
        else:
            # GIF 생성 실패 시 PNG 저장
            img.save(filepath, 'PNG')
            return filepath
    
    def _create_enhancement_frames(
        self,
        base_img: Image.Image,
        is_success: bool,
        level: int,
        previous_level: Optional[int],
        gold: int,
        next_cost: int,
        next_success_rate: float,
        attempts: int,
        successes: int,
        failures: int,
        width: int,
        height: int
    ) -> list:
        """강화 이미지 애니메이션 프레임 생성 (강화에 맞는 효과)"""
        frames = []
        padding_top = 30
        padding_bottom = 30
        
        if is_success:
            # 성공 애니메이션: 번개 효과 + 레벨 카운트업 + 빛나는 효과
            # 1. 페이드 인 (3프레임)
            for i in range(3):
                alpha = int(255 * (i + 1) / 3)
                frame = base_img.copy()
                if alpha < 255:
                    frame = frame.convert('RGBA')
                    alpha_channel = Image.new('L', frame.size, alpha)
                    frame.putalpha(alpha_channel)
                    frame = frame.convert('RGB')
                frames.append(frame)
            
            # 2. 번개 효과 (3프레임) - 강화의 순간
            for flash in range(3):
                frame = self._redraw_enhancement_frame(
                    width, height, is_success, level, previous_level, gold, next_cost, next_success_rate, attempts, successes, failures, flash_alpha=150 - (flash * 50)
                )
                frames.append(frame)
            
            # 3. 레벨 카운트업 (이전 레벨에서 현재 레벨로)
            if previous_level is not None and previous_level < level:
                for current_level in range(previous_level + 1, level + 1):
                    frame = self._redraw_enhancement_frame(
                        width, height, is_success, current_level, previous_level, gold, next_cost, next_success_rate, attempts, successes, failures, scale=1.1
                    )
                    frames.append(frame)
            
            # 4. 빛나는 효과 (3프레임) - 성공 축하
            for glow in [0.8, 1.0, 0.8]:
                frame = self._redraw_enhancement_frame(
                    width, height, is_success, level, previous_level, gold, next_cost, next_success_rate, attempts, successes, failures, glow_alpha=int(100 * glow)
                )
                frames.append(frame)
            
            # 5. 최종 프레임 (3프레임) - 안정화
            for _ in range(3):
                frames.append(base_img.copy())
        else:
            # 실패 애니메이션: 흔들림 효과 + 레벨 하락
            # 1. 페이드 인
            for i in range(3):
                alpha = int(255 * (i + 1) / 3)
                frame = base_img.copy()
                if alpha < 255:
                    frame = frame.convert('RGBA')
                    alpha_channel = Image.new('L', frame.size, alpha)
                    frame.putalpha(alpha_channel)
                    frame = frame.convert('RGB')
                frames.append(frame)
            
            # 2. 흔들림 효과 (3프레임) - 실패의 충격
            for shake in [-3, 3, -2, 2, 0]:
                frame = base_img.copy()
                if shake != 0:
                    # 약간의 흔들림 효과
                    frame = frame.transform(
                        (width, height),
                        Image.AFFINE,
                        (1, 0, shake, 0, 1, 0)
                    )
                frames.append(frame)
            
            # 3. 최종 프레임
            for _ in range(2):
                frames.append(base_img.copy())
        
        return frames if len(frames) > 1 else []
    
    def _redraw_enhancement_frame(
        self,
        width: int,
        height: int,
        is_success: bool,
        level: int,
        previous_level: Optional[int],
        gold: int,
        next_cost: int,
        next_success_rate: float,
        attempts: int,
        successes: int,
        failures: int,
        flash_alpha: int = 0,
        glow_alpha: int = 0,
        scale: float = 1.0
    ) -> Image.Image:
        """강화 프레임 다시 그리기 (잘림 방지)"""
        bg_color = hex_to_rgb('#0f172a')
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # 상단 그라데이션
        overlay = Image.new('RGBA', (width, 100), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for i in range(100):
            alpha = int(30 * (1 - i / 100))
            overlay_draw.rectangle([(0, i), (width, i + 1)], fill=(59, 130, 246, alpha))
        img.paste(overlay, (0, 0), overlay)
        
        # 번개 효과 (flash_alpha가 있을 때)
        if flash_alpha > 0:
            flash_overlay = Image.new('RGBA', (width, height), (255, 255, 255, flash_alpha))
            img.paste(flash_overlay, (0, 0), flash_overlay)
        
        # 빛나는 효과 (glow_alpha가 있을 때)
        if glow_alpha > 0:
            glow_color = hex_to_rgb('#34d399') if is_success else hex_to_rgb('#f87171')
            glow_overlay = Image.new('RGBA', (width, height), (*glow_color, glow_alpha))
            img.paste(glow_overlay, (0, 0), glow_overlay)
        
        # 폰트
        title_font = self._get_font(28)
        level_font = self._get_font(int(56 * scale))
        gold_font = self._get_font(22)
        info_font = self._get_font(14)
        tip_font = self._get_font(13)
        
        padding_top = 30
        padding_bottom = 30
        
        # 제목
        title_text = "강화 결과" if is_success else "강화 실패"
        title_color = hex_to_rgb('#34d399') if is_success else hex_to_rgb('#f87171')
        text_width, text_height = self._get_text_size(draw, title_text, title_font)
        draw.text(((width - text_width) // 2, padding_top), title_text, fill=title_color, font=title_font)
        
        # 레벨 표시
        level_y = padding_top + text_height + 25
        if is_success:
            level_text = f"+{level}"
            level_color = hex_to_rgb('#60a5fa')
        else:
            if previous_level is not None and previous_level > 0:
                level_text = f"+{previous_level} → +{level}"
            else:
                level_text = f"+{level} (변화 없음)"
            level_color = hex_to_rgb('#f87171')
            level_font = self._get_font(int(42 * scale))
        
        text_width, _ = self._get_text_size(draw, level_text, level_font)
        draw.text(((width - text_width) // 2, level_y), level_text, fill=level_color, font=level_font)
        
        # 골드 표시
        gold_y = level_y + 80
        if gold > 0:
            gold_text = f"{gold:,}G"
            total_width = self._get_text_with_icon_width(draw, gold_text, gold_font, "coin", 28)
            x_pos = (width - total_width) // 2
            gold_color = hex_to_rgb('#fbbf24')
            self._draw_text_with_icon(draw, img, (x_pos, gold_y), gold_text, gold_font, "coin", 28, gold_color)
        
        # 재밌는 정보 추가
        info_y = gold_y + 60
        info_font = self._get_font(14)
        tip_font = self._get_font(13)
        
        if next_cost > 0:
            next_info = f"다음 강화: {next_cost:,}G"
            text_width, _ = self._get_text_size(draw, next_info, info_font)
            draw.text(((width - text_width) // 2, info_y), next_info, fill=hex_to_rgb('#94a3b8'), font=info_font)
            info_y += 22
        
        if next_success_rate > 0:
            success_info = f"성공 확률: {next_success_rate:.1f}%"
            text_width, _ = self._get_text_size(draw, success_info, info_font)
            draw.text(((width - text_width) // 2, info_y), success_info, fill=hex_to_rgb('#94a3b8'), font=info_font)
            info_y += 22
        
        if attempts > 0:
            success_rate = (successes / attempts * 100) if attempts > 0 else 0
            stats_text = f"통계: {successes}승 {failures}패 ({success_rate:.1f}%)"
            text_width, _ = self._get_text_size(draw, stats_text, info_font)
            draw.text(((width - text_width) // 2, info_y), stats_text, fill=hex_to_rgb('#94a3b8'), font=info_font)
            info_y += 22
        
        tips = self._get_enhancement_tip(level, is_success, successes, failures)
        if tips:
            tip_y = info_y + 5
            for tip in tips:
                text_width, tip_height = self._get_text_size(draw, tip, tip_font)
                draw.text(((width - text_width) // 2, tip_y), tip, fill=hex_to_rgb('#64748b'), font=tip_font)
                tip_y += tip_height + 3
        
        # 아이콘
        icon_name = "star" if is_success else "heart-crack"
        icon_size = 48
        icon_color = hex_to_rgb('#34d399') if is_success else hex_to_rgb('#f87171')
        icon = self._load_icon(icon_name, icon_size, color=icon_color)
        if icon:
            icon_x = (width - icon_size) // 2
            icon_y = height - padding_bottom - icon_size
            img.paste(icon, (icon_x, icon_y), icon)
        
        return img
    
    def _get_enhancement_tip(self, level: int, is_success: bool, successes: int, failures: int) -> list:
        """강화 팁 메시지 생성"""
        tips = []
        
        if is_success:
            if level >= 10:
                tips.append("🎉 고레벨 달성! 대단해요!")
            elif level >= 5:
                tips.append("💪 잘하고 있어요!")
            else:
                tips.append("✨ 계속 도전하세요!")
        else:
            if failures > successes:
                tips.append("💪 포기하지 마세요!")
            else:
                tips.append("🎲 운이 따를 거예요!")
        
        return tips
    
    def _create_hunt_frames(
        self,
        base_img: Image.Image,
        is_success: bool,
        monster_type: str,
        monster_name: str,
        reward: int,
        level: int,
        gold: int,
        width: int,
        height: int
    ) -> list:
        """사냥 이미지 애니메이션 프레임 생성 (몬스터 처치에 맞는 효과)"""
        frames = []
        padding_top = 35
        padding_bottom = 35
        
        if is_success:
            # 성공 애니메이션: 타격 효과 + 몬스터 처치 + 보상 등장
            # 1. 페이드 인 (3프레임)
            for i in range(3):
                alpha = int(255 * (i + 1) / 3)
                frame = base_img.copy()
                if alpha < 255:
                    frame = frame.convert('RGBA')
                    alpha_channel = Image.new('L', frame.size, alpha)
                    frame.putalpha(alpha_channel)
                    frame = frame.convert('RGB')
                frames.append(frame)
            
            # 2. 타격 효과 (X 표시, 2프레임) - 처치의 순간
            for strike in range(2):
                frame = self._redraw_hunt_frame(
                    width, height, is_success, monster_type, monster_name, reward, level, gold, strike_alpha=200 - (strike * 100)
                )
                frames.append(frame)
            
            # 3. 몬스터 이름 페이드 아웃 (3프레임) - 처치됨
            for fade in [1.0, 0.5, 0.0]:
                frame = self._redraw_hunt_frame(
                    width, height, is_success, monster_type, monster_name, reward, level, gold, name_alpha=int(255 * fade)
                )
                frames.append(frame)
            
            # 4. 보상 등장 효과 (3프레임) - 골드 획득
            for reward_scale in [0.5, 0.8, 1.0]:
                frame = self._redraw_hunt_frame(
                    width, height, is_success, monster_type, monster_name, reward, level, gold, reward_scale=reward_scale
                )
                frames.append(frame)
            
            # 5. 승리 효과 - 아이콘 펄스 (3프레임)
            for pulse in [1.0, 1.2, 1.0]:
                frame = self._redraw_hunt_frame(
                    width, height, is_success, monster_type, monster_name, reward, level, gold, icon_scale=pulse
                )
                frames.append(frame)
            
            # 6. 최종 프레임 (2프레임)
            for _ in range(2):
                frames.append(base_img.copy())
        else:
            # 실패 애니메이션: 흔들림 + 도망 효과
            # 1. 페이드 인
            for i in range(3):
                alpha = int(255 * (i + 1) / 3)
                frame = base_img.copy()
                if alpha < 255:
                    frame = frame.convert('RGBA')
                    alpha_channel = Image.new('L', frame.size, alpha)
                    frame.putalpha(alpha_channel)
                    frame = frame.convert('RGB')
                frames.append(frame)
            
            # 2. 흔들림 효과 (몬스터가 도망감)
            for shake in [-2, 2, -1, 1, 0]:
                frame = base_img.copy()
                if shake != 0:
                    frame = frame.transform(
                        (width, height),
                        Image.AFFINE,
                        (1, 0, shake, 0, 1, 0)
                    )
                frames.append(frame)
            
            # 3. 최종 프레임
            for _ in range(2):
                frames.append(base_img.copy())
        
        return frames if len(frames) > 1 else []
    
    def _redraw_hunt_frame(
        self,
        width: int,
        height: int,
        is_success: bool,
        monster_type: str,
        monster_name: str,
        reward: int,
        level: int,
        gold: int,
        strike_alpha: int = 0,
        name_alpha: int = 255,
        reward_scale: float = 1.0,
        icon_scale: float = 1.0
    ) -> Image.Image:
        """사냥 프레임 다시 그리기 (잘림 방지)"""
        # base_img에서 정보 추출을 위해 다시 그리기
        bg_color = hex_to_rgb('#0f172a')
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # 상단 그라데이션
        overlay = Image.new('RGBA', (width, 120), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for i in range(120):
            alpha = int(40 * (1 - i / 120))
            overlay_draw.rectangle([(0, i), (width, i + 1)], fill=(59, 130, 246, alpha))
        img.paste(overlay, (0, 0), overlay)
        
        # 타격 효과 (X 표시)
        if strike_alpha > 0:
            strike_overlay = Image.new('RGBA', (width, height), (255, 0, 0, strike_alpha))
            img.paste(strike_overlay, (0, 0), strike_overlay)
            # X 표시 그리기
            xmark_font = self._get_font(120)
            xmark = self._get_fontawesome_icon_char('xmark')
            if xmark and hasattr(self, '_get_fontawesome_font'):
                fa_font = self._get_fontawesome_font(120)
                if fa_font:
                    draw.text((width // 2 - 60, height // 2 - 60), xmark, fill=(255, 255, 255, strike_alpha), font=fa_font)
        
        # 폰트
        title_font = self._get_font(28)
        name_font = self._get_font(38)
        type_font = self._get_font(20)
        reward_font = self._get_font(int(32 * reward_scale))
        info_font = self._get_font(18)
        gold_font = self._get_font(20)
        
        padding_top = 35
        padding_bottom = 35
        
        # 타입별 색상
        type_colors = {
            '일반몹': hex_to_rgb('#34d399'),
            '특수몹': hex_to_rgb('#fbbf24'),
            '보스몹': hex_to_rgb('#f87171')
        }
        type_color = type_colors.get(monster_type, hex_to_rgb('#60a5fa'))
        
        # 제목
        title_text = "사냥 성공!" if is_success else "사냥 실패..."
        title_color = type_color if is_success else hex_to_rgb('#f87171')
        text_width, text_height = self._get_text_size(draw, title_text, title_font)
        draw.text(((width - text_width) // 2, padding_top), title_text, fill=title_color, font=title_font)
        
        # 몬스터 이름 (알파 적용)
        name_y = padding_top + text_height + 30
        text_width, name_text_height = self._get_text_size(draw, monster_name, name_font)
        name_color = (*type_color, name_alpha) if is_success else (255, 255, 255, name_alpha)
        if name_alpha < 255:
            name_overlay = Image.new('RGBA', (width, name_text_height + 20), (0, 0, 0, 0))
            name_draw = ImageDraw.Draw(name_overlay)
            name_draw.text(((width - text_width) // 2, 0), monster_name, fill=name_color, font=name_font)
            img.paste(name_overlay, (0, name_y), name_overlay)
        else:
            draw.text(((width - text_width) // 2, name_y), monster_name, fill=type_color if is_success else (255, 255, 255), font=name_font)
        
        # 몬스터 타입
        type_y = name_y + name_text_height + 15
        type_text = f"[{monster_type}]"
        text_width, _ = self._get_text_size(draw, type_text, type_font)
        draw.text(((width - text_width) // 2, type_y), type_text, fill=type_color, font=type_font)
        
        # 보상 (성공 시, 스케일 적용)
        if is_success:
            reward_y = type_y + 50
            reward_text = f"+{reward:,}G 획득!"
            total_width = self._get_text_with_icon_width(draw, reward_text, reward_font, "coin", int(32 * reward_scale))
            x_pos = (width - total_width) // 2
            gold_color = hex_to_rgb('#fbbf24')
            self._draw_text_with_icon(draw, img, (x_pos, reward_y), reward_text, reward_font, "coin", int(32 * reward_scale), gold_color)
            
            # 강화 레벨 정보
            if level > 0:
                level_y = reward_y + 50
                level_text = f"강화 레벨: +{level}"
                info_font = self._get_font(18)
                text_width, _ = self._get_text_size(draw, level_text, info_font)
                draw.text(((width - text_width) // 2, level_y), level_text, fill=hex_to_rgb('#60a5fa'), font=info_font)
        else:
            # 실패 메시지
            fail_y = type_y + 50
            fail_text = "몬스터가 도망갔습니다..."
            info_font = self._get_font(18)
            text_width, _ = self._get_text_size(draw, fail_text, info_font)
            draw.text(((width - text_width) // 2, fail_y), fail_text, fill=hex_to_rgb('#f87171'), font=info_font)
        
        # 현재 골드
        if gold > 0:
            gold_y = height - padding_bottom - 80
            gold_text = f"현재 골드: {gold:,}G"
            gold_font = self._get_font(20)
            text_width, _ = self._get_text_size(draw, gold_text, gold_font)
            draw.text(((width - text_width) // 2, gold_y), gold_text, fill=hex_to_rgb('#fbbf24'), font=gold_font)
        
        # 아이콘
        icon_map = {
            '일반몹': 'shield',
            '특수몹': 'gem',
            '보스몹': 'crown'
        }
        icon_name = icon_map.get(monster_type, 'sword')
        icon_size = int(56 * icon_scale)
        icon_color = type_color if is_success else hex_to_rgb('#9ca3af')
        icon = self._load_icon(icon_name, icon_size, color=icon_color)
        if icon:
            icon_x = (width - icon_size) // 2
            icon_y = height - padding_bottom - icon_size
            img.paste(icon, (icon_x, icon_y), icon)
        
        return img
