# 小米空头监控系统

自动化的空头持仓监控仪表盘，每日生成小米集团（01810.HK）的空头分析报告。

## 🎯 功能特性

### 数据监控
- **每日数据**：HKEX 卖空成交（股数、金额）、隐含股价
- **周度数据**：SFC 淡仓报告（空仓股数、市值）
- **事件追踪**：HKEXnews 公告（回购、财报、投资等）

### 智能分析
自动判断空头行为模式：
- 📈 **空头加仓**：空仓增加 + 卖空活跃 + 股价承压
- 📉 **空头回补**：空仓减少 + 买盘增加 + 股价反弹
- ➡️ **做市/套利**：空仓稳定 + 卖空量波动 + 股价平稳
- 🚨 **高度警惕**：空仓大幅增加 + 卖空激增 + 股价大跌

### 输出格式
- 每日 Markdown 格式日报
- JSON 格式原始数据（便于后续分析）
- 自动生成并提交到 Git 仓库

## 📁 项目结构

```
小米股价/
├── .github/
│   └── workflows/
│       └── daily_report.yml    # GitHub Actions 工作流
├── src/
│   ├── config.py              # 配置文件
│   ├── data_fetcher.py        # 数据抓取模块
│   ├── analyzer.py            # 分析引擎
│   ├── report_generator.py    # 报告生成器
│   └── main.py                # 主程序入口
├── data/
│   ├── daily/                 # 每日数据（JSON）
│   └── weekly/                # 每周 SFC 数据
├── reports/                   # 生成的日报（Markdown）
└── README.md
```

## 🚀 快速开始

### 方式一：GitHub Actions（推荐）

1. **Fork 或 Clone 本项目**
   ```bash
   git clone https://github.com/yourusername/xiaomi-short-monitor.git
   ```

2. **推送到 GitHub**
   ```bash
   cd xiaomi-short-monitor
   git remote set-url origin https://github.com/yourusername/xiaomi-short-monitor.git
   git push -u origin main
   ```

3. **启用 GitHub Actions**
   - 进入仓库 Settings → Actions → General
   - 选择 "Allow all actions"
   - 保存设置

4. **手动触发首次运行**
   - 进入 Actions 页面
   - 选择 "小米空头监控日报" workflow
   - 点击 "Run workflow"

系统将在每个交易日 17:00 HKT 自动运行，生成日报并提交到仓库。

### 方式二：本地运行

1. **安装依赖**
   ```bash
   pip install yfinance requests beautifulsoup4
   ```

2. **运行主程序**
   ```bash
   python src/main.py
   ```

3. **查看报告**
   ```bash
   cat reports/$(date +%Y-%m-%d).md
   ```

## 📊 数据来源

| 数据源 | 更新频率 | 数据内容 |
|--------|----------|----------|
| [HKEX 短仓报告](https://www.hkex.com.hk/eng/stat/smstat/ssturnover/ncms/ASHTMAIN.HTM) | 每日 | 卖空股数、卖空金额 |
| [SFC 淡仓报告](https://www.sfc.hk/en/Regulatory-functions/Market/Short-position-reporting) | 每周四 | 空仓股数、空仓市值 |
| [Yahoo Finance](https://finance.yahoo.com/quote/1810.HK/) | 实时 | 股价、成交量 |
| [HKEXnews](https://www1.hkexnews.hk/) | 实时 | 公司公告 |

## ⚙️ 配置说明

编辑 `src/config.py` 可自定义：

- **股票代码**：默认监控小米（01810），可改为其他港股
- **分析阈值**：调整空头行为判断的敏感度
- **事件关键词**：添加或修改事件分类规则

## 📈 报告示例

```markdown
# 小米空头监控日报 2026-07-29

## 📊 今日核心指标
| 指标 | 数值 | 备注 |
|------|------|------|
| 收盘价 | HK$31.45 | 📈 +2.3% |
| 卖空金额 | HK$39.1 亿 | 高 |
| 空仓股数 | 14.06 亿股 | 大 |
| 空仓市值 | HK$378 亿 | - |

## 🔍 分析结论
**判断：空头小幅加仓**（置信度：75%）

分析依据：空仓增加 + 卖空活跃 + 股价承压

触发信号：
- 📈 空仓增加
- 📊 卖空量偏高
- ➡️ 股价平稳

## 📰 近期重要事件
- 💰 [29/07/2026] 股东大会通过回购授权
- 📊 [15/07/2026] 2026 Q2 财报发布
- 🚗 [01/07/2026] 6月汽车交付量公布
```

## ⚠️ 免责声明

本项目仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

## 📝 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
