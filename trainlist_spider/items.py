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
    StartDate = scrapy.Field()

# 车次途径站信息
class TrainDetailItem(scrapy.Item):
    TrainNo = scrapy.Field()
    TrainCode = scrapy.Field()
    Info = scrapy.Field()
    QueryDate =scrapy.Field()


# # 车次途径站信息 V2.1
class TrainDetailInfo(scrapy.Item):

    # 列车信息
    start_station_name = scrapy.Field()  # p
    end_station_name = scrapy.Field()  # p

    # 始发站信息
    train_class_name = scrapy.Field()  # 0
    service_type = scrapy.Field()  # 0

    # 发车日期
    start_date = scrapy.Field() # m
    # 到站时间
    arrive_time = scrapy.Field() #m

    # 到站车次
    arrive_train_code = scrapy.Field()#m
    # 出发车次
    depart_train_code = scrapy.Field()#m
    # 当前站名
    station_name = scrapy.Field()#m
    # 发车时间
    start_time = scrapy.Field() #m
    # 停留时间
    stopover_time = scrapy.Field() #m

    # 站续
    station_no = scrapy.Field() # m
    isEnabled = scrapy.Field() # m


# 车次途径站信息 V2.1
class TrainDetailDetail_V2_1(scrapy.Item):
    TrainNo = scrapy.Field()
    TrainCode = scrapy.Field()
    QueryDate = scrapy.Field()
    start_date = scrapy.Field()
    start_station_name = scrapy.Field()
    arrive_time = scrapy.Field()
    # station_train_code = scrapy.Field()
    # 到底车次
    arrive_train_code = scrapy.Field()
    # 出发车次
    depart_train_code = scrapy.Field()

    station_name = scrapy.Field()
    train_class_name = scrapy.Field()
    service_type = scrapy.Field()
    start_time = scrapy.Field()
    stopover_time = scrapy.Field()
    end_station_name = scrapy.Field()
    station_no = scrapy.Field()
    isEnabled = scrapy.Field()

# 车次途径站信息 V2
class TrainDetailItem_v2(scrapy.Item):
    TrainNo = scrapy.Field()
    TrainCode = scrapy.Field()
    QueryDate =scrapy.Field()
    start_date =scrapy.Field()
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
