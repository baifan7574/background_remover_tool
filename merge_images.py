from PIL import Image, ImageDraw, ImageFont
import os

# 定义路径
img_after_path = r'C:\Users\bai\.gemini\antigravity\brain\60dc866c-fb53-45fd-a211-0356f1560c64\uploaded_image_0_1767274028813.png'
img_before_path = r'C:\Users\bai\.gemini\antigravity\brain\60dc866c-fb53-45fd-a211-0356f1560c64\uploaded_image_1_1767274028813.jpg'
output_dir = r'd:\quicktoolshub\雷达监控。\Sites\NBFive\ProductHunt'
output_file = os.path.join(output_dir, 'background_remover_comparison.png')

# 加载图片
img_before = Image.open(img_before_path)
img_after = Image.open(img_after_path)

# 统一尺寸（以 before 为准）
width, height = img_before.size
img_after = img_after.resize((width, height), Image.Resampling.LANCZOS)

# 创建画布
combined = Image.new('RGB', (width * 2 + 20, height + 100), (255, 255, 255))
combined.paste(img_before, (0, 80))
combined.paste(img_after, (width + 20, 80))

# 添加文字标注
draw = ImageDraw.Draw(combined)
try:
    # 尝试加载字体
    font = ImageFont.truetype("arial.ttf", 48)
except:
    font = ImageFont.load_default()

# 绘制标题
draw.text((width // 2 - 60, 20), "BEFORE", fill=(100, 100, 100), font=font)
draw.text((width + width // 2 - 40, 20), "AFTER", fill=(43, 108, 255), font=font)

# 保存
combined.save(output_file)
print(f"✅ 对比图已生成: {output_file}")

# 同时保存原始图到该文件夹
img_before.save(os.path.join(output_dir, 'example_before.jpg'))
img_after.save(os.path.join(output_dir, 'example_after.png'))
print(f"✅ 原始示例图已归档")
