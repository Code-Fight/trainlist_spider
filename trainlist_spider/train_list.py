import json
import re
import pymongo
import sys
import io

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
fh =  open('/Users/zhangfeng/Downloads/train_list.js',encoding='UTF-8')
txt = fh.read()
txt = txt.replace("var",'')
txt = txt.replace("train_list",'')
txt = txt.replace("=",'')
txt = txt.replace(" ",'')
fh.close()
trian_list = json.loads(txt)
client = pymongo.MongoClient(host='127.0.0.1',port=27017)
# 选择数据库
mdb = client['train']
# 选择表（集合）
post = mdb["train_list"]
s = set()
len(s)
for tm in trian_list.keys():
    print(tm)
    for xh in trian_list[tm].keys():
        print(xh)
        len(s)
        # post.insert_many(trian_list[tm][xh])
        for train in trian_list[tm][xh]:
            ret = train['station_train_code']
            ret = re.findall('\(([\s\S]*)\)', ret)
            # print(ret[0])
            s.add(ret[0])
            # print(train['train_no'])
            # post.insert(dict(train))
            if post.find({'station_train_code':train['station_train_code']}).count()==0:
                post.insert(dict(train))

print(len(s))
for ss in s:

    print(ss)