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


    def process_item(self, item, spider):
        data = dict(item)

        # 列车时刻表
        if isinstance(item,TrainCodeItem):
            db_ret = self.train_code_list.find_one({'TrainCode': item['TrainCode']})
            # print("---------------------------------")
            # print("db_ret:"+str(db_ret))
            # print({'TrainCode':item['TrainCode']})
            # print("---------------------------------")
            if db_ret is None:
                self.train_code_list.insert(data)
        # 列车详细信息
        elif isinstance(item,TrainDetailItem):
            db_ret = self.train_code_detail.find_one({'TrainCode': item['TrainCode']})
            if db_ret is None:
                self.train_code_detail.insert(data)

        return item





