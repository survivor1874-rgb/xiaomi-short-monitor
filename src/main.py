#!/usr/bin/env python3
"""
小米空头监控系统 - 主程序
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import fetch_all_data
from analyzer import analyze_data
from report_generator import generate_report


def ensure_directories():
    """确保必要的目录存在"""
    dirs = [
        "data/daily",
        "data/weekly",
        "reports"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def load_historical_data(days: int = 30) -> list:
    """加载历史数据用于对比分析"""
    historical = []
    data_dir = Path("data/daily")
    
    if not data_dir.exists():
        return historical
    
    files = sorted(data_dir.glob("*.json"), reverse=True)[:days]
    
    for f in files:
        try:
            with open(f, "r") as file:
                data = json.load(file)
                historical.append(data)
        except Exception as e:
            print(f"[WARN] Failed to load {f}: {e}")
    
    return historical


def save_data(data: dict, date_str: str):
    """保存数据到文件"""
    daily_file = f"data/daily/{date_str}.json"
    with open(daily_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Saved daily data: {daily_file}")
    
    if data.get("sfc_short_position"):
        weekly_file = f"data/weekly/sfc_{date_str}.json"
        with open(weekly_file, "w") as f:
            json.dump(data["sfc_short_position"], f, indent=2, ensure_ascii=False)
        print(f"[INFO] Saved weekly data: {weekly_file}")


def save_report(report: str, date_str: str):
    """保存报告到文件"""
    report_file = f"reports/{date_str}.md"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"[INFO] Saved report: {report_file}")
    return report_file


def main():
    """主函数"""
    print("=" * 60)
    print("小米空头监控系统 - 开始运行")
    print("=" * 60)
    print()
    
    # 1. 确保目录存在
    ensure_directories()
    
    # 2. 抓取数据
    print("[STEP 1] 抓取数据...")
    data = fetch_all_data()
    
    if not data:
        print("[ERROR] Failed to fetch data")
        sys.exit(1)
    
    # 3. 加载历史数据
    print("[STEP 2] 加载历史数据...")
    historical = load_historical_data(days=30)
    print(f"[INFO] Loaded {len(historical)} historical records")
    
    # 4. 分析数据
    print("[STEP 3] 分析数据...")
    analysis = analyze_data(data, historical)
    
    # 5. 生成报告
    print("[STEP 4] 生成报告...")
    report = generate_report(data, analysis)
    
    # 6. 确定日期 - 安全地处理 None 值
    hkex_data = data.get("hkex_short_selling")
    if hkex_data and isinstance(hkex_data, dict):
        date_str = hkex_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 7. 保存数据和报告
    print("[STEP 5] 保存数据...")
    save_data(data, date_str)
    
    print("[STEP 6] 保存报告...")
    report_file = save_report(report, date_str)
    
    # 8. 输出摘要
    print()
    print("=" * 60)
    print("运行完成！")
    print("=" * 60)
    print(f"报告已生成: {report_file}")
    print()
    print("报告预览（前 20 行）：")
    print("-" * 40)
    for line in report.split("\n")[:20]:
        print(line)
    print("...")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
