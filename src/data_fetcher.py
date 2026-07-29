"""
小米空头监控系统 - 数据抓取模块
"""

import urllib.request
import json
import csv
import io
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *


class HKEXShortSellingFetcher:
    """HKEX 每日卖空数据抓取器"""
    
    def __init__(self):
        self.url = HKEX_SHORT_SELLING_URL
    
    def fetch(self) -> Optional[Dict]:
        """获取今日卖空数据"""
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=30)
            content = resp.read().decode('utf-8', errors='ignore')
            
            return self._parse(content)
        except Exception as e:
            print(f"[ERROR] Failed to fetch HKEX data: {e}")
            return None
    
    def _parse(self, content: str) -> Optional[Dict]:
        """解析 HKEX 数据"""
        result = {
            "date": None,
            "stock": {},
            "market": {}
        }
        
        # 提取交易日期
        date_match = re.search(r'TRADING DATE\s*:\s*(\d{1,2}\s+\w+\s+\d{4})', content)
        if date_match:
            try:
                date_str = date_match.group(1)
                result["date"] = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
            except:
                result["date"] = datetime.now().strftime('%Y-%m-%d')
        
        # 提取小米数据 (1810 XIAOMI-W)
        xiaomi_pattern = rf'{STOCK_CODE}\s+{STOCK_NAME}[\w-]*\s+([\d,]+)\s+([\d,]+)'
        xiaomi_match = re.search(xiaomi_pattern, content)
        
        if xiaomi_match:
            short_shares = int(xiaomi_match.group(1).replace(',', ''))
            short_turnover = int(xiaomi_match.group(2).replace(',', ''))
            
            result["stock"] = {
                "code": STOCK_CODE,
                "name": STOCK_NAME,
                "short_shares": short_shares,
                "short_turnover_hkd": short_turnover,
                "implied_price": round(short_turnover / short_shares, 2) if short_shares > 0 else 0
            }
        
        # 提取全市场数据
        market_match = re.search(
            r'Short Selling Turnover Total Value.*?HKD\s+([\d,]+).*?'
            r'Total market turnover.*?HKD([\d,]+).*?'
            r'Short Selling.*?as % total turnover\s+(\d+)%',
            content, re.DOTALL
        )
        
        if market_match:
            result["market"] = {
                "short_selling_total_hkd": int(market_match.group(1).replace(',', '')),
                "market_turnover_hkd": int(market_match.group(2).replace(',', '')),
                "short_ratio_pct": int(market_match.group(3))
            }
        
        return result if result["stock"] else None


class SFCShortPositionFetcher:
    """SFC 每周空仓报告抓取器"""
    
    def __init__(self):
        self.base_url = SFC_BASE_URL
    
    def fetch_latest(self) -> Optional[Dict]:
        """获取最新的 SFC 报告"""
        # 尝试最近 8 周的报告（SFC 数据可能有延迟）
        today = datetime.now()
        for weeks_back in range(0, 8):
            # 计算 N 周前的周四
            days_since_thursday = (today.weekday() - 3) % 7
            most_recent_thursday = today - timedelta(days=days_since_thursday)
            thursday = most_recent_thursday - timedelta(weeks=weeks_back)
            
            result = self._fetch_by_date(thursday)
            if result:
                return result
        
        return None
    
    def _fetch_by_date(self, date: datetime) -> Optional[Dict]:
        """按日期获取 SFC 报告"""
        date_str = date.strftime('%Y%m%d')
        # URL 格式: /YYYY/MM/DD/filename.csv
        url = f"{self.base_url}/{date.strftime('%Y/%m/%d')}/Short_Position_Reporting_Aggregated_Data_{date_str}.csv"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=30)
            content = resp.read().decode('utf-8', errors='ignore')
            
            return self._parse_csv(content, date_str)
        except Exception as e:
            return None
    
    def _parse_csv(self, content: str, date_str: str) -> Optional[Dict]:
        """解析 SFC CSV"""
        reader = csv.DictReader(io.StringIO(content))
        
        for row in reader:
            if row.get('Stock Code', '').strip() == STOCK_CODE:
                return {
                    "report_date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                    "stock_code": STOCK_CODE,
                    "stock_name": STOCK_NAME,
                    "short_position_shares": int(row.get('Aggregated Reportable Short Positions (Shares)', 0)),
                    "short_position_value_hkd": int(row.get('Aggregated Reportable Short Positions (HK$)', 0))
                }
        
        return None


class StockPriceFetcher:
    """股价数据抓取器"""
    
    def __init__(self):
        self.ticker = f"{STOCK_CODE}{STOCK_SUFFIX}"
    
    def fetch(self, days: int = 5) -> Optional[List[Dict]]:
        """获取股价数据"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(self.ticker)
            hist = ticker.history(period=f"{days}d")
            
            if hist.empty:
                return self._fetch_fallback()
            
            prices = []
            for idx, row in hist.iterrows():
                prices.append({
                    "date": idx.strftime('%Y-%m-%d'),
                    "close": round(float(row['Close']), 2),
                    "volume": int(row['Volume']),
                    "high": round(float(row['High']), 2),
                    "low": round(float(row['Low']), 2),
                    "open": round(float(row['Open']), 2)
                })
            
            return prices
        except Exception as e:
            print(f"[WARN] yfinance failed: {e}, using fallback")
            return self._fetch_fallback()
    
    def _fetch_fallback(self) -> Optional[List[Dict]]:
        """备用方案：从 HKEX 数据推算价格"""
        fetcher = HKEXShortSellingFetcher()
        data = fetcher.fetch()
        
        if data and data.get("stock", {}).get("implied_price"):
            return [{
                "date": data.get("date", datetime.now().strftime('%Y-%m-%d')),
                "close": data["stock"]["implied_price"],
                "volume": None,
                "source": "hkex_implied"
            }]
        
        return None


class HKEXnewsFetcher:
    """HKEXnews 公告抓取器"""
    
    def __init__(self):
        self.url = HKEXNEWS_SEARCH_URL
    
    def fetch_recent(self, days: int = 7) -> List[Dict]:
        """获取最近的公告"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'lang': 'EN',
            'stock': STOCK_SUFFIX_HKEX,
            'category': '0',
            'from': start_date.strftime('%Y%m%d'),
            'to': end_date.strftime('%Y%m%d')
        }
        
        url = f"{self.url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=30)
            content = resp.read().decode('utf-8', errors='ignore')
            
            return self._parse(content)
        except Exception as e:
            print(f"[ERROR] Failed to fetch HKEXnews: {e}")
            return []
    
    def _parse(self, content: str) -> List[Dict]:
        """解析 HKEXnews 公告"""
        events = []
        
        # 提取公告标题
        title_pattern = r'<div class="headline">(.*?)</div>'
        titles = re.findall(title_pattern, content, re.DOTALL)
        
        # 提取日期
        date_pattern = r'(\d{2}/\d{2}/\d{4})'
        dates = re.findall(date_pattern, content)
        
        # 提取 PDF 链接
        link_pattern = r'href="(/listedco/listconews/[^"]+\.pdf)"'
        links = re.findall(link_pattern, content)
        
        for i, title in enumerate(titles[:10]):  # 最多取 10 条
            # 清理标题
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            clean_title = clean_title.replace('&#x2f;', '/').replace('&#x3b;', ';')
            
            # 分类事件
            event_type = self._classify_event(clean_title)
            
            events.append({
                "date": dates[i] if i < len(dates) else "",
                "title": clean_title[:100] + "..." if len(clean_title) > 100 else clean_title,
                "type": event_type,
                "pdf_url": f"https://www1.hkexnews.hk{links[i]}" if i < len(links) else ""
            })
        
        return events
    
    def _classify_event(self, title: str) -> str:
        """根据标题分类事件类型"""
        title_lower = title.lower()
        
        for event_type, keywords in EVENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return event_type
        
        return "other"


def fetch_all_data() -> Dict:
    """抓取所有数据"""
    print("[INFO] Fetching all data...")
    
    # 1. HKEX 每日卖空数据
    print("[INFO] Fetching HKEX short selling data...")
    hkex_fetcher = HKEXShortSellingFetcher()
    hkex_data = hkex_fetcher.fetch()
    
    # 2. SFC 每周空仓报告
    print("[INFO] Fetching SFC short position data...")
    sfc_fetcher = SFCShortPositionFetcher()
    sfc_data = sfc_fetcher.fetch_latest()
    
    # 3. 股价数据
    print("[INFO] Fetching stock price data...")
    price_fetcher = StockPriceFetcher()
    price_data = price_fetcher.fetch(days=10)
    
    # 4. 公告事件
    print("[INFO] Fetching HKEXnews announcements...")
    news_fetcher = HKEXnewsFetcher()
    news_data = news_fetcher.fetch_recent(days=14)
    
    return {
        "fetch_time": datetime.now().isoformat(),
        "hkex_short_selling": hkex_data,
        "sfc_short_position": sfc_data,
        "stock_prices": price_data,
        "events": news_data
    }


if __name__ == "__main__":
    # 测试数据抓取
    data = fetch_all_data()
    print(json.dumps(data, indent=2, ensure_ascii=False))
