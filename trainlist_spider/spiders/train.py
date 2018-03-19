
import scrapy
import re
import datetime
import json

from trainlist_spider.items import *
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
                yield scrapy.Request(train_url, callback=self.get_traincode, dont_filter=True)
                # return


            # print(len(stac))
        # print(stac[0])
        # print(stac[3667985])


    #获取列车车次
    def get_traincode(self,response):
        # return
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

                if "停运" in tl or "暂停发售" in tl:
                    continue

                item = TrainCodeItem()
                item['TrainNo'] = tl_s[2]
                item['TrainCode'] = tl_s[3]
                item['StartStation'] = self.stations_dic_r[tl_s[4]]
                item['EndStation'] = self.stations_dic_r[tl_s[5]]
                item['StartTime'] = tl_s[8]
                item['EndTime'] = tl_s[9]
                item['TakeTime'] = tl_s[10]
                item['StartDate'] = datetime.datetime.strptime(tl_s[13],'%Y%m%d')
                item['QueryDate'] = self.query_date
                item['Info'] = tl
                yield item

                # 发送车次详情信息
                train_detail_url= "https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no="+ tl_s[2] +\
                               "&from_station_telecode="+ tl_s[4] +\
                               "&to_station_telecode="+ tl_s[5] +\
                               "&depart_date="+ tl_s[13][0:4]+"-"+tl_s[13][4:6]+"-"+tl_s[13][6:]
                yield scrapy.Request(train_detail_url,callback=self.get_traindetail,meta=item, dont_filter=True)






    #获取车次 途径站信息
    def get_traindetail(self,response):
        ret = response.body.decode("utf-8")
        # self.log(ret, level=logging.INFO)

        if "200" in ret:
            ret = json.loads(ret)
            ret = ret['data']['data']


            if len(ret) == 0:
                self.log("没有获取到途径站数据:"+str(response.request.url), level=logging.INFO)
                return


            # item = TrainDetailItem_v2()



            # 非直达列车
            if len(ret) > 2:

                station_no = 2
                train_list = response.meta
                detail_info = ret

                # 第一个车站的信息
                detail_info[0]['start_station_name'] = train_list['StartStation']
                detail_info[0]['end_station_name'] = train_list['EndStation']
                detail_info[0]['arrive_train_code'] = '----'
                detail_info[0]['depart_train_code'] = train_list['TrainCode']


                for i in range(1, len(ret)-1):
                    detail_info[i]['start_station_name'] = train_list['StartStation']
                    detail_info[i]['train_class_name'] = ret[0]['train_class_name']
                    detail_info[i]['service_type'] = ret[0]['service_type']
                    detail_info[i]['end_station_name'] = train_list['EndStation']
                    detail_info[i]['arrive_train_code'] = detail_info[i-1]['depart_train_code']
                    detail_info[i]['depart_train_code'] = ''

                    if self.stations_dic.get(detail_info[i]['station_name']) and self.stations_dic.get(detail_info[i+1]['station_name']):


                        train_url = "https://kyfw.12306.cn/otn/leftTicket/" + self.queryUrl + "?leftTicketDTO.train_date=" + self.query_date + \
                                    "&leftTicketDTO.from_station=" + self.stations_dic[ret[i]['station_name']] + \
                                    "&leftTicketDTO.to_station=" + self.stations_dic[ret[i + 1]["station_name"]] + \
                                    "&purpose_codes=ADULT"
                        # print(train_url)
                        # return
                        yield scrapy.Request(train_url, callback=self.q_get_detail, dont_filter=True, meta={
                            'station_no': station_no,
                            'train_list':train_list,
                            'detail_info':detail_info})
                        # station_no += 1
                        break
                    else:
                        station_no += 1
                else:
                    # 进到这里 说明 车次列表没有该车次信息 ，并且已经循环完了，那么直接添加到途径站信息
                    detail_info[len(ret)-1]['start_station_name'] = train_list['StartStation']
                    detail_info[len(ret)-1]['train_class_name'] = ret[0]['train_class_name']
                    detail_info[len(ret)-1]['service_type'] = ret[0]['service_type']
                    detail_info[len(ret)-1]['end_station_name'] = train_list['EndStation']
                    detail_info[len(ret)-1]['arrive_train_code'] = detail_info[len(ret)- 2]['depart_train_code']
                    detail_info[len(ret)-1]['depart_train_code'] = ''

                    item = TrainDetailItem()
                    item['TrainNo'] = response.meta['TrainNo']
                    item['TrainCode'] = response.meta['TrainCode']
                    item['QueryDate'] = self.query_date
                    item['Info'] = (detail_info)
                    yield item



            # 直达列车
            elif len(ret) == 2:
                item = TrainDetailItem()
                item['TrainNo'] = response.meta['TrainNo']
                item['TrainCode'] = response.meta['TrainCode']
                item['QueryDate'] = self.query_date
                info_list = []

                for r in ret:
                    temp  = TrainDetailInfo()
                    temp['start_date'] = str(response.meta['StartDate'])
                    temp['start_station_name'] = str(response.meta['StartStation'])
                    temp['arrive_time'] = r['arrive_time']
                    temp['arrive_train_code'] = str(response.meta['TrainCode'])
                    temp['depart_train_code'] = str(response.meta['TrainCode'])
                    temp['station_name'] = r['station_name']
                    temp['train_class_name'] = str(ret[0]['train_class_name'])
                    temp['service_type'] = str(ret[0]['service_type'])
                    temp['start_time'] = r['start_time']
                    temp['stopover_time'] = r['stopover_time']
                    temp['end_station_name'] = str(response.meta['EndStation'])
                    temp['station_no'] = r['station_no']
                    temp['isEnabled'] = r['isEnabled']
                    info_list.append(temp)

                info_list[0]['arrive_train_code'] = '----'
                info_list[1]['depart_train_code'] = '----'
                item['Info'] = info_list
                yield item

            else:
                self.log("不知道什么类型的车："+ str(response.body.decode("utf-8")),level=logging.INFO)


        else:
            self.log("获取车次详情失败",level=logging.INFO)


    def q_get_detail(self,response):
        ret = response.body.decode("utf-8")
        station_no = response.meta['station_no']
        detail_info = response.meta['detail_info']
        train_list = response.meta['train_list']
        # self.log(ret, level=logging.INFO)
        json_ret = json.loads(ret)

        if len(json_ret['data']['result']) <= 0:
            # self.log("没有取到数据" + str(json.dumps(json_ret['data']['result'])), level=logging.INFO)
            self.log("没有取到数据:"+str(response.request.url),level=logging.INFO)
            self.log("没有取到数据:" + str(json.dumps(json_ret)), level=logging.INFO)

            # 继续 取下一个车次
            yield self.queue_train_detail(station_no, train_list, detail_info, '')
            # for i,q in enumerate(queue):
            #     print("q_index:"+str(i))
            return


        ret_train_list = json_ret['data']['result']
        for tl in ret_train_list:
            tl_s = tl.split('|')

            if train_list['TrainNo'] == tl_s[2]:
                c_train_code = tl_s[3]
                # next(self.queue_train_detail(station_no, train_list, detail_info, c_train_code))
                yield self.queue_train_detail(station_no, train_list, detail_info, c_train_code)
                # for i, q in enumerate(queue):
                #     print("q_index:" + str(i))
                break


        else:
            self.log("没有找到匹配的车次:%s 信息：%s"%(train_list['TrainNo'],str(response.request.url)),level=logging.INFO)
            # 继续 取下一个车次
            # next(self.queue_train_detail(station_no , train_list, detail_info, ''))
            yield self.queue_train_detail(station_no, train_list, detail_info, '')
            # for i, q in enumerate(queue):
            #     print("q_index:" + str(i))
            # return



    def queue_train_detail(self, station_no, train_list, detail_info, c_train_code):

        '''
        通过站续 途径站信息 来发起新的请求 获取途径站
        :param station_no: 站续
        :param train_list: 主时刻表信息
        :param detail_info: 所有途径站信息
        :return:
        '''
        # 更改前一个站的 到达和出发车次


        detail_info[int(station_no) - 1]['arrive_train_code'] = detail_info[int(station_no) - 2]['depart_train_code']
        detail_info[int(station_no) - 1]['depart_train_code'] = c_train_code

        # 更改当前站
        detail_info[int(station_no)]['start_station_name'] = train_list['StartStation']
        detail_info[int(station_no)]['train_class_name'] = detail_info[0]['train_class_name']
        detail_info[int(station_no)]['service_type'] = detail_info[0]['service_type']
        detail_info[int(station_no)]['end_station_name'] = train_list['EndStation']
        detail_info[int(station_no)]['arrive_train_code'] = c_train_code
        detail_info[int(station_no)]['depart_train_code'] = ''

        if int(station_no) < (len(detail_info) - 1):

            # 需要再一次发起请求 因为站续小于倒数第二个

            # 再次发起请求 取下一个途径站信息
            queue = range(int(station_no), len(detail_info) - 1)

            for i in queue:

                if self.stations_dic.get(detail_info[i]['station_name']) and self.stations_dic.get(
                        detail_info[i + 1]['station_name']):

                    train_url = "https://kyfw.12306.cn/otn/leftTicket/" + self.queryUrl + "?leftTicketDTO.train_date=" + self.query_date + \
                                "&leftTicketDTO.from_station=" + self.stations_dic[detail_info[i]['station_name']] + \
                                "&leftTicketDTO.to_station=" + self.stations_dic[detail_info[i + 1]["station_name"]] + \
                                "&purpose_codes=ADULT"
                    # print(train_url)
                    # return
                    station_no += 1

                    return scrapy.Request(train_url, callback=self.q_get_detail, dont_filter=True, meta={
                        'station_no': station_no,
                        'train_list': train_list,
                        'detail_info': detail_info})

                    break
                else:
                    station_no += 1

                    # 更改前一个站的 到达和出发车次
                    detail_info[int(station_no) - 1]['arrive_train_code'] = detail_info[int(station_no) - 2][
                        'depart_train_code']
                    detail_info[int(station_no) - 1]['depart_train_code'] = ''

                    # 更改当前站
                    detail_info[int(station_no)]['start_station_name'] = train_list['StartStation']
                    detail_info[int(station_no)]['train_class_name'] = detail_info[0][
                        'train_class_name']
                    detail_info[int(station_no)]['service_type'] = detail_info[0]['service_type']
                    detail_info[int(station_no)]['end_station_name'] = train_list['EndStation']
                    detail_info[int(station_no)]['arrive_train_code'] = c_train_code
                    detail_info[int(station_no)]['depart_train_code'] = ''
            else:
                # 增加数据
                item = TrainDetailItem()
                item['TrainNo'] = train_list['TrainNo']
                item['TrainCode'] = train_list['TrainCode']
                item['QueryDate'] = self.query_date
                item['Info'] = (detail_info)

                return item


        elif int(station_no) == (len(detail_info) - 1):
            # 如果途径站的数量 等于 站续 说明已经是最后两个车站了 那么只增加下一个站的到站车次 即可
            # 增加下一个途径站的部分信息

            # 增加数据
            item = TrainDetailItem()
            item['TrainNo'] = train_list['TrainNo']
            item['TrainCode'] = train_list['TrainCode']
            item['QueryDate'] = self.query_date
            item['Info'] = (detail_info)

            return item

        else:
            self.log("坐标超了？车次：%s,站续：%s"%(c_train_code,station_no))



