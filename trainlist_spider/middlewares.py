# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import requests
from scrapy.downloadermiddlewares.retry import *
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import random
import time
import datetime
import json


class TrainlistSpiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

class TrainlistSpiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class LocalRetryMiddlewares(RetryMiddleware):
    '''
    重试中间件
    '''
    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        # if response.status in self.retry_http_codes:
        #     reason = response_status_message(response.status)
        #     return self._retry(request, reason, spider) or response
        if 'dataloss' in response.flags:
            return self._retry(request, 'Got Data Los', spider) or response



        if int(response.status) != 200:
            # reason = response_status_message(response.status)
            return self._retry(request, '非200返回', spider) or response

        # 自定义 retry机制
        ret = response.body
        if type(response.body) != bytes:
            ret = ret.decode('utf-8')
            if "网络" in ret:
                print('retryed :' + request.url)
                # self.log('retryed :' + request.url)
                return self._retry(request,'网络302',spider) or response

        if len(ret) == 0:
            return self._retry(request, '超时', spider) or response

        # if "200" not in ret:
        #     return self._retry(request, '获取数据失败', spider) or response


        if 'purpose_codes=ADULT' in request.url:
            # 车次列表
            json_ret = json.loads(ret)
            if len(json_ret['data']['result']) <= 0:
                request.meta['retry_times'] = request.meta.get('retry_times', 0) + 1
                return self._retry(request, 'maybe baned！', spider) or response
        elif 'train_no' in  request.url :
            # 途径站信息
            json_ret = json.loads(ret)
            try:

                # 如果取结果的时候 出现该问题 说明 12306抽风了
                if str(ret).find('验证码错误') :
                    return response

                # 检测 ret是否存在data   然后判断第一层data是否存在数据 然后 再看第二层data
                if str(ret).find('data') == -1 or \
                        json_ret['data'] == None or \
                        json_ret['data']['data'] == None or \
                        len(json_ret['data']['data']) == 0:
                    request.meta['retry_times'] = request.meta.get('retry_times', 0) + 1
                    return self._retry(request, 'maybe baned！', spider) or response
            except Exception as e:
                print(ret)








        return response

    # 改写重试机制
    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0)

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        # if retries <= retry_times:
        retryreq = request.copy()
        if retries > 10:
            logger.debug("超过10次 :"+str(request.url))
            retryreq.meta['retry_times'] = 0
            return None

        logger.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                     {'request': request, 'retries': retries, 'reason': reason},
                     extra={'spider': spider})


        retryreq.meta['retry_times'] = retries
        retryreq.dont_filter = True
        retryreq.priority = request.priority + self.priority_adjust

        if isinstance(reason, Exception):
            reason = global_object_name(reason.__class__)

        stats.inc_value('retry/count')
        stats.inc_value('retry/reason_count/%s' % reason)
        # print("retrying.."+str(retry_times))

        return retryreq
    # #     # else:
        #     stats.inc_value('retry/max_reached')
        #     logger.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
        #                  {'request': request, 'retries': retries, 'reason': reason},
        #                  extra={'spider': spider})


class MyUserAgentMiddleware(UserAgentMiddleware):
    '''
    随机 User-Agent 中间件
    '''

    def __init__(self, user_agent):
        self.user_agent = user_agent

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent=crawler.settings.get('MY_USER_AGENT')
        )

    def process_request(self, request, spider):

        agent = random.choice(self.user_agent)
        request.headers['User-Agent'] = agent
        logger.debug(request.headers['User-Agent'])


class MyProxyMiddlewareddd(object):
    '''
    设置 Proxy 中间件
    '''

    def __init__(self, ip, port, expire_time):
        self.proxy ={}
        self.proxy['ip'] = ip
        self.proxy['port'] = port
        self.proxy['expire_time'] = expire_time

    @classmethod
    def from_crawler(cls, crawler):

        return cls(
            ip = '',
            port = '',
            expire_time = datetime.datetime(2013, 8, 10, 10, 56, 10, 611490)
            # 用过去的一个时间来初始化
        )

    def process_request(self, request, spider):


        timeout_tims = 0
        exception_tims = 0

        # 如果当前剩余时间 小于 当前时间  代表ip过期 那么需要重新获取一个新的ip
        while  ((self.proxy['expire_time'] - datetime.timedelta(seconds=30)) < datetime.datetime.now()):

            # 获取新的ip地址
            free_url = 'http://webapi.http.zhimacangku.com/getip?num=1&type=2&pro=0&city=0&yys=0&port=1&pack=15345&ts=1&ys=0&cs=0&lb=1&sb=0&pb=45&mr=1&regions='
            url = "http://webapi.http.zhimacangku.com/getip?num=1&type=2&pro=0&city=0&yys=0&port=1&time=1&ts=1&ys=0&cs=0&lb=1&sb=0&pb=45&mr=1&regions="
            ret = requests.get(free_url)
            ret_json =ret.json()

            if not ret_json['success']:
                continue



            proxies = {'http': 'http://'+str(ret_json['data'][0]['ip'])+':'+str(ret_json['data'][0]['port']),
                       'https': 'http://'+str(ret_json['data'][0]['ip'])+':'+str(ret_json['data'][0]['port'])}
            url = "http://2018.ip138.com/ic.asp"

            try:
                re = requests.get(url, proxies=proxies, timeout=10)
                if ret_json['data'][0]['ip'] in re.text:
                    # 成功得到ip地址
                    self.proxy['ip'] = ret_json['data'][0]['ip']
                    self.proxy['port'] = ret_json['data'][0]['port']
                    self.proxy['expire_time'] = datetime.datetime.strptime(ret_json['data'][0]['expire_time'],'%Y-%m-%d %H:%M:%S')
                    break
            except requests.exceptions.ConnectTimeout:
                timeout_tims +=1

            except BaseException:
                exception_tims +=1

            if exception_tims > 5:
                logger.error("获取代理错误 %s 次"%(exception_tims))
                time.sleep(5)

            time.sleep(2)

        request.meta["proxy"] = "http://" + str(self.proxy['ip']) +":"+ str(self.proxy['port'])

