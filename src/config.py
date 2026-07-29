"""
小米空头监控系统 - 配置文件
"""

# 股票配置
STOCK_CODE = "1810"
STOCK_NAME = "XIAOMI"
STOCK_NAME_CN = "小米集团"
STOCK_SUFFIX = ".HK"
STOCK_SUFFIX_HKEX = "01810"

# 数据源 URLs
HKEX_SHORT_SELLING_URL = "https://www.hkex.com.hk/eng/stat/smstat/ssturnover/ncms/ASHTMAIN.HTM"
SFC_BASE_URL = "https://www.sfc.hk/-/media/EN/pdf/spr"
HKEXNEWS_SEARCH_URL = "https://www1.hkexnews.hk/search/titlesearch.xhtml"

# 分析阈值
THRESHOLDS = {
    "short_ratio_high": 0.15,
    "short_ratio_extreme": 0.20,
    "position_change_significant": 0.05,
    "position_change_major": 0.10,
    "volume_surge": 2.0,
    "price_change_significant": 0.03,
}

# 空头行为判断规则
SHORT_POSITION_RULES = {
    "short_accumulation": {
        "name_cn": "空头加仓",
        "name_en": "Short Accumulation",
        "description": "空仓增加 + 卖空活跃 + 股价承压",
        "signals": ["position_increase", "high_short_volume", "price_weakness"]
    },
    "short_covering": {
        "name_cn": "空头回补",
        "name_en": "Short Covering", 
        "description": "空仓减少 + 买盘增加 + 股价反弹",
        "signals": ["position_decrease", "low_short_volume", "price_strength"]
    },
    "market_making": {
        "name_cn": "做市/套利",
        "name_en": "Market Making / Arbitrage",
        "description": "空仓稳定 + 卖空量波动 + 股价平稳",
        "signals": ["position_stable", "variable_short_volume", "price_stable"]
    },
    "high_alert": {
        "name_cn": "高度警惕",
        "name_en": "High Alert",
        "description": "空仓大幅增加 + 卖空激增 + 股价大跌",
        "signals": ["position_surge", "extreme_short_volume", "price_drop"]
    }
}

# 事件关键词
EVENT_KEYWORDS = {
    "buyback": ["repurchase", "buy-back", "buyback", "回购", "購回"],
    "earnings": ["results", "annual", "interim", "quarterly", "业绩", "财报", "中期", "年度"],
    "delivery": ["delivery", "deliveries", "交付", "出货"],
    "investment": ["acquisition", "investment", "strategic", "投资", "收购", "战略"],
    "dividend": ["dividend", "股息", "派息"],
}

# 报告配置
REPORT_CONFIG = {
    "title": "小米空头监控日报",
    "emoji": {
        "up": "📈",
        "down": "📉",
        "neutral": "➡️",
        "warning": "⚠️",
        "alert": "🚨",
        "info": "📊",
        "event": "📰",
        "analysis": "🔍",
    }
}
