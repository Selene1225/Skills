# Fund Scraper MCP Server

一个基于 MCP (Model Context Protocol) 的基金数据爬取服务，通过浏览器自动化技术从天天基金网获取中国公募基金数据。

## 这是什么？

**MCP (Model Context Protocol)** 是 Anthropic 开发的开放协议，让 AI 助手（如 GitHub Copilot、Claude）能够调用外部工具和服务。

这个项目是一个 **MCP Server**，提供以下能力：
- 🔍 获取中国全部 **26000+ 只公募基金** 的代码和基本信息
- 📊 获取基金净值、增长率、排行榜数据
- 📈 获取基金详情（基金经理、规模、类型等）
- 📉 获取基金历史净值数据
- 💾 **支持命令行批量获取所有基金数据（边爬边写、断点续传）**

## 为什么需要它？

传统的基金数据 API 存在以下问题：
- ❌ 新浪财经 API 有反爬机制，IP 容易被封
- ❌ 天天基金网 API 排行榜接口不包含新发行的基金
- ❌ akshare 等库也存在部分基金找不到的情况

**本项目的解决方案：**
- ✅ 使用 Playwright 浏览器自动化，模拟真实用户访问
- ✅ 使用系统 Microsoft Edge 浏览器，无需下载额外浏览器
- ✅ 通过 `fundcode_search.js` 获取**真正的全量基金列表**
- ✅ 内置反检测机制，避免被封禁
- ✅ 支持 MCP 协议，可被各种 AI 助手调用
- ✅ **支持命令行直接使用，边爬边写，断点续传**

## 功能特性

### MCP 工具（供 AI 助手调用）

| 功能 | 描述 | 数据量 |
|------|------|--------|
| `scrape_all_fund_codes` | 获取全量基金代码列表 | 26000+ 只 |
| `scrape_fund_list` | 获取基金排行榜（含净值） | ~19000 只 |
| `scrape_fund_detail` | 获取单个基金详情 | 12+ 字段 |
| `scrape_fund_nav_history` | 获取净值历史 | 自定义时间范围 |
| `scrape_funds_batch` | 批量获取基金详情 | 自定义数量 |
| **`fetch_all_funds_info`** | **一键获取所有基金完整信息（推荐）** | **26000+ 只，12个字段** |
| `check_browser_status` | 检查浏览器状态 | - |

### 命令行工具（独立使用）

| 工具 | 功能 | 特性 |
|------|------|------|
| `fetch_funds.py` | 批量获取基金数据 | ✅ 边爬边写<br>✅ 断点续传<br>✅ 进度日志<br>✅ CSV 输出 |

---

## 🚀 快速开始

### 部署到新电脑（需要拷贝的文件）

如果要把这个项目部署到另一台电脑上运行，只需要拷贝以下文件：

```
fund_scraper_mcp/           # 整个文件夹
├── server.py              # MCP Server 主入口
├── browser_manager.py     # 浏览器管理
├── fetch_funds.py         # 命令行工具（重要！）
├── requirements.txt       # Python 依赖（重要！）
├── scrapers/              # 爬虫模块
│   ├── __init__.py
│   ├── base_scraper.py
│   └── eastmoney_scraper.py
└── utils/                 # 工具模块
    ├── __init__.py
    └── anti_detection.py
```

**❌ 不需要拷贝的文件/文件夹：**
- `__pycache__/` - Python 缓存文件
- `.vscode/` - VS Code 配置
- `test_*.csv` / `test_*.json` - 测试文件
- `*.log` - 日志文件
- `debug_*.png` / `debug_*.html` - 调试文件

**最简部署步骤：**

1. **拷贝整个 `fund_scraper_mcp` 文件夹**到新电脑（或使用 `git clone`）
2. **安装 Python 3.8 或更高版本**（推荐 3.11）
   - Windows: [python.org](https://www.python.org/downloads/) 下载安装
   - macOS: `brew install python@3.11`
   - Linux: `sudo apt install python3.11` (Ubuntu/Debian)
   - 验证安装: `python --version` 或 `python3 --version`
3. **安装 Microsoft Edge**（Windows 通常已有）
   - Windows: 系统自带，无需安装
   - macOS/Linux: [下载 Edge](https://www.microsoft.com/edge)
4. **安装 Python 依赖：**
   ```bash
   cd fund_scraper_mcp
   pip install -r requirements.txt
   ```
   或使用 `pip3` (如果系统同时有 Python 2 和 3):
   ```bash
   pip3 install -r requirements.txt
   ```
5. **开始使用！**（见下方使用方法）

---

## 📖 使用方法

### 方式一：图形界面（最简单，推荐新手）⭐

**适合场景：** 不熟悉命令行，想要可视化操作

#### 1. 双击启动

**Windows:**
- 直接双击 `启动基金数据获取工具.bat`
- 程序会自动检查 Python 和依赖，并启动图形界面

**或者手动启动:**
```bash
python fund_scraper_gui.py
```

#### 2. 图形界面操作

- **输出文件**: 点击"浏览"选择保存位置，或直接输入文件名
- **断点续传**: 如果之前中断过，勾选此项继续之前的进度
- **批次大小**: 每批处理多少个基金（默认100）
- **延迟**: 每个请求间隔秒数（默认1秒）
- 点击"**开始获取**"按钮，程序会：
  - ✅ 自动获取所有26000+个基金
  - ✅ 实时显示进度和日志
  - ✅ 数据边爬边写入文件
  - ✅ 可随时点击"停止"中断，下次续传

**特点：**
- 🎯 操作简单，无需命令行知识
- 📊 实时进度条和日志显示
- 💾 边爬边写，不怕中断
- 🔄 支持断点续传
- 📁 自动显示文件保存位置

---

### 方式二：命令行直接使用

**适合场景：** 熟悉命令行，需要自动化脚本

#### 1. 获取前100个基金（测试）
```bash
cd fund_scraper_mcp
python fetch_funds.py --max 100
```

#### 2. 获取所有基金（约26000+个）
```bash
python fetch_funds.py --all --output all_funds.csv
```

#### 3. 断点续传（如果中断了）
```bash
# 使用 Ctrl+C 停止后，用相同命令 + --resume 继续
python fetch_funds.py --all --output all_funds.csv --resume
```

#### 4. 自定义参数
```bash
# 获取前1000个，批次大小200，延迟0.5秒
python fetch_funds.py --max 1000 --batch 200 --delay 0.5 --output my_funds.csv
```

#### 5. 查看帮助
```bash
python fetch_funds.py --help
```

**命令行参数说明：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--max N` | 获取前 N 个基金 | `--max 100` |
| `--all` | 获取所有基金（约26000+个） | `--all` |
| `--output FILE` | 指定输出文件名 | `--output my_funds.csv` |
| `--resume` | 断点续传模式 | `--resume` |
| `--batch N` | 每批获取数量（默认100） | `--batch 200` |
| `--delay N` | 每个请求延迟秒数（默认1.0） | `--delay 0.5` |

**输出格式：** CSV 文件，包含12个字段（与新浪数据格式兼容）：
```csv
symbol,sname,per_nav,total_nav,yesterday_nav,nav_rate,nav_a,sg_states,nav_date,fund_manager,jjlx,jjzfe
000001,华夏成长混合,1.1670,3.7400,1.173,-0.51,-0.006,开放,2026-01-30,郑晓辉等,混合型-灵活,29.37亿元
```

**特性：**
- ✅ **边爬边写**：每获取一个基金，立即写入文件，不怕中断
- ✅ **断点续传**：中断后可以从上次停止的地方继续
- ✅ **详细日志**：实时显示进度、成功/失败状态、文件路径
- ✅ **完整路径**：自动显示输出文件的绝对路径

---

### 方式三：MCP Server（供 AI 助手使用）

**适合场景：** 通过 AI 助手（Copilot、Claude）调用

#### 1. 克隆项目
```bash
git clone git@github.com:Selene1225/Skills.git
cd Skills/fund_scraper_mcp
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

**注意：** 本项目使用系统已安装的 Microsoft Edge 浏览器，**无需**运行 `playwright install`。

#### 3. 配置 MCP 客户端

##### VS Code + GitHub Copilot

在项目根目录创建 `.vscode/mcp.json`：

```json
{
  "mcpServers": {
    "fund-scraper": {
      "command": "python",
      "args": ["C:/path/to/fund_scraper_mcp/server.py"],
      "env": {
        "HEADLESS": "true"
      }
    }
  }
}
```

重启 VS Code 后，Copilot 就能调用这些工具了。

##### Claude Desktop

编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "fund-scraper": {
      "command": "python",
      "args": ["C:/path/to/fund_scraper_mcp/server.py"],
      "env": {
        "HEADLESS": "true"
      }
    }
  }
}
```

#### 4. 使用示例

配置好 MCP 后，你可以在 AI 助手中这样使用：

**一键获取所有基金数据（推荐）：**
```
请用 fetch_all_funds_info 拉取所有基金数据，保存为 CSV 文件
```

**先测试（只获取前100个）：**
```
请用 fetch_all_funds_info 获取前100个基金的数据，参数：max_funds=100
```

**其他示例：**
```
请帮我获取所有基金的代码列表
```

```
请获取基金 000001 的详细信息
```

```
请获取基金 110022 最近30天的净值历史
```

```
请批量获取这些基金的详情：000001, 110022, 161005
```

---

## 📊 数据格式说明

### 字段说明（12个字段，与新浪数据格式兼容）

| 字段 | 说明 | 示例 |
|------|------|------|
| `symbol` | 基金代码 | `000001` |
| `sname` | 基金名称 | `华夏成长混合` |
| `per_nav` | 单位净值 | `1.1670` |
| `total_nav` | 累计净值 | `3.7400` |
| `yesterday_nav` | 前一日净值（计算得出） | `1.173` |
| `nav_rate` | 增长率 | `-0.51` |
| `nav_a` | 涨跌额（计算得出） | `-0.006` |
| `sg_states` | 申购状态 | `开放` |
| `nav_date` | 净值日期 | `2026-01-30` |
| `fund_manager` | 基金经理 | `郑晓辉等` |
| `jjlx` | 基金类型 | `混合型-灵活` |
| `jjzfe` | 基金规模 | `29.37亿元` |

---

## 🏗️ 项目结构

```
fund_scraper_mcp/
├── server.py                      # MCP Server 主入口
├── browser_manager.py             # Microsoft Edge 浏览器管理
├── fetch_funds.py                 # 命令行工具（边爬边写、断点续传）
├── fund_scraper_gui.py           # 图形界面工具 ⭐ 新增
├── 启动基金数据获取工具.bat      # Windows 一键启动脚本 ⭐ 新增
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py            # 爬虫抽象基类
│   └── eastmoney_scraper.py       # 天天基金爬虫实现
├── utils/
│   ├── __init__.py
│   └── anti_detection.py          # 反检测策略（UA轮换、延迟等）
├── test_scraper.py                # 功能测试脚本
├── requirements.txt               # Python 依赖
└── README.md                      # 本文件
```

---

## ⚙️ 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `HEADLESS` | 是否无头模式运行浏览器 | `true` |

**调试模式：** 如果想看到浏览器运行过程，设置 `HEADLESS=false`：
```json
"env": {
  "HEADLESS": "false"
}
```

---

## 🤖 支持的 MCP 客户端

| 客户端 | 支持状态 |
|--------|---------|
| GitHub Copilot (VS Code) | ✅ 支持 |
| Claude Desktop | ✅ 支持 |
| Claude Code | ✅ 支持 |
| Cursor | ✅ 支持 |
| Continue | ✅ 支持 |
| 自定义 MCP Client | ✅ 支持 |
| **命令行直接使用** | ✅ **支持** |

---

## ⚠️ 注意事项

1. ⚠️ 本项目仅供学习研究使用，请遵守相关网站的使用条款
2. ⚠️ 请勿高频请求，建议批量获取时添加适当延迟（默认1秒）
3. ✅ 使用系统 Microsoft Edge 浏览器，无需安装额外浏览器（约节省 200MB 空间）
4. 💡 Windows 系统通常已预装 Edge，macOS/Linux 用户需要先安装 Edge
5. 💾 使用命令行工具时，数据会边爬边写入文件，即使中断也不会丢失已获取的数据
6. 🔄 支持断点续传，中断后可以从上次停止的地方继续

---

## 🎯 常见使用场景

### 场景1：新手用户 - 使用图形界面
```
1. 双击 "启动基金数据获取工具.bat"
2. 在界面中点击"浏览"选择保存位置
3. 点击"开始获取"
4. 等待程序自动完成（可以看到实时进度）
```

### 场景2：快速获取少量基金数据（命令行）
```bash
# 获取前50个基金，快速测试
python fetch_funds.py --max 50
```

### 场景3：获取所有基金数据（推荐工作流）
```bash
# 第一步：开始获取（可能需要数小时）
python fetch_funds.py --all --output all_funds_20260215.csv

# 如果中途需要暂停（Ctrl+C），稍后继续：
python fetch_funds.py --all --output all_funds_20260215.csv --resume

# 继续运行，直到完成所有26000+个基金
```

### 场景4：加快速度（风险：可能被反爬虫）
```bash
# 减少延迟到0.5秒，批次增大到200
python fetch_funds.py --all --output fast.csv --batch 200 --delay 0.5
```

### 场景5：通过 AI 助手获取数据
```
你：请用 fetch_all_funds_info 获取所有基金数据

AI：正在获取约26000个基金的完整信息...
    [自动调用 MCP 工具]
    已获取 26163 个基金，保存为 funds_20260215.csv
```

---

## 📦 依赖说明

**Python 版本要求：**
- **最低版本**: Python 3.8
- **推荐版本**: Python 3.10 或 3.11
- **兼容版本**: Python 3.8, 3.9, 3.10, 3.11, 3.12

**Python 包依赖：**
```
mcp>=1.0.0              # MCP 协议支持
playwright>=1.40.0      # 浏览器自动化
aiohttp>=3.9.0         # 异步 HTTP 请求
```

**安装命令：**
```bash
pip install -r requirements.txt
```

**为什么选择这些版本？**
- **Python 3.8+**: `asyncio` 和类型提示的稳定支持
- **Python 3.10/3.11**: 性能更好，推荐使用
- **Playwright 1.40+**: 稳定的 Edge 浏览器支持
- **MCP 1.0+**: 最新的 MCP 协议标准

---

## 📄 License

MIT

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 到 [https://github.com/Selene1225/Skills](https://github.com/Selene1225/Skills)！

本 Skill 是 Skills 仓库的一部分，包含多个 MCP Server 实现。

---

## 🔗 相关链接

- **GitHub 仓库**: [https://github.com/Selene1225/Skills](https://github.com/Selene1225/Skills)
- **MCP 协议**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
- **数据来源**: [天天基金网](https://fund.eastmoney.com)
