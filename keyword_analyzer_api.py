"""
关键词分析API模块
包含所有6个关键词分析功能的模拟实现
后续接入真实API时，只需替换对应的函数即可
"""

import random
from datetime import datetime, timedelta

def get_action_name(action):
    """获取操作的中文名称"""
    action_names = {
        'extract': '提取',
        'competition': '竞争度查询',
        'trend': '趋势分析',
        'compare': '竞品对比',
        'longtail': '长尾关键词挖掘'
    }
    return action_names.get(action, '分析')

def generate_mock_keyword_extract(product_description, platform):
    """
    生成模拟的关键词提取数据
    
    ⚠️ 注意：这是模拟数据！
    ⚠️ 后续接入真实GPT API时，替换此函数即可：
    
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个专业的跨境电商关键词分析师"},
            {"role": "user", "content": f"请为以下产品描述提取适合{platform}平台的关键词：{product_description}"}
        ]
    )
    # 解析response并返回关键词列表
    """
    keywords = []
    base_keywords = product_description.lower().split()
    
    # 生成关键词列表（模拟）
    keyword_list = []
    
    if base_keywords:
        base_word = base_keywords[0]
        keyword_list = [
            {'keyword': f'{base_word} {platform}', 'platform': platform, 'score': 9.5},
            {'keyword': f'best {base_word}', 'platform': platform, 'score': 9.0},
            {'keyword': f'{base_word} review', 'platform': platform, 'score': 8.5},
            {'keyword': f'{base_word} buy', 'platform': platform, 'score': 8.0},
            {'keyword': f'{base_word} price', 'platform': platform, 'score': 7.5},
            {'keyword': f'{base_word} sale', 'platform': platform, 'score': 7.0},
            {'keyword': f'{base_word} deals', 'platform': platform, 'score': 6.5},
            {'keyword': f'{base_word} discount', 'platform': platform, 'score': 6.0},
            {'keyword': f'cheap {base_word}', 'platform': platform, 'score': 7.5},
            {'keyword': f'professional {base_word}', 'platform': platform, 'score': 7.0},
        ]
        
        # 添加平台特定的关键词
        if platform == 'amazon':
            keyword_list.extend([
                {'keyword': f'{base_word} prime', 'platform': platform, 'score': 8.0},
                {'keyword': f'{base_word} amazon choice', 'platform': platform, 'score': 8.5},
            ])
        elif platform == 'temu':
            keyword_list.extend([
                {'keyword': f'{base_word} temu', 'platform': platform, 'score': 8.0},
                {'keyword': f'{base_word} wholesale', 'platform': platform, 'score': 7.5},
            ])
    
    return {
        'keywords': keyword_list[:15],  # 返回前15个关键词
        'total_count': len(keyword_list),
        'platform': platform,
        'note': '⚠️ 这是模拟数据，接入真实API后将显示真实数据'
    }

def generate_mock_competition_data(product_description, platform):
    """
    生成模拟的竞争度数据
    
    ⚠️ 注意：这是模拟数据！
    ⚠️ 后续接入真实亚马逊SP-API时，替换此函数即可：
    
    from sp_api.api import ProductSearch
    client = ProductSearch(...)
    
    result = client.search_items(
        keywords=product_description,
        marketplaceIds=['ATVPDKIKX0DER']  # US marketplace
    )
    # 解析result并返回竞争度数据
    """
    keywords = product_description.lower().split()[:5]
    competition_data = []
    
    for i, word in enumerate(keywords):
        if len(word) > 3:
            competition_level = random.choice(['low', 'medium', 'high'])
            competition_data.append({
                'keyword': word,
                'search_volume': random.randint(1000, 100000),
                'competition_level': competition_level,
                'cpc': f'${random.uniform(0.5, 5.0):.2f}',
                'trend': random.choice(['up', 'down', 'stable'])
            })
    
    # 添加一些常见的变体
    if keywords:
        base_word = keywords[0]
        competition_data.extend([
            {
                'keyword': f'best {base_word}',
                'search_volume': random.randint(5000, 50000),
                'competition_level': 'high',
                'cpc': f'${random.uniform(1.0, 3.0):.2f}',
                'trend': 'up'
            },
            {
                'keyword': f'{base_word} review',
                'search_volume': random.randint(2000, 20000),
                'competition_level': 'medium',
                'cpc': f'${random.uniform(0.8, 2.5):.2f}',
                'trend': 'stable'
            },
            {
                'keyword': f'{base_word} 2024',
                'search_volume': random.randint(3000, 30000),
                'competition_level': 'medium',
                'cpc': f'${random.uniform(1.0, 2.5):.2f}',
                'trend': 'up'
            },
        ])
    
    return {
        'competition_data': {
            'keywords': competition_data,
            'platform': platform,
            'total_keywords': len(competition_data)
        },
        'keywords': competition_data,  # 兼容前端
        'note': '⚠️ 这是模拟数据，接入真实API后将显示真实数据'
    }

def generate_mock_trend_data(product_description, platform):
    """
    生成模拟的趋势数据
    
    ⚠️ 注意：这是模拟数据！
    ⚠️ 后续接入真实亚马逊SP-API时，替换此函数即可：
    
    # 使用亚马逊SP-API获取历史搜索趋势
    """
    keyword = product_description.split()[0] if product_description else 'keyword'
    trend_data = []
    base_date = datetime.now()
    
    # 生成过去6个月的趋势数据
    for i in range(6):
        date = base_date - timedelta(days=30 * (5 - i))
        trend_data.append({
            'date': date.strftime('%Y-%m'),
            'search_volume': random.randint(1000, 10000),
            'competition': round(random.uniform(0.3, 0.9), 2)
        })
    
    return {
        'trend_data': {
            'keyword': keyword,
            'platform': platform,
            'data': trend_data,
            'overall_trend': random.choice(['increasing', 'decreasing', 'stable']),
            'growth_rate': round(random.uniform(-20, 50), 1)  # 增长率（%）
        },
        'note': '⚠️ 这是模拟数据，接入真实API后将显示真实数据'
    }

def generate_mock_comparison_data(competitor_asin, platform):
    """
    生成模拟的竞品对比数据
    
    ⚠️ 注意：这是模拟数据！
    ⚠️ 后续接入真实亚马逊SP-API时，替换此函数即可：
    
    # 查询竞品ASIN的关键词排名
    """
    comparison_keywords = [
        {'keyword': 'wireless headphone', 'your_rank': random.randint(1, 50), 'competitor_rank': random.randint(1, 50)},
        {'keyword': 'bluetooth headphone', 'your_rank': random.randint(1, 50), 'competitor_rank': random.randint(1, 50)},
        {'keyword': 'noise cancelling', 'your_rank': random.randint(1, 50), 'competitor_rank': random.randint(1, 50)},
        {'keyword': 'headphone sale', 'your_rank': random.randint(1, 50), 'competitor_rank': random.randint(1, 50)},
        {'keyword': 'best headphone', 'your_rank': random.randint(1, 50), 'competitor_rank': random.randint(1, 50)},
    ]
    
    return {
        'comparison_data': {
            'competitor_asin': competitor_asin,
            'platform': platform,
            'keywords': comparison_keywords,
            'overlap_ratio': round(random.uniform(0.3, 0.7), 2),
            'total_keywords': len(comparison_keywords)
        },
        'note': '⚠️ 这是模拟数据，接入真实API后将显示真实数据'
    }

def generate_mock_longtail_keywords(product_description, platform):
    """
    生成模拟的长尾关键词
    
    ⚠️ 注意：这是模拟数据！
    ⚠️ 后续接入真实GPT API时，替换此函数即可：
    
    # 使用GPT生成长尾关键词变体
    """
    base_words = product_description.lower().split()[:3]
    longtail_keywords = []
    
    prefixes = ['best', 'top', 'cheap', 'affordable', 'premium', 'professional', 'wireless', 'portable', 'quality', 'durable']
    suffixes = ['review', 'buy', 'price', 'sale', 'deals', 'discount', '2024', '2025', 'guide', 'tips']
    modifiers = ['for', 'with', 'without', 'pro', 'plus', 'mini', 'max']
    
    if base_words:
        base_word = base_words[0]
        keyword_set = set()  # 使用set避免重复
        
        for prefix in prefixes[:6]:
            for suffix in suffixes[:5]:
                keyword = f'{prefix} {base_word} {suffix}'
                if keyword not in keyword_set:
                    keyword_set.add(keyword)
                    longtail_keywords.append({
                        'keyword': keyword,
                        'platform': platform,
                        'search_volume': random.randint(100, 5000),
                        'competition': random.choice(['low', 'medium']),
                        'cpc': f'${random.uniform(0.3, 2.0):.2f}'
                    })
        
        # 添加带修饰词的长尾关键词
        for modifier in modifiers[:4]:
            for suffix in suffixes[:3]:
                keyword = f'{base_word} {modifier} {suffix}'
                if keyword not in keyword_set and len(keyword) > 10:
                    keyword_set.add(keyword)
                    longtail_keywords.append({
                        'keyword': keyword,
                        'platform': platform,
                        'search_volume': random.randint(50, 2000),
                        'competition': 'low',
                        'cpc': f'${random.uniform(0.2, 1.5):.2f}'
                    })
    
    return {
        'longtail_keywords': longtail_keywords[:30],  # 返回前30个长尾关键词
        'total_count': len(longtail_keywords),
        'platform': platform,
        'note': '⚠️ 这是模拟数据，接入真实API后将显示真实数据'
    }

