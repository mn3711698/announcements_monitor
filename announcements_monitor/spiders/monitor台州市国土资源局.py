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
import PhantomJS_driver
import spider_func
spider_func = spider_func.spider_func()
PhantomJS_driver = PhantomJS_driver.PhantomJS_driver()

log_obj = spider_log.spider_log() #########

with open(os.getcwd() + r'\announcements_monitor\spiders\needed_data.txt', 'r') as f:
    s = f.read()
    needed_data = s.split(',')
needed_data = [s.encode('utf8') for s in needed_data]

title_type1 = ['parcel_no', 'parcel_location', '用地面积(㎡)', 'offer_area_m2', 'purpose',
               '地上建筑总面积(m2)', 'plot_ratio', '建筑密度', '建筑限高（m）', '绿地率',
               '出让年限(年)', 'starting_price_sum', '竞买保证金(万元)']
title_type2 = ['parcel_no', 'parcel_location', 'offer_area_m2', 'purpose',
               'plot_ratio', '出让年限', 'competitive_person', 'transaction_price_sum', '成交时间']

class Spider(scrapy.Spider):
    name = "511711"

    def start_requests(self):
        # 台州相应网址的index的系数，index_1代表第二页
        self.urls1 = ["http://www.zjtzgtj.gov.cn/col/col21069/index.html", ]
        self.urls2 = ["http://www.zjtzgtj.gov.cn/col/col21070/index.html", ]

        for url in self.urls1 + self.urls2:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        try:
            bs_obj = bs4.BeautifulSoup(PhantomJS_driver.get_html(response.url), 'html.parser')
            """在使用chrome等浏览器自带的提取extract xpath路径的时候,
                导致明明在浏览器中提取正确, 却在程序中返回错误的结果"""

            e_table = bs_obj.find('div', class_='default_pgContainer')
            e_row = e_table.find_all('li')
            for e_tr in e_row:
                item = announcements_monitor.items.AnnouncementsMonitorItem()
                item['monitor_city'] = '台州'

                item['monitor_id'] = self.name #/scxx/tdsc/tdcrgg/2016-11-17/6409.html
                item['monitor_title'] = e_tr.a.get_text(strip=True) # 标题
                item['monitor_date'] = e_tr.span.get_text(strip=True) # 成交日期 site.xpath('td[3]/text()').extract_first()
                item['monitor_url'] = "http://www.zjtzgtj.gov.cn" + e_tr.a.get('href')

                if re.search(ur'国有建设用地使用权挂牌出让公告', item['monitor_title']):
                    item['parcel_status'] = 'onsell'
                    yield scrapy.Request(item['monitor_url'],meta={'item':item},callback=self.parse1, dont_filter=True)
                elif re.search(ur'国有建设用地使用权出让结果公布', item['monitor_title']):
                    item['parcel_status'] = 'sold'
                    yield scrapy.Request(item['monitor_url'],meta={'item':item},callback=self.parse1, dont_filter=True)
                else:
                    yield item
        except:
            log_obj.update_error("%s中无法解析\n原因：%s\n%s" %(self.name, traceback.format_exc(),e_table))

    def parse1(self, response):
        bs_obj = bs4.BeautifulSoup(response.text, 'html.parser')
        item = response.meta['item']
        try:
            item['content_detail'], item['monitor_extra'] = spider_func.df_output(bs_obj.find('div', id='zoom'), self.name, item['parcel_status'])
            yield item
        except:
            log_obj.error(item['monitor_url'], "%s（%s）中无法解析\n%s" % (self.name, response.url, traceback.format_exc()))
            yield response.meta['item']

if __name__ == '__main__':
    pass