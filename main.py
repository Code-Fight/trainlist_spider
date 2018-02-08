from scrapy import cmdline

if __name__=="__main__":
    try:
        print("Start...")
        cmdline.execute("scrapy crawl train".split())

    except BaseException as e:
        print(e)
        pass
    finally:
        print('Done...')

