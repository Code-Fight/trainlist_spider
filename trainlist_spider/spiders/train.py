# -*- coding: utf-8 -*-
import scrapy
import re
import datetime
import json
from trainlist_spider.items import TrainCodeItem
from trainlist_spider.items import TrainDetailItem


class TrainSpider(scrapy.Spider):
    name = 'train'
    allowed_domains = ['12306.cn']
    start_urls = ['https://12306.cn/',]

    # 获取所有站站数据
    def start_requests(self):
        self.log("准备加载50M的站站组合信息，请耐心等待吧...")
        yield scrapy.Request("https://kyfw.12306.cn/otn/resources/js/query/train_list.js",callback=self.get_ftstations)

    # 获取站点简码
    def get_ftstations(self,response):

        ret = response.body.decode('utf-8')
        if "train_list" not in ret:
            self.log("获取站站组合信息失败...")
            self.log(response.request.url)
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
        self.log("站站组合信息加载完成，开始加载站段信息...")
        yield scrapy.Request("https://kyfw.12306.cn/otn/resources/js/framework/station_name.js",callback=self.get_stations)




    # 处理所有站段 并 组合来发送请求
    def get_stations(self,response):
        self.log("站段信息加载完成...")
        # 获取站段数据
        ret = re.findall('\'([\s\S]*)\'', response.body.decode('utf-8'))
        if len(ret):
            self.stations = ret[0].split('@')
            self.stations.pop(0)
        else:
            self.log("没有获取到站段信息")

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
            query_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            # 发起获取车次列表的请求
            s_station = str(i.split('-')[0]).strip()

            e_station = str(i.split('-')[1]).strip()

            # print(s_station)
            # print(e_station)
            # print(s_station in self.stations)
            # print(e_station in self.stations)

            if s_station in self.stations_dic and e_station in self.stations_dic:
                train_url = "https://kyfw.12306.cn/otn/leftTicket/queryZ?leftTicketDTO.train_date=" + query_date + \
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
            self.log("多次下载依然错误:"+response.request.url)
            return

        #解析json
        # print("train_ret:"+ret)
        json_ret = json.loads(ret)
        if len(json_ret['data']['result']) > 0:
            ret_train_list = json_ret['data']['result']
            for tl in ret_train_list:
                tl_s = tl.split('|')
                item = TrainCodeItem()
                item['TrainNo'] = tl_s[2]
                item['TrainCode'] = tl_s[3]
                item['StartStation'] = self.stations_dic_r[tl_s[4]]
                item['EndStation'] = self.stations_dic_r[tl_s[5]]
                item['StartTime'] = tl_s[8]
                item['EndTime'] = tl_s[9]
                item['TakeTime'] = tl_s[10]
                item['QueryDate'] = tl_s[13]
                item['Info'] = tl
                yield item

                # 发送车次详情信息
                train_detail_url= "https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no="+ tl_s[2] +\
                               "&from_station_telecode="+ tl_s[4] +\
                               "&to_station_telecode="+ tl_s[5] +\
                               "&depart_date="+ tl_s[13][0:4]+"-"+tl_s[13][4:6]+"-"+tl_s[13][6:]
                yield scrapy.Request(train_detail_url,callback=self.get_traindetail,meta=item)






    #获取车次详细信息
    def get_traindetail(self,response):
        ret = response.body.decode("utf-8")
        if "网络可能存在问题" in ret:
            self.log("多次下载依然错误:"+response.request.url)
            return
        if "200" in ret:
            ret = json.loads(ret)
            ret = ret['data']['data']
            item = TrainDetailItem()
            item['Info'] = ret
            item['TrainNo'] = response.meta['TrainNo']
            item['TrainCode'] = response.meta['TrainCode']
            yield item

        else:
            self.log("获取车次详情失败")
