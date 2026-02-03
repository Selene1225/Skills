from __future__ import print_function
import sys
from datetime import *
import time
import json
import random
import traceback
import requests
# -*- coding: UTF-8 -*-
 
class FundsData:
    """
    基金数据获取类
    数据来源：天天基金网（东方财富）
    优点：稳定可靠，无反爬限制，字段完整
    """
    
    # 基础配置
    data_path = ".\\"  # 数据输出路径，默认当前目录
    data_limit = 500   # 每页获取数量
    linePerPageMap = [500, 500, 500, 500, 500, 500, 500]
    linePerPageIndex = 0
    lineSum = 0
 
    # URL配置 - 使用天天基金网接口
    urlMap = {
        1: {
            'name': '基金',
            'url': "http://fund.eastmoney.com/data/rankhandler.aspx",
            'fileTitle': u'基金代码,基金名称,单位净值,累计净值,前一日净值,增长率,涨跌额,申购状态,净值日期,基金经理,基金类型,基金zfe',
            'dataKey': ['symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav', 'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager', 'jjlx', 'jjzfe']
        },
    }
 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh-HK;q=0.9,zh;q=0.8,en;q=0.7",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Referer": "http://fund.eastmoney.com/",
    }
 
    def demo(self):
        print("1-下载文件: " + self.urlMap[1]['name'])
        self.getData(self.urlMap[1])
 
    def putFileTitle(self, file_obj, title):
        output = title + "\n"
        file_obj.write(output)
 
    def invoke(self, url, param):
        """调用天天基金网接口"""
        try:
            response = requests.get(url, params=param, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return False
            
            dataStr = response.text
            if len(dataStr) < 10:
                return False
            else:
                return dataStr
        except Exception as e:
            print(f"请求失败: {e}")
            return False
 
    def getValue(self, key, values):
        """获取字段值"""
        if key not in values:
            return ''
        value = values[key]
        if value is None:
            return ''
        return str(value)
 
    def outPutJsonData(self, data):
        """解析天天基金网返回的数据"""
        try:
            # 天天基金网返回格式: var rankData = {datas:["...", "..."]}
            if 'var rankData' not in data:
                return None
            
            # 提取JSON数据
            start = data.find('[')
            end = data.rfind(']') + 1
            if start == -1 or end <= start:
                return None
            
            data_str = data[start:end]
            data_list = json.loads(data_str)
            
            # 转换为需要的格式
            result = {
                'total_num': len(data_list),  # 这里只能获取当前页的数量
                'data': []
            }
            
            for item in data_list:
                parts = item.split(',')
                if len(parts) >= 8:
                    fund_info = {
                        'symbol': parts[0] if len(parts) > 0 else '',
                        'sname': parts[1] if len(parts) > 1 else '',
                        'per_nav': parts[4] if len(parts) > 4 else '',  # 单位净值
                        'total_nav': parts[5] if len(parts) > 5 else '',  # 累计净值
                        'yesterday_nav': '',  # 天天基金排行榜接口没有此字段
                        'nav_rate': parts[6] if len(parts) > 6 else '',  # 日增长率
                        'nav_a': '',  # 涨跌额，需要计算
                        'sg_states': parts[23] if len(parts) > 23 else '开放申购',  # 申购状态
                        'nav_date': parts[3] if len(parts) > 3 else '',  # 净值日期
                        'fund_manager': parts[27] if len(parts) > 27 else '',  # 基金经理
                        'jjlx': '',  # 基金类型，排行榜接口没有
                        'jjzfe': parts[26] if len(parts) > 26 else ''  # 资产规模
                    }
                    result['data'].append(fund_info)
            
            return result
        except Exception as e:
            print(f"解析数据失败: {e}")
            traceback.print_exc()
            return None
 
    def outPutData(self, file_obj, datakey, data):
        """输出数据到文件"""
        tmpall = self.outPutJsonData(data)
        if tmpall is None or "data" not in tmpall:
            print("没找到数据")
            return 0
 
        tmp = tmpall['data']
        if tmp is None or len(tmp) == 0:
            return 0
            
        for item1 in tmp:
            data_str = ''
            for key in datakey:
                data_str += str(self.getValue(key, item1)) + ","
            if len(data_str) > 0:
                data_str = data_str[:-1]
            output = data_str + "\n"
            file_obj.write(output)
        return len(tmp)
 
    def getData(self, urlMap):
        """获取所有基金数据"""
        # 先获取总数量（天天基金网需要特殊处理）
        total_num = self.GetTotalNum(urlMap)
        if total_num == 0:
            print("无法获取数据总数，将持续获取直到没有数据")
            total_num = 999999  # 设置一个大数
 
        print("总数量为" + str(total_num))
        time_str = date.today()
        filename = self.data_path + urlMap['name'] + '-' + str(time_str) + '.csv'
        print("开始下载数据，输出到 " + filename)
        
        file_obj = open(filename, 'w', encoding='utf-8-sig')
        self.putFileTitle(file_obj, urlMap['fileTitle'])
        
        url = urlMap['url']
        self.lineSum = 0
        self.linePerPageIndex = 0
        downloaded = 0
        
        while downloaded < total_num:
            # 构造请求参数
            page_num = self.linePerPageMap[self.linePerPageIndex]
            self.linePerPageIndex += 1
            if self.linePerPageIndex > 6:
                self.linePerPageIndex = 0
            
            page_index = (self.lineSum // page_num) + 1
            
            param = {
                'op': 'ph',
                'dt': 'kf',
                'ft': 'all',
                'rs': '',
                'gs': '0',
                'sc': 'qjzf',
                'st': 'desc',
                'sd': '2024-01-01',
                'ed': '2026-01-31',
                'qdii': '',
                'tabSubtype': ',,,,,',
                'pi': str(page_index),
                'pn': str(page_num),
                'dx': '1'
            }
            
            data = self.invoke(url, param)
            if data == False:
                print("下载完成或网络错误")
                break
                
            lineNum = self.outPutData(file_obj, urlMap['dataKey'], data)
            if lineNum == 0:
                print("没有更多数据，下载完成")
                break
                
            downloaded += lineNum
            self.lineSum += page_num
            
            print("本次期望下载" + str(page_num) + "行，实际下载" + str(lineNum) + "行，共下载" + str(downloaded) + "行")
            
            # 随机延迟，避免请求过快
            sleepTime = random.randint(1, 3)
            time.sleep(sleepTime)
        
        file_obj.close()
        print("所有数据下载完成")
 
    def GetTotalNum(self, urlMap):
        """获取基金总数量"""
        try:
            print("获取基金总数量...")
            url = urlMap['url']
            
            # 天天基金网接口参数
            param = {
                'op': 'ph',
                'dt': 'kf',
                'ft': 'all',
                'rs': '',
                'gs': '0',
                'sc': 'qjzf',
                'st': 'desc',
                'sd': '2024-01-01',
                'ed': '2026-01-31',
                'qdii': '',
                'tabSubtype': ',,,,,',
                'pi': '1',
                'pn': '20',
                'dx': '1'
            }
            
            data = self.invoke(url, param)
            if data == False:
                print("无法正常调用接口")
                return 0
                
            # 天天基金网的接口需要特殊处理来获取总数
            # 由于接口不返回总数，我们使用一个较大的数字，让程序自动停止
            # 或者我们可以从基金列表接口获取总数
            
            # 尝试从基金列表获取总数
            list_url = "http://fund.eastmoney.com/js/fundcode_search.js"
            try:
                r = requests.get(list_url, headers=self.headers, timeout=10)
                if r.status_code == 200:
                    text = r.text.replace('var r = ', '').replace(';', '')
                    funds = json.loads(text)
                    total = len(funds)
                    print(f"从基金列表接口获取到总数: {total}")
                    return total
            except:
                pass
            
            # 如果获取不到总数，返回0，让主程序持续获取
            return 0
            
        except Exception as e:
            print(u"获取基金总数量失败")
            exstr = traceback.format_exc()
            print(exstr)
            return 0
 
try:
    pro = FundsData()
    pro.demo()
except Exception as e:
    print(u"有问题!")
    exstr = traceback.format_exc()
    print(exstr)
