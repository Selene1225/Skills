"""
使用 akshare 获取基金数据（推荐方案）

✅ 优点:
1. 完全免费，无需API Key
2. 数据稳定，无反爬限制
3. 接口简单，易于使用
4. 数据来源可靠（东方财富等公开数据）
5. 支持19,000+只基金

安装: pip install akshare
文档: https://akshare.akfamily.xyz/
"""

import akshare as ak
import pandas as pd
from datetime import datetime


def get_all_funds(symbol="全部"):
    """
    获取开放式基金排行数据
    
    参数:
        symbol: 基金类型
            - "全部" (默认)
            - "股票型"
            - "混合型"
            - "债券型"
            - "指数型"
            - "QDII"
            - "LOF"
            - "FOF"
    
    返回:
        DataFrame包含: 基金代码、基金简称、单位净值、累计净值、
                      日增长率、近1周、近1月、近3月、近6月、近1年等
    """
    try:
        df = ak.fund_open_fund_rank_em(symbol=symbol)
        print(f"✅ 成功获取 {len(df)} 只{symbol}基金数据")
        return df
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        return None


def get_top_performers(df, metric='近1月', top_n=20):
    """
    获取表现最好的基金
    
    参数:
        df: 基金数据DataFrame
        metric: 排序指标（日增长率、近1周、近1月、近3月、近6月、近1年、今年来、成立来）
        top_n: 返回前N个
    
    返回:
        排序后的DataFrame
    """
    if df is None or len(df) == 0:
        return None
    
    # 确保是数值类型
    df[metric] = pd.to_numeric(df[metric], errors='coerce')
    
    # 按指标降序排序
    top_funds = df.nlargest(top_n, metric)
    return top_funds


def save_to_csv(df, filename):
    """保存数据到CSV文件"""
    if df is not None and len(df) > 0:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 数据已保存到: {filename}")
        return True
    return False


def analyze_fund_data(df):
    """分析基金数据"""
    if df is None or len(df) == 0:
        return
    
    print("\n" + "="*80)
    print("基金数据分析")
    print("="*80)
    
    # 转换为数值类型
    numeric_cols = ['单位净值', '日增长率', '近1周', '近1月', '近3月', '近6月', '近1年', '今年来', '成立来']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print(f"\n基金总数: {len(df)}")
    print(f"数据日期: {df['日期'].iloc[0] if '日期' in df.columns else 'N/A'}")
    
    # 统计信息
    if '近1月' in df.columns:
        print(f"\n近1月收益率统计:")
        print(f"  平均值: {df['近1月'].mean():.2f}%")
        print(f"  中位数: {df['近1月'].median():.2f}%")
        print(f"  最大值: {df['近1月'].max():.2f}%")
        print(f"  最小值: {df['近1月'].min():.2f}%")
        print(f"  正收益基金: {(df['近1月'] > 0).sum()} 只 ({(df['近1月'] > 0).sum() / len(df) * 100:.1f}%)")
    
    # 今年来收益率统计
    if '今年来' in df.columns:
        print(f"\n今年来收益率统计:")
        print(f"  平均值: {df['今年来'].mean():.2f}%")
        print(f"  最大值: {df['今年来'].max():.2f}%")
        print(f"  最小值: {df['今年来'].min():.2f}%")


if __name__ == "__main__":
    print("="*80)
    print("akshare 基金数据获取示例")
    print("="*80)
    
    # 1. 获取所有基金
    print("\n【任务1】获取所有开放式基金数据")
    all_funds = get_all_funds(symbol="全部")
    
    if all_funds is not None:
        # 保存全部数据
        save_to_csv(all_funds, 'akshare_all_funds.csv')
        
        # 数据分析
        analyze_fund_data(all_funds)
        
        # 2. 获取近1月表现最好的基金
        print("\n" + "="*80)
        print("【任务2】近1月收益率Top 20基金")
        print("="*80)
        top_1m = get_top_performers(all_funds, metric='近1月', top_n=20)
        if top_1m is not None:
            print("\n近1月收益率Top 20:")
            for i, row in enumerate(top_1m.iterrows(), 1):
                fund = row[1]
                print(f"{i:2d}. {fund['基金代码']:6s} {fund['基金简称']:30s} "
                      f"近1月: {fund['近1月']:>7.2f}% 今年来: {fund['今年来']:>7.2f}%")
            
            save_to_csv(top_1m, 'akshare_top_funds_1month.csv')
        
        # 3. 获取今年来表现最好的基金
        print("\n" + "="*80)
        print("【任务3】今年来收益率Top 20基金")
        print("="*80)
        top_ytd = get_top_performers(all_funds, metric='今年来', top_n=20)
        if top_ytd is not None:
            print("\n今年来收益率Top 20:")
            for i, row in enumerate(top_ytd.iterrows(), 1):
                fund = row[1]
                print(f"{i:2d}. {fund['基金代码']:6s} {fund['基金简称']:30s} "
                      f"今年来: {fund['今年来']:>7.2f}% 成立来: {fund['成立来']:>7.2f}%")
            
            save_to_csv(top_ytd, 'akshare_top_funds_ytd.csv')
    
    # 4. 分类获取不同类型基金
    print("\n" + "="*80)
    print("【任务4】分类获取不同类型基金")
    print("="*80)
    
    fund_types = {
        "股票型": "akshare_stock_funds.csv",
        "混合型": "akshare_hybrid_funds.csv",
        "债券型": "akshare_bond_funds.csv",
        "指数型": "akshare_index_funds.csv"
    }
    
    for fund_type, filename in fund_types.items():
        print(f"\n获取{fund_type}基金...")
        df = get_all_funds(symbol=fund_type)
        if df is not None:
            save_to_csv(df, filename)
            
            # 显示该类型收益最高的前5个
            top_5 = get_top_performers(df, metric='近1月', top_n=5)
            if top_5 is not None:
                print(f"  近1月收益Top 5:")
                for i, row in enumerate(top_5.iterrows(), 1):
                    fund = row[1]
                    print(f"    {i}. {fund['基金简称']:25s} 近1月: {fund['近1月']:>6.2f}%")
    
    print("\n" + "="*80)
    print("✅ 所有任务完成!")
    print("="*80)
    print("\n生成的文件:")
    print("  - akshare_all_funds.csv (所有基金)")
    print("  - akshare_top_funds_1month.csv (近1月Top 20)")
    print("  - akshare_top_funds_ytd.csv (今年来Top 20)")
    print("  - akshare_stock_funds.csv (股票型)")
    print("  - akshare_hybrid_funds.csv (混合型)")
    print("  - akshare_bond_funds.csv (债券型)")
    print("  - akshare_index_funds.csv (指数型)")
