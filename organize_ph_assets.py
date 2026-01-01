import shutil
import os

brain_dir = r'C:\Users\bai\.gemini\antigravity\brain\60dc866c-fb53-45fd-a211-0356f1560c64'
output_dir = r'd:\quicktoolshub\雷达监控。\Sites\NBFive\ProductHunt'

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
