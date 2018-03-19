# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.conf import settings
from trainlist_spider.items import *
import pymongo



# 车次列表
class TrainCodeListPipline(object):

    def __init__(self):

        # 初始化数据库
        host = settings["MONGODB_HOST"]
        port = settings["MONGODB_PORT"]
        dbname = settings["MONGODB_DBNAME"]

        client = pymongo.MongoClient(host=host,port=port)
        # 选择数据库
        mdb = client[dbname]
        # 选择表（集合）
        self.train_code_list = mdb["train_code_list"]
        self.train_code_detail = mdb["train_code_detail"]
        self.train_code_detail_v2 = mdb["train_code_detail_v2"]
        self.count = 0

    def process_item(self, item, spider):
        data = dict(item)


        # 列车时刻表
        if isinstance(item,TrainCodeItem):
            db_ret = self.train_code_list.find_one({'TrainCode': item['TrainCode'], 'QueryDate': item['QueryDate']})
            # print("---------------------------------")
            # print("db_ret:"+str(db_ret))
            # print({'TrainCode':item['TrainCode']})
            # print("---------------------------------")
            if db_ret is None:
                self.train_code_list.insert(data)
        # 列车详细信息
        elif isinstance(item,TrainDetailItem):
            self.count +=1
            # print("item:"+str(self.count))
            db_ret = self.train_code_detail.find_one({'TrainCode': item['TrainCode'], 'QueryDate': item['QueryDate']})
            if db_ret is None:
                self.train_code_detail.insert(data)
            # else:
                # print(db_ret)
        # 列车途径站 升级版 v2
        elif isinstance(item,TrainDetailItem_v2):
            db_ret = self.train_code_detail_v2.find_one({'TrainCode': item['TrainCode'], 'QueryDate': item['QueryDate'], 'station_no': item['station_no']})
            if db_ret is None:
                self.train_code_detail_v2.insert(data)

        return item





