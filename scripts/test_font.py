#!/usr/bin/env python3
"""
폰트 테스트 스크립트
"""
from image_generator import ImageGenerator
from PIL import Image, ImageDraw
import os

def test_fonts():
    """폰트 테스트"""
    gen = ImageGenerator()
    
    # 테스트 텍스트
    test_text = "강화 성공 +10\n골드 +500G"
    
    # 폰트 가져오기
    font = gen._get_font(40)
    print(f"폰트 로드됨: {font is not None}")
    
    # 이미지 생성
    img = Image.new('RGB', (600, 200), 'white')
    draw = ImageDraw.Draw(img)
    
    # 텍스트 그리기
    draw.text((20, 50), test_text, fill='black', font=font)
    
    # 저장
    output_path = '/tmp/font_test.png'
    img.save(output_path)
    print(f"테스트 이미지 저장: {output_path}")
    
    # 폰트 경로 확인
    galmuri_path = '/usr/share/fonts/truetype/custom/Galmuri11.ttf'
    noto_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    
    print(f"\n폰트 파일 확인:")
    print(f"  Galmuri11.ttf: {os.path.exists(galmuri_path)}")
    print(f"  NotoSansCJK-Regular.ttc: {os.path.exists(noto_path)}")
    
    # 직접 폰트 로드 테스트
    if os.path.exists(galmuri_path):
        try:
            test_font = ImageFont.truetype(galmuri_path, 40)
            print(f"\nGalmuri 폰트 직접 로드 성공")
        except Exception as e:
            print(f"\nGalmuri 폰트 로드 실패: {e}")
    
    if os.path.exists(noto_path):
        try:
            test_font = ImageFont.truetype(noto_path, 40)
            print(f"Noto 폰트 직접 로드 성공")
        except Exception as e:
            print(f"Noto 폰트 로드 실패: {e}")

if __name__ == '__main__':
    from PIL import ImageFont
    test_fonts()
