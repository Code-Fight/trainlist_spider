import scrapy
import re
import datetime
import json
# from http import cookiejar
from scrapy.http.cookies import CookieJar
# from urllib import request as urequest
from PIL import Image
from io import BytesIO
import base64
import time
# from scrapy.pipelines.images

from trainlist_spider.items import *
from scrapy.conf import settings
import logging
import requests


class TrainSpider(scrapy.Spider):
    name = 'train'
    allowed_domains = ['12306.cn','192.168.40.13']
    start_urls = ['https://12306.cn/',]



    # 请求 leftTicket/init
    def start_requests(self):
        self.j_url = "https://kyfw.12306.cn/otn/queryTrainInfo/init"
        # 为了对抗 12306的验证码识别时的 4秒延迟
        self.d_url = "http://192.168.2.118:18080/delay.ashx"
        # 验证码识别服务
        self.vcode_url = "http://192.168.2.118:18888/code"
        self.n_success = 0
        self.n_error = 0
        self.n_o_error = 0
        # self.query_date = "2018-05-10"
        # return self.get_vcode("ss")

        # yield scrapy.Request("https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=other&rand=sjrand&0.6072056947144686",callback=self.get_vcode_image)





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
                    ret = train['train_no']
                    # ret = re.findall('\(([\s\S]*)\)', ret)
                    self.train_list.add(ret)

        # print(len(self.train_list))
        # return
        self.log("站站组合信息加载完成,共"+str(len(self.train_list))+"个，开始采集...",level=logging.INFO)
        self.n_cookiejar = len(self.train_list)+1
        for i,tl in enumerate(self.train_list):
            # print(tl)
            yield scrapy.Request("https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=other&rand=sjrand&0.6072056947144686",
                                 priority = 1,
                                 meta={'cookiejar':i,"train_no":tl},
                                 dont_filter=True,
                                 callback=self.get_vcode_image)
            # break



    def get_vcode_image(self,response):
        '''
        获取验证码图片
        :return:
        '''
        # print(response.meta.get("train_no"))
        # print(response.meta.get("cookiejar"))
        # s = requests.session()
        # cookiejar = CookieJar()
        # cookiejar.extract_cookies(response, response.request)
        # cj_tmp = []
        # for c in cookiejar:
        #     requests.utils.add_dict_to_cookiejar(s.cookies, {c.name: c.value})
        #     # cj_tmp.append({"name":c.name,"value":c.value})
        cookiejar = response.meta['cookiejar']
        # print(cookiejar)
        # print(cj_tmp)
        # 获取验证码
        # re = s.get('https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=other&rand=sjrand&0.5603309825943052')

        vcode_image = Image.open(BytesIO(response.body))

        # vcode_image.show()

        # 识别验证码
        # image_o = vcode_image
        buffered = BytesIO()
        vcode_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue())

        sb_url = self.vcode_url
        post_Data = {
            "vcode": bytes.decode(img_base64)
        }

        rsp = requests.post(sb_url, data=post_Data)
        vcode_text = rsp.text

        # 验证验证码
        # 验证之前需要等待4S  所以在这里请求一次延迟接口
        yield scrapy.Request(url=self.d_url,
                             dont_filter=True,
                             priority=3,
                             meta={"train_no":response.meta.get("train_no"),"vcode_text":vcode_text,"cj":cookiejar},
                             callback=self.check_vcode)






    def check_vcode(self,response):
        '''
        验证code
        :param v_text:
        :return:
        '''

        vcode_text = response.meta.get("vcode_text")
        cj = response.meta.get("cj")
        # time.sleep(1)

        post_url = "https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn"

        post_Data = {"randCode": vcode_text, "rand": "sjrand"}


        yield scrapy.FormRequest(url=post_url,
                                 priority = 5,
                                 formdata=post_Data,
                                 dont_filter=True,
                                 callback=self.cb_check_vocde,
                                 meta={'cookiejar':cj,'cj':cj,"train_no": response.meta.get("train_no"), "vcode_text": vcode_text})
            # if "randCodeRight" in re.text:
            #     return True
            # elif "randCodeError" in re.text:
            #     return False
            # else:
            #     time.sleep(1)

    def cb_check_vocde(self,response):
        '''
        验证 验证码回调
        :param response:
        :return:
        '''

        vcode_text = response.meta.get("vcode_text")
        re = response.body.decode('utf-8')
        if self.n_success!=0 or self.n_error!=0:
            print("识别率",(self.n_success/(self.n_success+self.n_error))*100,"%")
            print("未知错误：",self.n_o_error)
        if "randCodeRight" in re:
            self.n_success +=1
            train_no = response.meta.get("train_no")
            vcode_text = response.meta.get("vcode_text")
            url = "https://kyfw.12306.cn/otn/queryTrainInfo/query?leftTicketDTO.train_no=" + train_no + "&leftTicketDTO.train_date=" + self.query_date + "&rand_code=" + vcode_text
            yield scrapy.Request(url=url,
                                 priority=10,
                                 dont_filter=True,
                                 callback=self.cb_get_data,
                                 meta={'cookiejar': response.meta.get("cookiejar"), "train_no": response.meta.get("train_no"),
                                       "vcode_text": vcode_text})

            pass

        elif "randCodeError" in re:
            self.n_error += 1
            # 调用重新发起请求
            # print("验证码错误")
            yield scrapy.Request(url="https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=other&rand=sjrand&0.607205694714468",
                                 priority=1,
                                 dont_filter=True,
                                 meta={'cookiejar':response.meta.get("cookiejar"),"train_no": response.meta.get("train_no"), "vcode_text": vcode_text,
                                       "cj": response.meta.get("cookiejar")},
                                 callback=self.get_vcode_image)
        else:
            print("验证码未知原因")
            print(re)
            self.n_cookiejar +=1
            self.n_o_error += 1
            s = requests.session()
            cookiejar = CookieJar()
            cookiejar.extract_cookies(response, response.request)
            cj_tmp = []
            for c in cookiejar:
                # requests.utils.add_dict_to_cookiejar(s.cookies, {c.name: c.value})
                cj_tmp.append({"name":c.name,"value":c.value})
            cookiejar = response.meta['cookiejar']
            print(cookiejar)
            # print(cj_tmp)
            # yield scrapy.Request(url=self.j_url,
            #                      priority=4,
            #                      dont_filter=True,
            #                      meta={"train_no": response.meta.get("train_no"), "vcode_text": vcode_text,
            #                            "cj": response.meta.get("cookiejar")},
            #                      callback=self.check_vcode)
            yield scrapy.Request(url="https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=other&rand=sjrand&0.607205694714468",
                                 priority=1,
                                 dont_filter=True,
                                 meta={'cookiejar': self.n_cookiejar,
                                       "train_no": response.meta.get("train_no"), "vcode_text": vcode_text,
                                       "cj": self.n_cookiejar},
                                 callback=self.get_vcode_image)

    # def get_data(self,response):
    #     '''
    #     获取数据
    #     :param response:
    #     :return:
    #     '''
    #     train_no = response.meta.get("train_no")
    #     vcode_text = response.meta.get("vcode_text")
    #     url = "https://kyfw.12306.cn/otn/queryTrainInfo/query?leftTicketDTO.train_no=" + train_no + "&leftTicketDTO.train_date=" + self.query_date + "&rand_code=" + vcode_text
    #     yield scrapy.Request(url=url,
    #                          priority=10,
    #                          dont_filter=True,
    #                          callback=self.cb_get_data,
    #                          meta={'cookiejar':response.meta.get("cj"),"train_no":response.meta.get("train_no"),"vcode_text":vcode_text})

    def cb_get_data(self,response):
        '''
        获取数据回调
        :param response:
        :return:
        '''

        train_no = response.meta.get("train_no")
        vcode_text = response.meta.get("vcode_text")

        # 计算停留时间
        def StopOverTime(o):
            if o['arrive_time'] == "----":
                return 0

            ar = str(o['arrive_time']).split(':')
            st = str(o['start_time']).split(':')

            st_m = int(st[0]) * 60 + int(st[1])
            ar_m = int(ar[0]) * 60 + int(ar[1])
            s = int(st_m) - int(ar_m)
            if s < 0:
                s += 1440
            return s
        r = response.body.decode('utf-8')
        retData = json.loads(r)

        if retData["data"]["data"] == None:
            self.log( train_no+ " nono data ")
            return None

        if "验证码" not in r and len(retData["data"]["data"]) > 1:
            # self.log(r_j)
            item = TrainCodeItem()
            item['TrainNo'] = train_no
            item['TrainCode'] = retData['data']['data'][0]['station_train_code']
            item['StartStation'] = retData['data']['data'][0]['station_name']
            item['EndStation'] = retData['data']['data'][len(retData['data']['data']) - 1]['station_name']
            item['StartTime'] = retData['data']['data'][0]['start_time']
            item['EndTime'] = retData['data']['data'][len(retData['data']['data']) - 1]['arrive_time']
            item['TakeTime'] = retData['data']['data'][len(retData['data']['data']) - 1]['running_time']
            item['StartDate'] = self.query_date
            item['QueryDate'] = self.query_date
            item['Info'] = ''
            yield item

            # 详情
            ret = retData['data']['data']
            item = TrainDetailItem()
            item['TrainNo'] = train_no
            item['TrainCode'] = retData['data']['data'][0]['station_train_code']
            item['QueryDate'] = self.query_date
            info_list = []

            for i, r in enumerate(ret):
                temp = TrainDetailInfo()
                temp['start_date'] = self.query_date
                temp['start_station_name'] = retData['data']['data'][0]['station_name']
                temp['arrive_time'] = r['arrive_time']

                if i == 0:
                    temp['arrive_train_code'] = str(r['station_train_code'])
                else:
                    temp['arrive_train_code'] = str(ret[i - 1]['station_train_code'])

                temp['depart_train_code'] = r['station_train_code']

                temp['station_name'] = r['station_name']
                temp['train_class_name'] = str(ret[0]['train_class_name'])
                temp['service_type'] = str(ret[0]['service_type'])
                temp['start_time'] = r['start_time']
                temp['stopover_time'] = StopOverTime(r)
                temp['end_station_name'] = retData['data']['data'][len(retData['data']['data']) - 1]['station_name']
                temp['station_no'] = r['station_no']
                temp['isEnabled'] = ''
                temp['arrive_day_diff'] = str(r['arrive_day_diff'])
                temp['arrive_day_str'] = str(r['arrive_day_str'])
                temp['running_time'] = str(r['running_time'])
                info_list.append(temp)


            item['Info'] = info_list
            yield item

        else:
            yield scrapy.Request(url="https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=other&rand=sjrand&0.607205694714468",
                                 dont_filter=True,
                                 priority=1,
                                 callback=self.get_vcode_image,
                                 meta={'cookiejar':response.meta.get("cj"),"train_no":response.meta.get("train_no"),"vcode_text":vcode_text})


    # def get_vcode(self,response):
    #     print(response.meta.get("train_no"))
    #     # 验证验证码
    #     def check_vcode(v_text):
    #
    #         time.sleep(3)
    #         while True:
    #
    #             post_url = "https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn"
    #
    #             post_Data = {"randCode": v_text, "rand": "sjrand"}
    #             re = s.post(url=post_url, data=post_Data)
    #             if "randCodeRight" in re.text:
    #
    #                 return True
    #             elif "randCodeError" in re.text:
    #                 return False
    #             else:
    #                 time.sleep(1)
    #     # 获取数据
    #     def GetData(train_no,v_text,query_date,ss):
    #         url="https://kyfw.12306.cn/otn/queryTrainInfo/query?leftTicketDTO.train_no="+train_no+"&leftTicketDTO.train_date="+query_date+"&rand_code="+v_text
    #         r = ss.get(url)
    #         r_j = json.loads(r.text)
    #
    #         if r_j["data"]["data"] ==None:
    #             return True,None
    #
    #         if "验证码" not in r.text and len(r_j["data"]["data"])>1:
    #             # self.log(r_j)
    #
    #             return True,r_j
    #         else:
    #             return False,None
    #     # 计算停留时间
    #     def StopOverTime(o):
    #         if o['arrive_time'] == "----":
    #             return 0
    #
    #         ar = str(o['arrive_time']).split(':')
    #         st = str(o['start_time']).split(':')
    #
    #
    #         st_m = int(st[0])*60 + int(st[1])
    #         ar_m = int(ar[0])*60 + int(ar[1])
    #         s = int(st_m) - int(ar_m)
    #         if s < 0:
    #             s+=1440
    #         return s
    #
    #
    #     s = requests.session()
    #     cookiejar = CookieJar()
    #     cookiejar.extract_cookies(response, response.request)
    #     for c in cookiejar:
    #         requests.utils.add_dict_to_cookiejar(s.cookies, {c.name:c.value})
    #
    #
    #     # 开始识别验证码
    #     while True:
    #         # 获取验证码
    #         re = s.get('https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=other&rand=sjrand&0.5603309825943052')
    #         # print(s.cookies)
    #         # print(re.cookies)
    #         vcode_image = Image.open(BytesIO(re.content))
    #         vcode_image.show()
    #
    #         # 识别验证码
    #         # image_o = vcode_image
    #         buffered = BytesIO()
    #         vcode_image.save(buffered,format="PNG")
    #         img_base64 = base64.b64encode(buffered.getvalue())
    #
    #         sb_url = "http://192.168.2.235:8080/code"
    #         post_Data = {
    #             "vcode":bytes.decode(img_base64)
    #         }
    #
    #         rsp = requests.post(sb_url,data=post_Data)
    #         vcode_text = rsp.text
    #
    #         # 获取数据 并 存储
    #         if check_vcode(vcode_text):
    #             train_no = response.request.meta.get("train_no")
    #             isSuccess,retData = GetData(train_no,vcode_text,self.query_date,s)
    #             if retData==None:
    #                 break
    #             if isSuccess:
    #
    #                 item = TrainCodeItem()
    #                 item['TrainNo'] = train_no
    #                 item['TrainCode'] = retData['data']['data'][0]['station_train_code']
    #                 item['StartStation'] = retData['data']['data'][0]['station_name']
    #                 item['EndStation'] = retData['data']['data'][len(retData['data']['data'])-1]['station_name']
    #                 item['StartTime'] = retData['data']['data'][0]['start_time']
    #                 item['EndTime'] = retData['data']['data'][len(retData['data']['data'])-1]['arrive_time']
    #                 item['TakeTime'] = retData['data']['data'][len(retData['data']['data'])-1]['running_time']
    #                 item['StartDate'] = self.query_date
    #                 item['QueryDate'] = self.query_date
    #                 item['Info'] = ''
    #                 yield item
    #
    #                 # 详情
    #                 ret  = retData['data']['data']
    #                 item = TrainDetailItem()
    #                 item['TrainNo'] = train_no
    #                 item['TrainCode'] = retData['data']['data'][0]['station_train_code']
    #                 item['QueryDate'] = self.query_date
    #                 info_list = []
    #
    #                 for i,r in enumerate(ret):
    #                     temp = TrainDetailInfo()
    #                     temp['start_date'] = self.query_date
    #                     temp['start_station_name'] = retData['data']['data'][0]['station_name']
    #                     temp['arrive_time'] = r['arrive_time']
    #
    #                     if i == 0 :
    #                         temp['arrive_train_code'] = str(r['station_train_code'])
    #                     else:
    #                         temp['arrive_train_code'] = str(ret[i-1]['station_train_code'])
    #
    #
    #                     temp['depart_train_code'] = r['station_train_code']
    #
    #                     temp['station_name'] = r['station_name']
    #                     temp['train_class_name'] = str(ret[0]['train_class_name'])
    #                     temp['service_type'] = str(ret[0]['service_type'])
    #                     temp['start_time'] = r['start_time']
    #                     temp['stopover_time'] = StopOverTime(r)
    #                     temp['end_station_name'] = retData['data']['data'][len(retData['data']['data'])-1]['station_name']
    #                     temp['station_no'] = r['station_no']
    #                     temp['isEnabled'] = ''
    #                     temp['arrive_day_diff'] = str(r['arrive_day_diff'])
    #                     temp['arrive_day_str'] = str(r['arrive_day_str'])
    #                     temp['running_time'] = str(r['running_time'])
    #                     info_list.append(temp)
    #
    #                 # info_list[0]['arrive_train_code'] = '----'
    #                 # info_list[1]['depart_train_code'] = '----'
    #                 item['Info'] = info_list
    #                 yield item
    #                 break

    # def get_vcode_v2(self, response):
    #     print(response.meta.get("train_no"))
    #
    #
    #
    #
    #
    #     # 获取数据
    #     def GetData(train_no, v_text, query_date, ss):
    #         url = "https://kyfw.12306.cn/otn/queryTrainInfo/query?leftTicketDTO.train_no=" + train_no + "&leftTicketDTO.train_date=" + query_date + "&rand_code=" + v_text
    #         r = ss.get(url)
    #         r_j = json.loads(r.text)
    #
    #         if r_j["data"]["data"] == None:
    #             return True, None
    #
    #         if "验证码" not in r.text and len(r_j["data"]["data"]) > 1:
    #             # self.log(r_j)
    #
    #             return True, r_j
    #         else:
    #             return False, None
    #
    #     # 计算停留时间
    #     def StopOverTime(o):
    #         if o['arrive_time'] == "----":
    #             return 0
    #
    #         ar = str(o['arrive_time']).split(':')
    #         st = str(o['start_time']).split(':')
    #
    #         st_m = int(st[0]) * 60 + int(st[1])
    #         ar_m = int(ar[0]) * 60 + int(ar[1])
    #         s = int(st_m) - int(ar_m)
    #         if s < 0:
    #             s += 1440
    #         return s
    #
    #     s = requests.session()
    #     cookiejar = CookieJar()
    #     cookiejar.extract_cookies(response, response.request)
    #     for c in cookiejar:
    #         requests.utils.add_dict_to_cookiejar(s.cookies, {c.name: c.value})
    #
    #
    #     # 获取验证码
    #     re = s.get(
    #         'https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=other&rand=sjrand&0.5603309825943052')
    #     # print(s.cookies)
    #     # print(re.cookies)
    #     vcode_image = Image.open(BytesIO(re.content))
    #     # vcode_image.show()
    #
    #     # 识别验证码
    #     # image_o = vcode_image
    #     buffered = BytesIO()
    #     vcode_image.save(buffered, format="PNG")
    #     img_base64 = base64.b64encode(buffered.getvalue())
    #
    #     sb_url = "http://192.168.2.235:8080/code"
    #     post_Data = {
    #         "vcode": bytes.decode(img_base64)
    #     }
    #
    #     rsp = requests.post(sb_url, data=post_Data)
    #     vcode_text = rsp.text
    #
    #
    #     yield scrapy.Request(url=self.d_url,dont_filter=True,priority=2,
    #                          meta={'s':s,'v_text':vcode_text,'train_no':response.meta.get("train_no")},callback=self.get_vcode_crack)
    #     # 获取数据 并 存储
    #
    #
    #
    # def get_vcode_crack(self,response):
    #     s = response.meta.get('s')
    #     v_text= response.meta.get('v_text')
    #     post_url = "https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn"
    #
    #     post_Data = {"randCode": v_text, "rand": "sjrand"}
    #     re = s.post(url=post_url, data=post_Data)
    #     if "randCodeRight" in re.text:
    #         train_no = response.meta.get("train_no")
    #         vcode_text = response.meta.get("vcode_text")
    #         url = "https://kyfw.12306.cn/otn/queryTrainInfo/query?leftTicketDTO.train_no=" + train_no + "&leftTicketDTO.train_date=" + self.query_date + "&rand_code=" + vcode_text
    #         yield scrapy.Request(url=url,
    #                              priority=10,
    #                              dont_filter=True,
    #                              callback=self.get_vcode_data,
    #                              meta={'cookiejar': response.meta.get("cj"), "train_no": response.meta.get("train_no"),
    #                                    "vcode_text": vcode_text})
    #
    #
    #     else:
    #         yield scrapy.Request("https://kyfw.12306.cn/otn/queryTrainInfo/init",
    #                              priority=1,
    #                              meta={ "train_no":  response.meta.get("train_no")},
    #                              dont_filter=True,
    #                              callback=self.get_vcode_v2)
    #
    # def get_vcode_data(self,response):
    #     print("开始获取数据")
    #     train_no = response.request.meta.get("train_no")
    #     def StopOverTime(o):
    #         if o['arrive_time'] == "----":
    #             return 0
    #
    #         ar = str(o['arrive_time']).split(':')
    #         st = str(o['start_time']).split(':')
    #
    #         st_m = int(st[0]) * 60 + int(st[1])
    #         ar_m = int(ar[0]) * 60 + int(ar[1])
    #         s = int(st_m) - int(ar_m)
    #         if s < 0:
    #             s += 1440
    #         return s
    #     r = response.body.decode('utf-8')
    #     retData = json.loads(r)
    #
    #     item = TrainCodeItem()
    #     item['TrainNo'] = train_no
    #     item['TrainCode'] = retData['data']['data'][0]['station_train_code']
    #     item['StartStation'] = retData['data']['data'][0]['station_name']
    #     item['EndStation'] = retData['data']['data'][len(retData['data']['data']) - 1]['station_name']
    #     item['StartTime'] = retData['data']['data'][0]['start_time']
    #     item['EndTime'] = retData['data']['data'][len(retData['data']['data']) - 1]['arrive_time']
    #     item['TakeTime'] = retData['data']['data'][len(retData['data']['data']) - 1]['running_time']
    #     item['StartDate'] = self.query_date
    #     item['QueryDate'] = self.query_date
    #     item['Info'] = ''
    #     yield item
    #
    #     # 详情
    #     ret = retData['data']['data']
    #     item = TrainDetailItem()
    #     item['TrainNo'] = train_no
    #     item['TrainCode'] = retData['data']['data'][0]['station_train_code']
    #     item['QueryDate'] = self.query_date
    #     info_list = []
    #
    #     for i, r in enumerate(ret):
    #         temp = TrainDetailInfo()
    #         temp['start_date'] = self.query_date
    #         temp['start_station_name'] = retData['data']['data'][0]['station_name']
    #         temp['arrive_time'] = r['arrive_time']
    #
    #         if i == 0:
    #             temp['arrive_train_code'] = str(r['station_train_code'])
    #         else:
    #             temp['arrive_train_code'] = str(ret[i - 1]['station_train_code'])
    #
    #         temp['depart_train_code'] = r['station_train_code']
    #
    #         temp['station_name'] = r['station_name']
    #         temp['train_class_name'] = str(ret[0]['train_class_name'])
    #         temp['service_type'] = str(ret[0]['service_type'])
    #         temp['start_time'] = r['start_time']
    #         temp['stopover_time'] = StopOverTime(r)
    #         temp['end_station_name'] = retData['data']['data'][len(retData['data']['data']) - 1][
    #             'station_name']
    #         temp['station_no'] = r['station_no']
    #         temp['isEnabled'] = ''
    #         temp['arrive_day_diff'] = str(r['arrive_day_diff'])
    #         temp['arrive_day_str'] = str(r['arrive_day_str'])
    #         temp['running_time'] = str(r['running_time'])
    #         info_list.append(temp)
    #
    #     # info_list[0]['arrive_train_code'] = '----'
    #     # info_list[1]['depart_train_code'] = '----'
    #     item['Info'] = info_list
    #     yield item
    #

