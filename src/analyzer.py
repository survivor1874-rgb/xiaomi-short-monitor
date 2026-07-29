"""
小米空头监控系统 - 分析引擎
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *


class ShortPositionAnalyzer:
    """空头行为分析器"""
    
    def __init__(self):
        self.thresholds = THRESHOLDS
        self.rules = SHORT_POSITION_RULES
    
    def analyze(self, current_data: Dict, historical_data: Optional[List[Dict]] = None) -> Dict:
        """分析空头行为"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "signals": [],
            "judgment": None,
            "confidence": 0,
            "summary_cn": "",
            "summary_en": "",
            "metrics": {}
        }
        
        # 分析各项指标
        short_metrics = self._analyze_short_selling(current_data)
        position_metrics = self._analyze_position(current_data, historical_data)
        price_metrics = self._analyze_price(current_data, historical_data)
        
        analysis["metrics"] = {
            **short_metrics,
            **position_metrics,
            **price_metrics
        }
        
        # 判断空头行为
        judgment, confidence, signals = self._judge_behavior(
            short_metrics, position_metrics, price_metrics
        )
        
        analysis["judgment"] = judgment
        analysis["confidence"] = confidence
        analysis["signals"] = signals
        
        # 生成总结
        analysis["summary_cn"] = self._generate_summary_cn(analysis)
        analysis["summary_en"] = self._generate_summary_en(analysis)
        
        return analysis
    
    def _analyze_short_selling(self, data: Dict) -> Dict:
        """分析卖空数据"""
        metrics = {}
        
        hkex = data.get("hkex_short_selling", {})
        if not hkex or not hkex.get("stock"):
            return metrics
        
        stock = hkex["stock"]
        market = hkex.get("market", {})
        
        # 卖空股数
        metrics["short_shares"] = stock.get("short_shares", 0)
        metrics["short_turnover_hkd"] = stock.get("short_turnover_hkd", 0)
        
        # 卖空比例（占全市场）
        if market.get("market_turnover_hkd") and stock.get("short_turnover_hkd"):
            # 这里需要该股票的总成交额，暂时用隐含价格估算
            metrics["implied_price"] = stock.get("implied_price", 0)
        
        # 卖空金额级别
        turnover = stock.get("short_turnover_hkd", 0)
        if turnover > 5e9:
            metrics["short_volume_level"] = "极高"
        elif turnover > 2e9:
            metrics["short_volume_level"] = "高"
        elif turnover > 1e9:
            metrics["short_volume_level"] = "中等"
        else:
            metrics["short_volume_level"] = "低"
        
        return metrics
    
    def _analyze_position(self, current: Dict, historical: Optional[List[Dict]] = None) -> Dict:
        """分析空仓变化"""
        metrics = {}
        
        sfc = current.get("sfc_short_position")
        if not sfc:
            return metrics
        
        metrics["position_shares"] = sfc.get("short_position_shares", 0)
        metrics["position_value_hkd"] = sfc.get("short_position_value_hkd", 0)
        metrics["position_date"] = sfc.get("report_date", "")
        
        # 计算空仓市值级别
        value = sfc.get("short_position_value_hkd", 0)
        if value > 50e9:
            metrics["position_size_level"] = "极大"
        elif value > 30e9:
            metrics["position_size_level"] = "大"
        elif value > 10e9:
            metrics["position_size_level"] = "中等"
        else:
            metrics["position_size_level"] = "小"
        
        # 与历史数据对比
        if historical:
            prev_data = self._get_previous_sfc_data(historical)
            if prev_data:
                prev_shares = prev_data.get("short_position_shares", 0)
                if prev_shares > 0:
                    change_pct = (sfc["short_position_shares"] - prev_shares) / prev_shares
                    metrics["position_change_pct"] = round(change_pct * 100, 2)
                    
                    if abs(change_pct) > self.thresholds["position_change_major"]:
                        metrics["position_change_level"] = "重大变化"
                    elif abs(change_pct) > self.thresholds["position_change_significant"]:
                        metrics["position_change_level"] = "显著变化"
                    else:
                        metrics["position_change_level"] = "稳定"
                    
                    metrics["position_trend"] = "增加" if change_pct > 0 else "减少"
        
        return metrics
    
    def _analyze_price(self, current: Dict, historical: Optional[List[Dict]] = None) -> Dict:
        """分析价格走势"""
        metrics = {}
        
        prices = current.get("stock_prices", [])
        if not prices:
            return metrics
        
        latest = prices[-1]
        metrics["latest_price"] = latest.get("close", 0)
        metrics["latest_date"] = latest.get("date", "")
        
        # 计算价格变化
        if len(prices) >= 2:
            prev_price = prices[-2].get("close", 0)
            if prev_price > 0:
                change_pct = (latest["close"] - prev_price) / prev_price
                metrics["price_change_pct"] = round(change_pct * 100, 2)
                
                if abs(change_pct) > self.thresholds["price_change_significant"]:
                    metrics["price_change_level"] = "大幅波动"
                else:
                    metrics["price_change_level"] = "平稳"
                
                metrics["price_trend"] = "上涨" if change_pct > 0 else "下跌"
        
        # 计算 5 日趋势
        if len(prices) >= 5:
            five_days_ago = prices[-5].get("close", 0)
            if five_days_ago > 0:
                five_day_change = (latest["close"] - five_days_ago) / five_days_ago
                metrics["five_day_change_pct"] = round(five_day_change * 100, 2)
        
        return metrics
    
    def _get_previous_sfc_data(self, historical: List[Dict]) -> Optional[Dict]:
        """从历史数据中获取上一期 SFC 数据"""
        for data in reversed(historical):
            sfc = data.get("sfc_short_position")
            if sfc:
                return sfc
        return None
    
    def _judge_behavior(self, short_metrics: Dict, position_metrics: Dict, price_metrics: Dict) -> Tuple[str, int, List[str]]:
        """判断空头行为"""
        signals = []
        scores = {rule: 0 for rule in self.rules}
        
        # 分析空仓变化信号
        if position_metrics.get("position_trend") == "增加":
            if position_metrics.get("position_change_level") == "重大变化":
                signals.append("position_surge")
                scores["high_alert"] += 3
                scores["short_accumulation"] += 2
            else:
                signals.append("position_increase")
                scores["short_accumulation"] += 2
        
        elif position_metrics.get("position_trend") == "减少":
            if position_metrics.get("position_change_level") == "重大变化":
                signals.append("position_major_decrease")
                scores["short_covering"] += 3
            else:
                signals.append("position_decrease")
                scores["short_covering"] += 2
        else:
            signals.append("position_stable")
            scores["market_making"] += 1
        
        # 分析卖空量信号
        volume_level = short_metrics.get("short_volume_level", "")
        if volume_level in ["极高", "高"]:
            signals.append("high_short_volume")
            scores["short_accumulation"] += 2
            scores["high_alert"] += 1
        elif volume_level == "低":
            signals.append("low_short_volume")
            scores["short_covering"] += 1
        
        # 分析价格信号
        price_trend = price_metrics.get("price_trend", "")
        price_change_level = price_metrics.get("price_change_level", "")
        
        if price_trend == "下跌" and price_change_level == "大幅波动":
            signals.append("price_drop")
            scores["high_alert"] += 2
            scores["short_accumulation"] += 1
        elif price_trend == "上涨":
            signals.append("price_strength")
            scores["short_covering"] += 1
        else:
            signals.append("price_stable")
            scores["market_making"] += 1
        
        # 选择得分最高的判断
        max_score = max(scores.values())
        if max_score == 0:
            return "market_making", 50, signals
        
        judgment = max(scores, key=scores.get)
        confidence = min(95, max(50, int(max_score * 15 + 50)))
        
        return judgment, confidence, signals
    
    def _generate_summary_cn(self, analysis: Dict) -> str:
        """生成中文总结"""
        judgment = analysis.get("judgment", "")
        metrics = analysis.get("metrics", {})
        
        rule = self.rules.get(judgment, {})
        judgment_cn = rule.get("name_cn", "未知")
        description = rule.get("description", "")
        
        summary_parts = [f"**判断：{judgment_cn}**"]
        summary_parts.append(f"（置信度：{analysis.get('confidence', 0)}%）")
        summary_parts.append("")
        summary_parts.append(f"分析依据：{description}")
        
        # 添加具体数据
        if metrics.get("position_shares"):
            shares_b = metrics["position_shares"] / 1e8
            summary_parts.append(f"- 当前空仓：{shares_b:.2f} 亿股")
        
        if metrics.get("position_change_pct"):
            change = metrics["position_change_pct"]
            summary_parts.append(f"- 周环比变化：{'+' if change > 0 else ''}{change:.1f}%")
        
        if metrics.get("short_turnover_hkd"):
            turnover_b = metrics["short_turnover_hkd"] / 1e8
            summary_parts.append(f"- 今日卖空金额：HK${turnover_b:.1f} 亿")
        
        if metrics.get("latest_price"):
            summary_parts.append(f"- 最新股价：HK${metrics['latest_price']:.2f}")
        
        return "\n".join(summary_parts)
    
    def _generate_summary_en(self, analysis: Dict) -> str:
        """生成英文总结"""
        judgment = analysis.get("judgment", "")
        rule = self.rules.get(judgment, {})
        
        return f"{rule.get('name_en', 'Unknown')} - {rule.get('description', '')}"


def analyze_data(data: Dict, historical: Optional[List[Dict]] = None) -> Dict:
    """分析数据的入口函数"""
    analyzer = ShortPositionAnalyzer()
    return analyzer.analyze(data, historical)


if __name__ == "__main__":
    # 测试分析引擎
    with open("data/daily/test_data.json", "r") as f:
        test_data = json.load(f)
    
    result = analyze_data(test_data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
