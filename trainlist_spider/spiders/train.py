# -*- coding: utf-8 -*-
import scrapy
import re
import datetime
import json
from trainlist_spider.items import TrainCodeItem
from trainlist_spider.items import TrainDetailItem
from scrapy.conf import settings
import logging


class TrainSpider(scrapy.Spider):
    name = 'train'
    allowed_domains = ['12306.cn']
    start_urls = ['https://12306.cn/',]


    # 请求 leftTicket/init
    def start_requests(self):
        yield scrapy.Request("https://kyfw.12306.cn/otn/leftTicket/init", callback=self.get_queryurl)





    # 获取 queryurl  &  请求train_list.js
    def get_queryurl(self,response):

        try:
            self.queryUrl = re.findall('var CLeftTicketUrl = \'leftTicket/(.*?)\';', response.body.decode('utf-8'),re.S)[0]
            self.log('获取queryurl成功 : '+self.queryUrl, logging.INFO)

            # 初始化查询时间
            querydata = 1
            if settings['QUERY_DATE']:
                querydata = int(settings['QUERY_DATE'])

            self.query_date = (datetime.datetime.now() + datetime.timedelta(days=querydata)).strftime("%Y-%m-%d")

            self.log("准备加载50M的站站组合信息，请耐心等待吧...", level=logging.INFO)
            yield scrapy.Request("https://kyfw.12306.cn/otn/resources/js/query/train_list.js",
                                 callback=self.get_ftstations)

        except BaseException:
            self.log('获取queryurl失败',logging.ERROR)
            return





    # 获取train_list.js & 请求station_name.js
    def get_ftstations(self,response):

        ret = response.body.decode('utf-8')
        if "train_list" not in ret:
            self.log("获取站站组合信息失败...",level=logging.INFO)
            self.log(response.request.url,level=logging.INFO)
            return
        # print('.................retry .................')
        # return
        txt = ret.replace("var", '')
        txt = txt.replace("train_list", '')
        txt = txt.replace("=", '')
        txt = txt.replace(" ", '')
        trian_list = json.loads(txt)
        self.train_list=set()
        for tm in trian_list.keys():
            for xh in trian_list[tm].keys():
                for train in trian_list[tm][xh]:
                    ret = train['station_train_code']
                    ret = re.findall('\(([\s\S]*)\)', ret)
                    self.train_list.add(ret[0])

        # print(len(self.train_list))
        # return
        self.log("站站组合信息加载完成，开始加载站段信息...",level=logging.INFO)
        yield scrapy.Request("https://kyfw.12306.cn/otn/resources/js/framework/station_name.js",callback=self.get_stations)




    # 处理所有站段 并 组合来发送请求
    def get_stations(self,response):
        self.log("站段信息加载完成...",level=logging.INFO)
        # 获取站段数据
        ret = re.findall('\'([\s\S]*)\'', response.body.decode('utf-8'))
        if len(ret):
            self.stations = ret[0].split('@')
            self.stations.pop(0)
        else:
            self.log("没有获取到站段信息",level=logging.INFO)

        # 把所有的站点信息做成字典
        self.stations_dic = {}
        # 反向字典 为构造数据准备
        self.stations_dic_r = {}
        for s in self.stations:
            self.stations_dic[s.split('|')[1]] = s.split('|')[2]
            self.stations_dic_r[s.split('|')[2]] = s.split('|')[1]

        # 组合站站数据来发送请求
        # stac = []

        print("共有站段信息： "+str(len(self.stations)))
        print("共有站站组合 ："+str(len(self.train_list)))

        for i in self.train_list:
            # print(i)
            # stac.append({'s': self.stations[i], 'e': self.stations[j]})

            # 发起获取车次列表的请求
            s_station = str(i.split('-')[0]).strip()

            e_station = str(i.split('-')[1]).strip()

            # print(s_station)
            # print(e_station)
            # print(s_station in self.stations)
            # print(e_station in self.stations)

            if s_station in self.stations_dic and e_station in self.stations_dic:
                train_url = "https://kyfw.12306.cn/otn/leftTicket/" + self.queryUrl + "?leftTicketDTO.train_date=" + self.query_date + \
                            "&leftTicketDTO.from_station=" + self.stations_dic[s_station] + \
                            "&leftTicketDTO.to_station=" + self.stations_dic[e_station] + "&purpose_codes=ADULT"
                # print(train_url)
                # return
                yield scrapy.Request(train_url, callback=self.get_traincode)
                # return


            # print(len(stac))
        # print(stac[0])
        # print(stac[3667985])


    #获取列车车次
    def get_traincode(self,response):
        ret = response.body.decode("utf-8")
        if "网络可能存在问题" in ret:
            self.log("多次下载依然错误:"+response.request.url,level=logging.INFO)
            return

        #解析json
        # print("train_ret:"+ret)
        json_ret = json.loads(ret)
        if len(json_ret['data']['result']) > 0:
            ret_train_list = json_ret['data']['result']
            for tl in ret_train_list:
                tl_s = tl.split('|')


                # 优先取始发终到车次信息 过滤掉不是始发终到的车次
                if tl_s[4]!=tl_s[6] or tl_s[5]!=tl_s[7]:
                    # self.log("ignore data: %s|%s|%s|%s"%(tl_s[4],tl_s[5],tl_s[6],tl_s[7]),level=logging.INFO)
                    continue

                item = TrainCodeItem()
                item['TrainNo'] = tl_s[2]
                item['TrainCode'] = tl_s[3]
                item['StartStation'] = self.stations_dic_r[tl_s[4]]
                item['EndStation'] = self.stations_dic_r[tl_s[5]]
                item['StartTime'] = tl_s[8]
                item['EndTime'] = tl_s[9]
                item['TakeTime'] = tl_s[10]
                item['StartDate'] = tl_s[13]
                item['QueryDate'] = self.query_date
                item['Info'] = tl
                yield item

                # 发送车次详情信息
                train_detail_url= "https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no="+ tl_s[2] +\
                               "&from_station_telecode="+ tl_s[4] +\
                               "&to_station_telecode="+ tl_s[5] +\
                               "&depart_date="+ tl_s[13][0:4]+"-"+tl_s[13][4:6]+"-"+tl_s[13][6:]
                yield scrapy.Request(train_detail_url,callback=self.get_traindetail,meta=item)






    #获取车次 途径站信息
    def get_traindetail(self,response):
        ret = response.body.decode("utf-8")
        if "网络可能存在问题" in ret:
            self.log("多次下载依然错误:"+response.request.url,level=logging.INFO)
            return
        if "200" in ret:
            ret = json.loads(ret)
            ret = ret['data']['data']
            # item = TrainDetailItem()
            # item['Info'] = ret
            # item['TrainNo'] = response.meta['TrainNo']
            # item['TrainCode'] = response.meta['TrainCode']
            # item['QueryDate'] = self.query_date

            # 再次发起请求 反推 每个车站的信息
            ret = json.loads(ret)
            for r in ret:
                train_url = "https://kyfw.12306.cn/otn/leftTicket/" + self.queryUrl + "?leftTicketDTO.train_date=" + self.query_date + \
                            "&leftTicketDTO.from_station=" + self.stations_dic[r[""]] + \
                            "&leftTicketDTO.to_station=" + self.stations_dic[r[""]] + "&purpose_codes=ADULT"
                # print(train_url)
                # return
                yield scrapy.Request(train_url, callback=self.get_traincode,meta=r)



            # yield item

        else:
            self.log("获取车次详情失败",level=logging.INFO)

    # 通过途径站信息 反推 每个车站的发到站
    def get_train_other_detail(self,response):
        pass
    pass
