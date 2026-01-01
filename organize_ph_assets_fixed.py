import shutil
import os

brain_dir = r'C:\Users\bai\.gemini\antigravity\brain\60dc866c-fb53-45fd-a211-0356f1560c64'
# 修正后的路径：就在 NBFive 根目录下
output_dir = r'd:\quicktoolshub\雷达监控。\NBFive\ProductHunt'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

mapping = {
    'homepage_1767274096135.png': '01_homepage.png',
    'tools_list_1767274119737.png': '02_tools_list.png',
    'background_remover_page_1767274155655.png': '03_background_remover_tool.png',
    'keyword_analysis_page_1767274188079.png': '04_keyword_analysis_tool.png',
    'nbfive_clean_logo_1767273200229.png': '00_nbfive_clean_logo.png',
    'uploaded_image_1_1767274028813.jpg': 'example_guitar_before.jpg',
    'uploaded_image_0_1767274028813.png': 'example_guitar_after.png'
}

for src_name, dest_name in mapping.items():
    src_path = os.path.join(brain_dir, src_name)
    dest_path = os.path.join(output_dir, dest_name)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"✅ Copied {src_name} to {dest_name}")
    else:
        print(f"❌ Source not found: {src_name}")

# 生成对比图（如果还没生成过或者需要重新生成到新位置）
from PIL import Image, ImageDraw, ImageFont
img_after_path = os.path.join(brain_dir, 'uploaded_image_0_1767274028813.png')
img_before_path = os.path.join(brain_dir, 'uploaded_image_1_1767274028813.jpg')
output_file = os.path.join(output_dir, 'background_remover_comparison.png')

if os.path.exists(img_before_path) and os.path.exists(img_after_path):
    img_before = Image.open(img_before_path)
    img_after = Image.open(img_after_path)
    width, height = img_before.size
    img_after = img_after.resize((width, height), Image.Resampling.LANCZOS)
    combined = Image.new('RGB', (width * 2 + 20, height + 100), (255, 255, 255))
    combined.paste(img_before, (0, 80))
    combined.paste(img_after, (width + 20, 80))
    draw = ImageDraw.Draw(combined)
    try: font = ImageFont.truetype("arial.ttf", 48)
    except: font = ImageFont.load_default()
    draw.text((width // 2 - 60, 20), "BEFORE", fill=(100, 100, 100), font=font)
    draw.text((width + width // 2 - 40, 20), "AFTER", fill=(43, 108, 255), font=font)
    combined.save(output_file)
    print(f"✅ 对比图已重新生成至新位置")
