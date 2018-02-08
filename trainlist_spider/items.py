# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TrainlistSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

# 车次信息
class TrainCodeItem(scrapy.Item):
    TrainNo = scrapy.Field()
    TrainCode = scrapy.Field()
    StartStation = scrapy.Field()
    EndStation = scrapy.Field()
    StartTime = scrapy.Field()
    EndTime = scrapy.Field()
    TakeTime = scrapy.Field()
    QueryDate = scrapy.Field()
    Info = scrapy.Field()

# 车次途径站信息
class TrainDetailItem(scrapy.Item):
    TrainNo = scrapy.Field()
    TrainCode = scrapy.Field()
    Info = scrapy.Field()
    QueryDate =scrapy.Field()
