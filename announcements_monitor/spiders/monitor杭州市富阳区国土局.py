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
import traceback
import bs4
import scrapy
import announcements_monitor.items
import re
import datetime
import pandas as pd

with open(os.getcwd() + r'\announcements_monitor\spiders\needed_data.txt', 'r') as f:
    s = f.read()
    needed_data = s.split(',')
needed_data = [s.encode('utf8') for s in needed_data]

sys.path.append(sys.prefix + "\\Lib\\MyWheels")
sys.path.append(os.getcwd()) #########
reload(sys)
sys.setdefaultencoding('utf8')
import spider_log  ########
import spider_func
spider_func = spider_func.spider_func()
log_obj = spider_log.spider_log() #########

re_table = {
    u'地块编号':'parcel_no',
    u'宗地编号':'parcel_no',
    u'地块坐落':'parcel_location',
    u'地块位置':'parcel_location',
    u'土地用途':'purpose',
    u'出让面积':'offer_area_m2',
    u'容积率':'plot_ratio',
    u'起始价':'starting_price_sum',
    u'起价':'starting_price_sum',
    u'建筑面积':'building_area',
    u'竞得单位':'competitive_person',
    u'成交价':'transaction_price_sum'
}

class Spider(scrapy.Spider):
    name = "511695"
    allowed_domains = ["www.fuyang.gov.cn"]

    def start_requests(self):
        urls1 = ["http://www.fuyang.gov.cn/fy/gtj/crxx/index_%s.jhtml" % i for i in xrange(2) if i > 0]
        urls2 = ["http://www.fuyang.gov.cn/fy/gtj/cjxx/index_%s.jhtml" % i for i in xrange(2) if i > 0]

        for url in urls1+urls2:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        try:
            #log_obj.debug(u"准备分析内容：%s" %response.url)
            sel = scrapy.Selector(response)
            items = []
            root_path = '/html/body/div[6]/div[2]/div/div[2]/div/ul/li'
            sites = sel.xpath(root_path)  # [@id="list"]
            if not sites:
                sites = sel.xpath(root_path.replace("/tbody",""))

            for site in sites:
                item = announcements_monitor.items.AnnouncementsMonitorItem()
                item['monitor_city'] = '杭州富阳'

                item['monitor_id'] = self.name
                item['monitor_title'] = site.xpath('a/text()').extract_first()
                item['monitor_date'] = site.xpath('span/text()').extract_first()
                item['monitor_url'] = site.xpath('a/@href').extract_first()

                if re.search(r'.*出让公告|.*拍卖公告|.*挂牌公告', item['monitor_title'].encode('utf8')):
                    item['parcel_status'] = 'onsell'
                    yield scrapy.Request(url=item['monitor_url'], meta={'item': item}, callback=self.parse1,
                                         dont_filter=False)
                elif re.search(r'.*使用权结果公示.*', item['monitor_title'].encode('utf8')):
                    item['parcel_status'] = 'sold'
                    yield scrapy.Request(item['monitor_url'], meta={'item': item}, callback=self.parse1,
                                         dont_filter=False)
                else:
                    yield item
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