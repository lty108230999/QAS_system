from flask import Flask, request, make_response
import hashlib
import xml.etree.ElementTree as ET
import time
import gensim
import jieba
import numpy as np
from scipy.linalg import norm
import re
import xlrd


app = Flask(__name__)
app.debug = True



model_file = 'cut.model'
model = gensim.models.Word2Vec.load(model_file)
#model = gensim.models.KeyedVectors.load_word2vec_format(model_file, binary=False,unicode_errors='ignore')

tfidf = open('tfidf.txt','r',encoding = 'utf-8').readlines()
tfidf_dict = {}
for i in tfidf:
    i = i.strip().split('\t')
    tfidf_dict[i[0]] = float(i[1])
    
adding_list = ['AR','APP','2D','3D','CMS','视网么']
for i in adding_list:
    jieba.add_word(i)
            
def turning(ques):
    turning_list = [['增强现实','AR'],['如何','怎么','怎样'],['流程','步骤','方法'],['创建','新建'],['内容管理系统','CMS']]
    for i in turning_list:
        for k in i:
            if k in ques:
                ques = re.sub(k,i[0],ques)
    return ques

def jaccard(s_max,question):
    s_dict = [x for x in s_max if x != '吗']
    q_dict = [x for x in question if x != '吗']
    count = 0
    for i in s_dict:
        if i in q_dict:
            count += 1
    s_dict.extend(q_dict)
    length = len(set(s_dict))
    j = count/length
    return j         

def sentence_similarity(s1,s2,tfidf_dict):
    def sentence_vector(s):
        stopwords = open('stop_word.txt','r',encoding = 'utf-8').read()
        stop_words = [word for word in stopwords if word != '\n']
        words = jieba.lcut(s)
        words = [x for x in words if x not in stop_words]
        v = np.zeros(64)
        for word in words:
            try:
                v += model[word]
            except:
                  pass
        v /= len(words)
        return v
    v1,v2 = sentence_vector(s1),sentence_vector(s2)
    return np.dot(v1,v2)/(norm(v1) * norm(v2))
def ques_read(f):
    wb = xlrd.open_workbook(filename = f)
    sheet1 = wb.sheet_by_index(0)
    ques = sheet1.col_values(0)
    answ = sheet1.col_values(1)
    token = sheet1.col_values(2)
    media_id = sheet1.col_values(3)
    return ques,answ,token,media_id

f = 'test1.xlsx'
ques,answ,token,media_id = ques_read(f)

@app.route('/robot/', methods=['GET'])
# route() 装饰器用于把一个函数绑定到一个 URL
# 在微信公众号修改配置那里，如果你写的是“/wechat/”在括号里，就要在二级域名后面加上，不然就会出现token验证失败的一种情况！
def wechat_tuling():
    if request.method == 'GET':
        print('接受到信息')
        my_signature = request.args.get('signature', '') # 获取携带 signature微信加密签名的参数
        my_timestamp = request.args.get('timestamp', '') # 获取携带随机数timestamp的参
        my_nonce = request.args.get('nonce', '')   # 获取携带时间戳nonce的参数
        my_echostr = request.args.get('echostr', '')  # 获取携带随机字符串echostr的参数
        token = 'lty108230999'
        # 这里输入你要在微信公众号里面填的token，保持一致
        data = [token, my_timestamp, my_nonce]
        data.sort()
        # 进行字典排序
        temp = ''.join(data)
        # 拼接成字符串
        mysignature = hashlib.sha1(temp.encode('utf-8')).hexdigest()
        # # 判断请求来源，将三个参数字符串拼接成一个字符串进行sha1加密,记得转换为utf-8格式
        if my_signature == mysignature:
            # 开发者获得加密后的字符串可与signature对比，标识该请求来源于微信
            return make_response(my_echostr)
        else:
            return ''
@app.route('/robot/', methods=['POST'])
def autoplay():
    print('接受到信息，开始解析')
    xml = ET.fromstring(request.data)
    # 获取用户发送的原始数据
    # fromstring()就是解析xml的函数，然后通过标签进行find()，即可得到标记内的内容。
    fromUser = xml.find('FromUserName').text
    toUser = xml.find('ToUserName').text
    msgType = xml.find("MsgType").text
    createTime = xml.find("CreateTime")
    content = xml.find('Content').text
    print('解析完毕，内容为'+content)
    xml_text = '''
                <xml>
                <ToUserName><![CDATA[%s]]></ToUserName>
                <FromUserName><![CDATA[%s]]></FromUserName>
                <CreateTime>123456</CreateTime>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA[%s]]></Content>
                </xml>'''
    xml_image = '''
                <xml>
              <ToUserName><![CDATA[%s]]></ToUserName>
              <FromUserName><![CDATA[%s]]></FromUserName>
              <CreateTime>12345678</CreateTime>
              <MsgType><![CDATA[image]]></MsgType>
              <Image>
                <MediaId><![CDATA[%s]]></MediaId>
              </Image>
            </xml>'''
    xml_article = '''
                <xml>
              <ToUserName><![CDATA[%s]]></ToUserName>
              <FromUserName><![CDATA[%s]]></FromUserName>
              <CreateTime>12345678</CreateTime>
              <MsgType><![CDATA[news]]></MsgType>
              <ArticleCount>1</ArticleCount>
              <Articles>
                <item>
                  <Title><![CDATA[%s]]></Title>
                  <Description><![CDATA[%s]]></Description>
                  <PicUrl><![CDATA[%s]]></PicUrl>
                  <Url><![CDATA[%s]]></Url>
                </item>
              </Articles>
            </xml>'''
    # 返回数据包xml的文本回复格式
    if msgType == 'text':
        starttime = time.time()
        question = turning(content)
        s = {}
        ss = {}
        lib = {}
        lib_qt = {}
        lib_qm = {}
        s_max = ''
        for i in range(0,len(ques)):
            lib_qt[ques[i]] = int(token[i])
        for i in range(0,len(ques)):
            lib_qm[ques[i]] = media_id[i]   
        for i in range(0,len(ques)):
            lib[ques[i]] = answ[i]
        print(len(lib_qt),len(lib_qm),len(ques))
        text = [x.strip() for x in ques if len(x)>2]
        if question in lib:
            s_max = question
            answer = lib[question]
        else:
            for i in text:
                similarity = sentence_similarity(i,question,tfidf_dict)
                s[i] = similarity
            print(s)
            s_max = max(s,key = s.get)
        print(s_max)
        for i in range(0,10):
            if jaccard(s_max,question) == 0:
                del s[s_max]
                s_max = max(s,key = s.get)
            else:
                try:
                    ss[s_max] = s[s_max]+jaccard(s_max,question)
                except:
                    ss[s_max] = 1.5
        s_max = max(ss,key = ss.get)
        endtime = time.time()
        print('总共的时间为:', round(endtime - starttime, 2),'secs')
        print('问题：'+question)
        print('-------------------------------------')
        if lib_qt[s_max] == 1:
            answer = lib_qm[s_max]
            res = make_response(xml_image % (fromUser, toUser, answer))
        elif lib_qt[s_max] == 2:
            answer = lib[s_max]
            img = lib_qm[s_max].split(' ')[0]
            url = lib_qm[s_max].split(' ')[1]
            res = make_response(xml_article % (fromUser, toUser,s_max ,answer,img,url))
        else:
            answer = lib[s_max]
            res = make_response(xml_text % (fromUser, toUser, answer))
        res.content_type = 'application/xml'
        return res
        # 输出自动回复


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5050)   
    # 加上host这段，就可以在浏览器访问你的网址, 新浪SAE需要指定5050端口
