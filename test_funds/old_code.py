from __future__ import print_function
import io
import sys
from builtins import Exception
from datetime import *
import time
import urllib.parse
import urllib.request
import json
import re
import codecs
import random
import traceback
# -*- coding: UTF-8 -*-
 
class FundsData:
    DOMAIN = 'http://vip.stock.finance.sina.com.cn/'
    page_start = 1
    # data_path = "E:\\0-MINE\\Dady-Stock\\"
    data_path = "E:\\数据\\"
# 替代下面urlMap.param.num数值
    data_limit = 500
    # 不能随便改，不然会出现数据重复
    linePerPageMap = [500, 500, 500, 500, 500, 500, 500]
    linePerPageIndex = 0
    lineSum = 0
 
    data_prefix = r'^.*\s.*\({"total_num"'
    data_surfix = r"\);$"
 
    urlMap = {
        1: {
            'name' : '基金',
            'url' : "fund_center/data/jsonp.php/IO.XSRV2.CallbackList['6XxbX6h4CED0ATvW']/NetValue_Service.getNetValueOpen",
            'param' : {
                'sort' : 'symbol',
                'num' : 100,
                'asc' : 1,
                'type2' : 0
            },
            'fileTitle' : u'基金代码,基金名称,单位净值,累计净值,前一日净值,增长率,涨跌额,申购状态,净值日期,基金经理,基金类型,基金zfe',
            'dataKey' : ['symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav', 'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager', 'jjlx', 'jjzfe']
        },
    }
 
    operationMap = {
        'turnover' : 100,
        'r0_net' : 10000,
        'amount' : 10000,
        'r0_out' : 10000,
        'r0_in' : 10000,
        'outamount' : 10000,
        'inamount' : 10000,
        'netamount' : 10000
    }
 
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36",
        "Accept-Language":"zh-CN,zh-HK;q=0.9,zh;q=0.8,en;q=0.7",
        "Accept-Encoding":"gzip, deflate",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Connection":"keep-alive",
        "Host":"vip.stock.finance.sina.com.cn",
        "Cache-Control":"max-age=0",
    }
 
    def demo(self):
        print("1-下载文件: " + self.urlMap[1]['name'])
        self.getData(self.urlMap[1])
 
    def putFileTitle(self, file_obj, title):
        output = title + "\n"
        file_obj.write(output)
 
    def invoke(self, url, param):
        tmp = urllib.parse.urlencode(param)
        url = self.DOMAIN + url + '?' + tmp
        try:
            data = urllib.request.urlopen(url)
            dataStr = data.read()
            if len(dataStr) < 10:
                return False
            else:
                return dataStr
        except Exception as e:
            return False
 
    def getValue(self, key, values):
        value = values[key]
        if key in self.operationMap:
            val = float(value) / self.operationMap[key]
            ret = str(val)
        else:
            ret = value
        return ret
 
    def outPutJsonData(self, data):
        tmp1 = re.sub(r'(\w+):', '"\g<1>":', data.decode('GBK'))
        tmp2 = re.sub(self.data_prefix, '{"total_num"', tmp1)
        tmp1 = re.sub(self.data_surfix, '', tmp2)
        tmp = json.loads(tmp1)
        return tmp
 
    def outPutData(self, file_obj, datakey, data):
        tmpall = self.outPutJsonData(data)
        if "data" not in tmpall:
            print("没找到数据")
            return 0
 
        tmp = tmpall['data']
        if tmp is None:
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
        total_num = self.GetTotalNum(urlMap)
        if total_num == 0:
            return
 
        print("总数量为" + str(total_num))
        time_str = date.today()
        filename = self.data_path + urlMap['name'] + '-' + str(time_str) + '.csv'
        print("开始下载数据，输出到 " + filename)
        file_obj = open(filename, 'w', encoding='utf-8-sig')
        self.putFileTitle(file_obj, urlMap['fileTitle'])
        url = urlMap['url']
        param = urlMap['param']
        self.lineSum = 0
        self.linePerPageIndex = 0
        while True:
            param = self.fillParamPageInfo(param)
            data = self.invoke(url, param)
            if data == False:
                print("下载完成")
                break
            lineNum = self.outPutData(file_obj, urlMap['dataKey'], data)
            if lineNum == 0:
                break
            curentLine = self.lineSum - param['num'] + lineNum
            print("本次期望下载" + str(param['num']) + "行，实际下载" + str(lineNum) + "行，共下载" + str(curentLine) + "行")
            sleepTime = random.randint(3,6);
            time.sleep(sleepTime)
        file_obj.close()
        print("所有数据下载完成")
 
    def GetTotalNum(self, urlMap):
        try:
            print("获取基金总数量...")
            url = urlMap['url']
            param = urlMap['param']
            data = self.invoke(url, param)
            if data == False:
                print("无法正常调用接口")
                return 0
            tmp = self.outPutJsonData(data)
            if 'total_num' not in tmp:
                print("没找到总数量")
                return
            return tmp['total_num']
        except Exception as e:
            print(u"获取基金总数量失败")
            exstr = traceback.format_exc()
            print(exstr)
            return 0
 
 
    def fillParamPageInfo(self, param):
        param['num'] = self.linePerPageMap[self.linePerPageIndex]
        self.linePerPageIndex += 1
        if self.linePerPageIndex > 6:
            self.linePerPageIndex = 0
        param['page'] = self.lineSum // param['num'] + 1
        self.lineSum += param['num']
        return param
 
    def test(self):
        file_obj = open("D:\\test.csv", 'w', encoding='utf-8-sig')
        file_obj.write(u"测试中文")
        file_obj.close()
 
try:
    pro = FundsData()
    pro.demo()
except Exception as e:
    print(u"有问题!")
    exstr = traceback.format_exc()
    print(exstr)
 
input("按 回车 结束")
# 1. 到 windows-software-center安装python3.9
# 2. C:\Users\yiliu4\AppData\Local\Programs\Python\Python37-32\Scripts 目录下，pip.exe install pyinstaller
# 3. 脚本拷贝到 C:\Users\yiliu4\AppData\Local\Programs\Python\Python37-32\Scripts
# 4. C:\Users\yiliu4\AppData\Local\Programs\Python\Python37-32\Scripts\ 下执行 pyinstaller -F xxx.py