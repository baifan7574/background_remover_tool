# 功能开关配置
# 新功能默认关闭，测试通过后再开启
# 这样可以避免新功能影响现有功能

FEATURE_FLAGS = {
    # ========== 现有功能（已稳定，保持开启） ==========
    'background_remover': True,      # 背景移除
    'image_compressor': True,        # 图片压缩
    'format_converter': True,        # 格式转换
    'image_cropper': True,           # 图片裁剪
    'keyword_analyzer': True,        # 关键词分析
    'currency_converter': True,      # 汇率换算
    
    # ========== 问题功能（已关闭） ==========
    'add_watermark': False,          # 加水印（旧版，有问题）
    'add_watermark_v2': False,       # 加水印（新版，有问题）
    'remove_watermark': False,       # 去水印（有问题）
    
    # ========== 新功能（开发中，默认关闭） ==========
    'image_rotate_flip': False,      # 图片旋转/翻转（开发中）
    'brightness_contrast': False,    # 亮度/对比度调节（开发中）
    'batch_workflow': False,         # 批量处理工作流（开发中）
    'product_batch_processing': False,  # 产品图片批量处理（开发中）
    'ai_product_description': False, # AI产品描述生成（开发中）
}

def is_feature_enabled(feature_name):
    """检查功能是否启用"""
    return FEATURE_FLAGS.get(feature_name, False)

def enable_feature(feature_name):
    """启用功能（仅用于测试）"""
    if feature_name in FEATURE_FLAGS:
        FEATURE_FLAGS[feature_name] = True
        return True
    return False

def disable_feature(feature_name):
    """禁用功能（用于快速关闭问题功能）"""
    if feature_name in FEATURE_FLAGS:
        FEATURE_FLAGS[feature_name] = False
        return True
    return False

