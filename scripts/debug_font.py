#!/usr/bin/env python3
"""
폰트 디버깅 스크립트
"""
from image_generator import ImageGenerator
from PIL import Image, ImageDraw, ImageFont
import os
import platform

def test_fonts():
    """폰트 테스트 및 디버깅"""
    print(f"Platform: {platform.system()}")
    print()
    
    gen = ImageGenerator()
    
    # 폰트 경로 확인
    galmuri_path = '/usr/share/fonts/truetype/custom/Galmuri11.ttf'
    noto_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    
    print("폰트 파일 확인:")
    print(f"  Galmuri11.ttf: {os.path.exists(galmuri_path)}")
    print(f"  NotoSansCJK-Regular.ttc: {os.path.exists(noto_path)}")
    print()
    
    # 직접 폰트 로드 테스트
    print("직접 폰트 로드 테스트:")
    if os.path.exists(galmuri_path):
        try:
            font = ImageFont.truetype(galmuri_path, 40)
            img = Image.new('RGB', (400, 100), 'white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 30), '강화 성공 +10', fill='black', font=font)
            print("  ✅ Galmuri 폰트 로드 및 렌더링 성공")
        except Exception as e:
            print(f"  ❌ Galmuri 폰트 로드 실패: {e}")
    
    if os.path.exists(noto_path):
        try:
            font = ImageFont.truetype(noto_path, 40)
            img = Image.new('RGB', (400, 100), 'white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 30), '강화 성공 +10', fill='black', font=font)
            print("  ✅ Noto 폰트 로드 및 렌더링 성공")
        except Exception as e:
            print(f"  ❌ Noto 폰트 로드 실패: {e}")
    
    print()
    print("ImageGenerator 폰트 테스트:")
    font = gen._get_font(40)
    print(f"  폰트 로드됨: {font is not None}")
    print(f"  폰트 타입: {type(font)}")
    
    # 실제 이미지 생성 테스트
    print()
    print("이미지 생성 테스트:")
    try:
        img_path = gen.generate_enhancement_image(
            level=10,
            is_success=True,
            gold=1000,
            next_cost=100,
            next_success_rate=50.0,
            attempts=10,
            successes=7,
            failures=3
        )
        print(f"  ✅ 이미지 생성 성공: {img_path}")
        print(f"  파일 존재: {os.path.exists(img_path) if img_path else False}")
    except Exception as e:
        print(f"  ❌ 이미지 생성 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_fonts()
