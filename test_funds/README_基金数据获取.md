# 基金数据获取方案总结

本项目提供了多种方式获取基金数据，您可以根据需求选择合适的方案。

## 方案对比

| 方案 | 数据源 | 数据量 | 稳定性 | 推荐度 |
|------|--------|--------|--------|--------|
| 新浪财经 | vip.stock.finance.sina.com.cn | 24,439+ 个开放式基金 | ⚠️ 有反爬限制 | ⭐⭐⭐ |
| 天天基金网 | fund.eastmoney.com | 股票型基金 | ✅ 稳定 | ⭐⭐⭐⭐⭐ |

## 1. 新浪财经方案 ⭐⭐⭐

### 数据来源
- **网址**: https://vip.stock.finance.sina.com.cn/fund_center/index.html#jzkfgpx
- **API**: `https://vip.stock.finance.sina.com.cn/fund_center/data/jsonp.php/IO.XSRV2.CallbackList/NetValueReturn_Service.NetValueReturnOpen`
- **数据量**: 24,439+ 个开放式基金

### 优点
- ✅ 数据量大，覆盖所有开放式基金
- ✅ 数据字段丰富（净值、收益率、基金经理、规模等）
- ✅ 支持多种排序方式
- ✅ 单次请求可获取40-100条数据

### 缺点
- ⚠️ 有反爬虫机制，短时间内多次请求会被限制（返回500错误）
- ⚠️ 被限制后需等待10-30分钟恢复
- ⚠️ 不适合批量获取全量数据

### 使用方式

#### 文件说明
- `test_sina_fund.py` - 测试脚本，验证接口可用性
- `get_sina_funds.py` - 完整版（包含批量获取和重试机制）
- `get_sina_simple.py` - 简化版（推荐使用）⭐

#### 示例代码

```python
from get_sina_simple import get_sina_fund_data_simple
import pandas as pd

# 获取今年以来收益最高的100个基金
funds = get_sina_fund_data_simple(page=1, page_size=100, sort='form_year', asc=0)

if funds:
    df = pd.DataFrame(funds)
    df.to_csv('top_funds.csv', index=False, encoding='utf-8-sig')
    print(f"成功获取 {len(funds)} 个基金")
```

#### 排序字段
- `form_year` - 今年以来收益率 ⭐推荐
- `form_start` - 成立以来收益率
- `one_year` - 近一年收益率
- `six_month` - 近半年收益率
- `three_month` - 近三月收益率
- `per_nav` - 单位净值

### 最佳实践
1. **单次请求策略**: 每次只请求1页，每页40-100条数据
2. **避免频繁请求**: 如果被限制（500错误），等待10-30分钟
3. **保存数据**: 获取数据后立即保存，避免重复请求
4. **多角度获取**: 通过不同排序方式获取不同视角的数据

## 2. 天天基金网方案 ⭐⭐⭐⭐⭐ （推荐）

### 数据来源
- **网址**: http://fund.eastmoney.com
- **API**: `http://fund.eastmoney.com/data/rankhandler.aspx`
- **数据量**: 股票型基金（数量较少但稳定）

### 优点
- ✅ 稳定性好，无明显反爬限制
- ✅ 支持分页，可批量获取
- ✅ 数据格式清晰
- ✅ 适合持续监控和定时抓取

### 缺点
- ⚠️ 只包含股票型基金（相比新浪的全部开放式基金）
- ⚠️ 数据字段相对较少

### 使用方式

#### 文件说明
- `test_sina_api.py` - 测试脚本（实际测试的是天天基金网接口）
- `get_tt_fund_data.py` - 天天基金网数据获取脚本

#### 示例代码

```python
from test_sina_api import get_fund_data
import time

all_funds = []
for page in range(1, 10):  # 获取前10页
    data = get_fund_data(page=page, page_size=20)
    if data:
        all_funds.extend(data)
        print(f"第{page}页获取成功，累计 {len(all_funds)} 条")
        time.sleep(0.5)  # 礼貌抓取
```

## 推荐方案

### 如果您需要:

1. **全量开放式基金数据（2万+）** → 使用新浪财经 + 单页大批量策略
   - 文件: `get_sina_simple.py`
   - 策略: 一次性获取100条，通过不同排序获取不同视角

2. **持续监控股票型基金** → 使用天天基金网
   - 文件: `test_sina_api.py` 或 `get_tt_fund_data.py`
   - 策略: 支持分页批量获取，可定时运行

3. **快速测试接口** → 使用测试脚本
   - 新浪: `test_sina_fund.py`
   - 天天: `test_sina_api.py`

## 数据字段说明

### 新浪财经字段
- `symbol` - 基金代码
- `name` - 基金名称
- `per_nav` - 单位净值
- `total_nav` - 累计净值
- `jzrq` - 净值日期
- `three_month` - 近三月收益率(%)
- `six_month` - 近半年收益率(%)
- `one_year` - 近一年收益率(%)
- `form_year` - 今年以来收益率(%)
- `form_start` - 成立以来收益率(%)
- `clrq` - 成立日期
- `jjjl` - 基金经理
- `zmjgm` - 资产规模(万元)
- `zjzfe` - 资金总份额

### 天天基金网字段
逗号分隔的字符串，包含：基金代码、名称、拼音、日期、净值、累计净值、各期增长率等

## 注意事项

1. **遵守网站规则**: 设置合理的请求间隔，避免对服务器造成压力
2. **数据仅供学习**: 请遵守数据使用规定，不要用于商业用途
3. **及时保存数据**: 获取后立即保存到本地，避免重复请求
4. **错误处理**: 做好异常处理，网络请求可能失败

## 依赖包

```bash
pip install requests pandas
```

或使用项目提供的 `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 测试新浪财经接口（等待10-30分钟避免被限制）
python test_sina_fund.py

# 3. 测试天天基金网接口（推荐）
python test_sina_api.py

# 4. 获取数据
python get_sina_simple.py  # 新浪财经
# 或
python get_tt_fund_data.py  # 天天基金网
```

## 常见问题

**Q: 新浪财经返回500错误？**
A: 这是因为短时间内请求过多被限制，请等待10-30分钟后重试。

**Q: 如何获取所有基金数据？**
A: 新浪有24,439个基金，但分页请求会被限制。建议:
   - 通过不同排序方式分批获取
   - 每次获取100条，间隔较长时间
   - 或使用代理IP轮换

**Q: 哪个数据源更稳定？**
A: 天天基金网更稳定，适合定时抓取；新浪数据更全但有限制。

**Q: 数据更新频率？**
A: 两个数据源都是每日更新，通常在交易日结束后更新当日净值。
