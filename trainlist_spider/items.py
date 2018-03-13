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

# 车次途径站信息 V2
class TrainDetailItem(scrapy.Item):
    TrainNo = scrapy.Field()
    TrainCode = scrapy.Field()
    QueryDate =scrapy.Field()
    start_station_name = scrapy.Field()
    arrive_time = scrapy.Field()
    station_train_code = scrapy.Field()
    station_name = scrapy.Field()
    train_class_name = scrapy.Field()
    service_type = scrapy.Field()
    start_time = scrapy.Field()
    stopover_time = scrapy.Field()
    end_station_name = scrapy.Field()
    station_no = scrapy.Field()
    isEnabled = scrapy.Field()
