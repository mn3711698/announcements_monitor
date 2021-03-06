# -*- coding:utf-8 -*-  
"""
--------------------------------
    @Author: Dyson
    @Contact: Weaver1990@163.com
    @file: proxy_spider.py
    @time: 2017/3/9 16:27
--------------------------------
"""
import sys
import os

import numpy as np
import pandas as pd
import scrapy
import announcements_monitor.items
import re
import traceback
import datetime
import bs4
import json

log_path = r'%s/log/spider_DEBUG(%s).log' %(os.getcwd(),datetime.datetime.date(datetime.datetime.today()))

sys.path.append(sys.prefix + "\\Lib\\MyWheels")
sys.path.append(os.getcwd()) #########
reload(sys)
sys.setdefaultencoding('utf8')
import spider_log  ########
import spider_func
spider_func = spider_func.spider_func()
log_obj = spider_log.spider_log() #########

with open(os.getcwd() + r'\announcements_monitor\spiders\needed_data.txt', 'r') as f:
    s = f.read()
    needed_data = s.split(',')
needed_data = [s.encode('utf8') for s in needed_data]

class Spider(scrapy.Spider):
    name = "511714"

    def start_requests(self):
        # 临安相应网址的index的系数，index_1代表第二页
        self.urls1 = ["http://www.linan.gov.cn/gtzyj/gsgg/tdzpgcrgg/index.html", ] + ["http://www.linan.gov.cn/gtzyj/gsgg/tdzpgcrgg/index_%s.html" %i for i in xrange(2) if i > 1]
        self.urls2 = ["http://www.linan.gov.cn/gtzyj/gsgg/tdcrcjgs/index.html", ] + ["http://www.linan.gov.cn/gtzyj/gsgg/tdcrcjgs/index_%s.html" %i for i in xrange(2) if i > 1]
        #self.urls3 = ["http://www.linan.gov.cn/gtzyj/gsgg/cjxx/index.html", ] + ["http://www.linan.gov.cn/gtzyj/gsgg/cjxx/index_%s.html" % i for i in xrange(2) if i > 1]
        for url in self.urls1 + self.urls2:# + self.urls3:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        try:
            bs_obj = bs4.BeautifulSoup(response.text, 'html.parser')
            """在使用chrome等浏览器自带的提取extract xpath路径的时候,
                导致明明在浏览器中提取正确, 却在程序中返回错误的结果"""
            e_table = bs_obj.find('div', class_='list_con')
            e_row = e_table.find_all('li')
            for e_li in e_row:
                item = announcements_monitor.items.AnnouncementsMonitorItem()
                item['monitor_city'] = '临安'
                item['monitor_id'] = self.name #/scxx/tdsc/tdcrgg/2016-11-17/6409.html
                item['monitor_title'] = e_li.find('span', class_='event').get_text(strip=True) # 标题
                item['monitor_date'] = e_li.find('span', class_='time').get_text(strip=True) # 成交日期

                if response.url in self.urls1:
                    item['parcel_status'] = 'onsell'
                    item['monitor_url'] = "http://www.linan.gov.cn/gtzyj/gsgg/tdzpgcrgg/" + re.sub(r'\.\/', '',e_li.a.get('href'))
                elif response.url in self.urls2:
                    item['parcel_status'] = 'sold'
                    item['monitor_url'] = "http://www.linan.gov.cn/gtzyj/gsgg/tdcrcjgs/" + re.sub(r'\.\/', '',e_li.a.get('href'))
                elif response.url in self.urls3:
                    item['parcel_status'] = 'update'
                    item['monitor_url'] = "http://www.linan.gov.cn/gtzyj/gsgg/cjxx/" + re.sub(r'\.\/', '',e_li.a.get('href'))

                yield scrapy.Request(item['monitor_url'], meta={'item': item}, callback=self.parse1, dont_filter=True)
        except:
            log_obj.update_error("%s中无法解析\n原因：%s" %(self.name, traceback.format_exc()))

    def parse1(self, response):
        bs_obj = bs4.BeautifulSoup(response.text, 'html.parser')
        item = response.meta['item']
        try:
            item['content_detail'],item['monitor_extra'] = spider_func.df_output(bs_obj,self.name,item['parcel_status'])
            yield item
        except:
            log_obj.error(item['monitor_url'], "%s（%s）中无法解析\n%s" % (self.name, response.url, traceback.format_exc()))
            yield response.meta['item']

if __name__ == '__main__':
    pass