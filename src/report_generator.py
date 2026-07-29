"""
小米空头监控系统 - 日报生成器
"""

import json
from datetime import datetime
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *


class DailyReportGenerator:
    """每日报告生成器"""
    
    def __init__(self):
        self.emoji = REPORT_CONFIG["emoji"]
        self.title = REPORT_CONFIG["title"]
    
    def generate(self, data: Dict, analysis: Dict) -> str:
        """生成日报 Markdown"""
        report = []
        
        # 标题
        date = self._get_report_date(data)
        report.append(f"# {self.title} {date}")
        report.append("")
        
        # 核心指标
        report.append(self._section_header("今日核心指标", self.emoji["info"]))
        report.append(self._generate_metrics_table(data, analysis))
        report.append("")
        
        # 周度空仓数据
        if data.get("sfc_short_position"):
            report.append(self._section_header("周度空仓数据（SFC）", self.emoji["info"]))
            report.append(self._generate_sfc_section(data, analysis))
            report.append("")
        
        # 分析结论
        report.append(self._section_header("分析结论", self.emoji["analysis"]))
        report.append(self._generate_analysis_section(analysis))
        report.append("")
        
        # 近期事件
        events = data.get("events", [])
        if events:
            report.append(self._section_header("近期重要事件", self.emoji["event"]))
            report.append(self._generate_events_section(events))
            report.append("")
        
        # 趋势图表（文字版）
        report.append(self._section_header("趋势观察", self.emoji["neutral"]))
        report.append(self._generate_trend_section(data, analysis))
        report.append("")
        
        # 数据来源
        report.append("---")
        report.append("")
        report.append("*数据来源：HKEX、SFC、HKEXnews | 自动生成时间：" + datetime.now().strftime("%Y-%m-%d %H:%M") + "*")
        
        return "\n".join(report)
    
    def _get_report_date(self, data: Dict) -> str:
        """获取报告日期"""
        hkex = data.get("hkex_short_selling", {})
        if hkex and hkex.get("date"):
            return hkex["date"]
        return datetime.now().strftime("%Y-%m-%d")
    
    def _section_header(self, title: str, emoji: str) -> str:
        """生成章节标题"""
        return f"## {emoji} {title}"
    
    def _generate_metrics_table(self, data: Dict, analysis: Dict) -> str:
        """生成核心指标表格"""
        metrics = analysis.get("metrics", {})
        lines = []
        
        lines.append("| 指标 | 数值 | 备注 |")
        lines.append("|------|------|------|")
        
        # 股价
        price = metrics.get("latest_price")
        price_change = metrics.get("price_change_pct", 0)
        if price:
            change_emoji = self.emoji["up"] if price_change > 0 else self.emoji["down"] if price_change < 0 else self.emoji["neutral"]
            lines.append(f"| 收盘价 | HK${price:.2f} | {change_emoji} {'+' if price_change > 0 else ''}{price_change:.1f}% |")
        
        # 卖空金额
        short_turnover = metrics.get("short_turnover_hkd")
        if short_turnover:
            lines.append(f"| 卖空金额 | HK${short_turnover/1e8:.1f} 亿 | {metrics.get('short_volume_level', '-')} |")
        
        # 卖空股数
        short_shares = metrics.get("short_shares")
        if short_shares:
            lines.append(f"| 卖空股数 | {short_shares/1e6:.1f} 百万股 | - |")
        
        # 空仓数据
        position_shares = metrics.get("position_shares")
        if position_shares:
            lines.append(f"| 空仓股数 | {position_shares/1e8:.2f} 亿股 | {metrics.get('position_size_level', '-')} |")
        
        position_value = metrics.get("position_value_hkd")
        if position_value:
            lines.append(f"| 空仓市值 | HK${position_value/1e8:.0f} 亿 | - |")
        
        return "\n".join(lines)
    
    def _generate_sfc_section(self, data: Dict, analysis: Dict) -> str:
        """生成 SFC 空仓数据部分"""
        sfc = data.get("sfc_short_position", {})
        metrics = analysis.get("metrics", {})
        lines = []
        
        if sfc:
            shares_b = sfc.get("short_position_shares", 0) / 1e8
            value_b = sfc.get("short_position_value_hkd", 0) / 1e8
            
            lines.append(f"- **报告日期**：{sfc.get('report_date', 'N/A')}")
            lines.append(f"- **空仓股数**：{shares_b:.2f} 亿股")
            lines.append(f"- **空仓市值**：HK${value_b:.0f} 亿")
            
            # 环比变化
            change_pct = metrics.get("position_change_pct")
            if change_pct is not None:
                change_emoji = self.emoji["warning"] if abs(change_pct) > 5 else self.emoji["neutral"]
                lines.append(f"- **周环比**：{change_emoji} {'+' if change_pct > 0 else ''}{change_pct:.1f}%")
                
                if abs(change_pct) > 10:
                    lines.append(f"- ⚠️ **重大变化**：空仓{'大幅增加' if change_pct > 0 else '大幅减少'}")
        
        return "\n".join(lines)
    
    def _generate_analysis_section(self, analysis: Dict) -> str:
        """生成分析结论部分"""
        lines = []
        
        judgment = analysis.get("judgment", "")
        confidence = analysis.get("confidence", 0)
        summary_cn = analysis.get("summary_cn", "")
        
        # 判断结果
        lines.append(summary_cn)
        lines.append("")
        
        # 信号列表
        signals = analysis.get("signals", [])
        if signals:
            lines.append("**触发信号：**")
            for signal in signals:
                signal_desc = self._get_signal_description(signal)
                lines.append(f"- {signal_desc}")
        
        return "\n".join(lines)
    
    def _get_signal_description(self, signal: str) -> str:
        """获取信号描述"""
        descriptions = {
            "position_increase": "📈 空仓增加",
            "position_surge": "🚨 空仓大幅增加",
            "position_decrease": "📉 空仓减少",
            "position_major_decrease": "📉 空仓大幅减少",
            "position_stable": "➡️ 空仓稳定",
            "high_short_volume": "📊 卖空量偏高",
            "low_short_volume": "📊 卖空量偏低",
            "price_drop": "📉 股价下跌",
            "price_strength": "📈 股价上涨",
            "price_stable": "➡️ 股价平稳",
        }
        return descriptions.get(signal, f"❓ {signal}")
    
    def _generate_events_section(self, events: List[Dict]) -> str:
        """生成事件部分"""
        lines = []
        
        # 按类型分组
        events_by_type = {}
        for event in events:
            event_type = event.get("type", "other")
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(event)
        
        # 类型图标
        type_icons = {
            "buyback": "💰",
            "earnings": "📊",
            "delivery": "🚗",
            "investment": "💼",
            "dividend": "💵",
            "other": "📄"
        }
        
        for event_type, type_events in events_by_type.items():
            icon = type_icons.get(event_type, "📄")
            for event in type_events[:3]:  # 每类最多显示 3 条
                date = event.get("date", "")
                title = event.get("title", "")
                lines.append(f"- {icon} [{date}] {title}")
        
        return "\n".join(lines)
    
    def _generate_trend_section(self, data: Dict, analysis: Dict) -> str:
        """生成趋势观察部分"""
        lines = []
        metrics = analysis.get("metrics", {})
        
        # 5 日趋势
        five_day_change = metrics.get("five_day_change_pct")
        if five_day_change is not None:
            trend_emoji = self.emoji["up"] if five_day_change > 0 else self.emoji["down"]
            lines.append(f"- **5日股价趋势**：{trend_emoji} {'+' if five_day_change > 0 else ''}{five_day_change:.1f}%")
        
        # 空仓趋势
        position_change = metrics.get("position_change_pct")
        if position_change is not None:
            if abs(position_change) > 10:
                lines.append(f"- **空仓趋势**：{self.emoji['warning']} 持续{'增加' if position_change > 0 else '减少'}，需密切关注")
            elif abs(position_change) > 5:
                lines.append(f"- **空仓趋势**：{'增加' if position_change > 0 else '减少'}中")
            else:
                lines.append(f"- **空仓趋势**：{self.emoji['neutral']} 相对稳定")
        
        # 综合建议
        judgment = analysis.get("judgment", "")
        if judgment == "high_alert":
            lines.append(f"- **关注提示**：{self.emoji['alert']} 多项指标异常，建议密切关注后续走势")
        elif judgment == "short_accumulation":
            lines.append(f"- **关注提示**：{self.emoji['warning']} 空头有加仓迹象，注意风险")
        elif judgment == "short_covering":
            lines.append(f"- **关注提示**：{self.emoji['up']} 空头回补中，或有反弹机会")
        
        return "\n".join(lines)


def generate_report(data: Dict, analysis: Dict) -> str:
    """生成报告的入口函数"""
    generator = DailyReportGenerator()
    return generator.generate(data, analysis)


if __name__ == "__main__":
    # 测试报告生成
    with open("data/daily/test_data.json", "r") as f:
        test_data = json.load(f)
    
    with open("data/daily/test_analysis.json", "r") as f:
        test_analysis = json.load(f)
    
    report = generate_report(test_data, test_analysis)
    print(report)
