from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os

def create_marketing_image(source_path, output_path, text="FREE REMOVER"):
    try:
        # 1. 打开原始图片
        if not os.path.exists(source_path):
            print(f"Error: Source image not found at {source_path}")
            # Create a dummy image if source doesn't exist
            img = Image.new('RGB', (800, 800), color = (73, 109, 137))
        else:
            img = Image.open(source_path)
        
        # 转换 convert to RGB just in case
        img = img.convert("RGB")
        
        # 2. 调整图片大小以适应社交媒体 (例如 1080x1080)
        # 这里为了演示，我们保持原比例但确保宽度至少 800
        target_width = 800
        ratio = target_width / float(img.size[0])
        target_height = int(float(img.size[1]) * float(ratio))
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # 3. 添加滤镜效果 (自动化美化)
        # 增加一点饱和度，让商品看起来更诱人
        converter = ImageEnhance.Color(img)
        img = converter.enhance(1.2)
        
        # 4. 绘制营销横幅 (Banner)
        # 在底部画一个半透明黑色背景
        banner_height = 100
        # Pillow doesn't support alpha on RGB directly for draw.rectangle unless we use a separate layer
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([(0, height - banner_height), (width, height)], fill=(0, 0, 0, 180))
        
        # 组合图层
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")
        
        # 5. 添加文字
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体，Windows通常有arial.ttf
        try:
            # 字体大小根据图片宽度动态调整
            font_size = int(banner_height * 0.5)
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
            
        # 计算文字位置居中
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) / 2
        y = (height - banner_height) + (banner_height - text_height) / 2 - 10 # 稍微向上调整
        
        # 绘制黄色高亮文字
        draw.text((x, y), text, font=font, fill=(255, 215, 0))
        
        # 6. 添加右上角的 "NEW" 标签
        tag_size = 120
        tag_overlay = Image.new('RGBA', img.size, (0,0,0,0))
        tag_draw = ImageDraw.Draw(tag_overlay)
        tag_color = (255, 69, 0, 230) # Red-Orange
        
        # 画一个圆形标签
        margin = 20
        tag_box = [width - tag_size - margin, margin, width - margin, margin + tag_size]
        tag_draw.ellipse(tag_box, fill=tag_color)
        
        # 组合
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, tag_overlay)
        img = img.convert("RGB")
        
        # 在标签上写字
        draw = ImageDraw.Draw(img)
        label_text = "FREE"
        try:
            label_font = ImageFont.truetype("arialbd.ttf", 40) # Bold
        except:
            label_font = font
            
        label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
        lw = label_bbox[2] - label_bbox[0]
        lh = label_bbox[3] - label_bbox[1]
        
        lx = tag_box[0] + (tag_size - lw) / 2
        ly = tag_box[1] + (tag_size - lh) / 2 - 5
        
        draw.text((lx, ly), label_text, fill=(255, 255, 255), font=label_font)

        # 7. 保存结果
        img.save(output_path)
        print(f"Success! Marketing image saved to: {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # 使用之前目录里看到的文件
    src = "d:\\background_remover_tool\\微信图片_20251115113626_133_94.png"
    dst = "d:\\background_remover_tool\\auto_marketing_post.png"
    
    # 如果源文件不存在，尝试另一个
    if not os.path.exists(src):
         src = "d:\\background_remover_tool\\downloaded_test.png"
         
    create_marketing_image(src, dst, text="No Watermark - 100% Free")
