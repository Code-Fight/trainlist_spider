

import requests
# import ssl
import ssl

# context = ssl._create_unverified_context()


# from scrapy import Request

ssl._create_default_https_context = ssl._create_unverified_context

# requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

# requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH:!aNULL'
requests.adapters.DEFAULT_RETRIES = 10
s = requests.session()
s.keep_alive = False
proxies = {'http':'http://115.207.88.219:7305','https':'http://115.207.88.219:7305'}
# url = "https://kyfw.12306.cn/otn/leftTicket/queryO?leftTicketDTO.train_date=2018-03-20&leftTicketDTO.from_station=ICW&leftTicketDTO.to_station=DMQ&purpose_codes=ADULT"
url = "http://2017.ip138.com/ic.asp"
# re = requests.get(url, proxies = proxies)

try:
    re = requests.get(url, proxies=proxies, timeout=10)
    print(re.text)
except requests.exceptions.ConnectTimeout:
    print("超时")
except BaseException:
    print("异常")
# Request.
# print(re.text)
# re = requests.get("https://kyfw.12306.cn/otn/leftTicket/queryO?leftTicketDTO.train_date=2018-03-20&leftTicketDTO.from_station=ICW&leftTicketDTO.to_station=DMQ&purpose_codes=ADULT",
#                   headers = {'Host':'kyfw.12306.cn'})
# print(re.text)
#
# re = scrapy.Request("https://219.148.174.55/otn/leftTicket/queryO?leftTicketDTO.train_date=2018-03-20&leftTicketDTO.from_station=ICW&leftTicketDTO.to_station=DMQ&purpose_codes=ADULT",
#                   headers = {'Host':'kyfw.12306.cn'})
# print(re.body)

# re = scrapy.Request.("http://www.ip.cn/",callback=a)
# def a (re):
#
#     print(re.body)

#
# # sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
# fh =  open('/Users/zhangfeng/Downloads/train_list.js',encoding='UTF-8')
# txt = fh.read()
# txt = txt.replace("var",'')
# txt = txt.replace("train_list",'')
# txt = txt.replace("=",'')
# txt = txt.replace(" ",'')
# fh.close()
# trian_list = json.loads(txt)
# client = pymongo.MongoClient(host='127.0.0.1',port=27017)
# # 选择数据库
# mdb = client['train']
# # 选择表（集合）
# post = mdb["train_list"]
# s = set()
# len(s)
# for tm in trian_list.keys():
#     print(tm)
#     for xh in trian_list[tm].keys():
#         print(xh)
#         len(s)
#         # post.insert_many(trian_list[tm][xh])
#         for train in trian_list[tm][xh]:
#             ret = train['station_train_code']
#             ret = re.findall('\(([\s\S]*)\)', ret)
#             # print(ret[0])
#             s.add(ret[0])
#             # print(train['train_no'])
#             # post.insert(dict(train))
#             if post.find({'station_train_code':train['station_train_code']}).count()==0:
#                 post.insert(dict(train))
#
# print(len(s))
# for ss in s:
#
#     print(ss)