"""
使用 akshare 库获取基金数据

akshare 是专业的金融数据接口库，数据来源于东方财富等公开网站
官网: https://akshare.akfamily.xyz/
"""

import akshare as ak
import pandas as pd

print("="*80)
print("测试 akshare 获取基金数据")
print("="*80)

try:
    print("\n1. 获取开放式基金净值排行...")
    fund_open_df = ak.fund_open_fund_rank_em(symbol="全部")
    print(f"✅ 成功！共获取 {len(fund_open_df)} 条基金数据")
    print(f"\n数据列: {list(fund_open_df.columns)}")
    print(f"\n前10条数据:")
    print(fund_open_df.head(10)[['基金代码', '基金简称', '单位净值', '日增长率', '近1周', '近1月', '近3月', '近1年']])
    
    # 保存数据
    fund_open_df.to_csv('akshare_funds_all.csv', index=False, encoding='utf-8-sig')
    print(f"\n数据已保存到: akshare_funds_all.csv")
    
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("2. 获取单个基金的历史净值数据")
print("="*80)

try:
    # 获取华夏成长(000001)的历史净值
    fund_code = "000001"
    fund_history_df = ak.fund_open_fund_info_em(fund=fund_code, indicator="单位净值走势")
    print(f"✅ 成功！基金 {fund_code} 共有 {len(fund_history_df)} 条历史净值记录")
    print(f"\n最近5条记录:")
    print(fund_history_df.head())
    
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("3. 获取基金排行榜（按不同类型）")
print("="*80)

fund_types = ["股票型", "混合型", "债券型", "指数型", "QDII"]

for fund_type in fund_types[:3]:  # 只测试前3种
    try:
        print(f"\n获取{fund_type}基金...")
        df = ak.fund_open_fund_rank_em(symbol=fund_type)
        print(f"✅ {fund_type}: {len(df)} 只基金")
        if len(df) > 0:
            top_fund = df.iloc[0]
            print(f"   收益最高: {top_fund['基金简称']} ({top_fund['基金代码']}) - 日增长率: {top_fund['日增长率']}%")
    except Exception as e:
        print(f"❌ {fund_type} 失败: {e}")

print("\n" + "="*80)
print("✅ akshare 测试完成!")
print("="*80)
print("""
akshare 优势:
1. ⭐ 数据稳定，来源可靠（东方财富等公开数据）
2. ⭐ API简单，无需处理反爬问题
3. ⭐ 数据丰富，涵盖基金、股票、期货等
4. ⭐ 持续维护更新
5. ⭐ 完全免费开源

推荐使用场景:
- 数据分析和研究
- 量化投资策略开发
- 基金组合分析
- 历史数据回测

常用函数:
- ak.fund_open_fund_rank_em(symbol="全部")  # 基金排行
- ak.fund_open_fund_info_em(fund="000001", indicator="单位净值走势")  # 历史净值
- ak.fund_name_em()  # 所有基金列表
""")
