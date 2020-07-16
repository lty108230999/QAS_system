import json
import timeout_decorator
from wechatpy.replies import ArticlesReply
from wechatpy.utils import check_signature
from wechatpy.crypto import WeChatCrypto
from wechatpy import parse_message, create_reply
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException

# 是否开启本地debug模式
debug = False

# 腾讯云对象存储依赖
if debug:
    from qcloud_cos import CosConfig
    from qcloud_cos import CosS3Client
    from qcloud_cos import CosServiceError
    from qcloud_cos import CosClientError
else:
    from qcloud_cos_v5 import CosConfig
    from qcloud_cos_v5 import CosS3Client
    from qcloud_cos_v5 import CosServiceError
    from qcloud_cos_v5 import CosClientError
    
# 配置存储桶
appid = '1302540728'
secret_id = u'AKIDGHe5OYvs7NL2UhuH6MM1PYQwBAqFtuJT'
secret_key = u'QQ9ajYDbjZopZ4NmtjIgqlQtBDxKzY2J'
region = u'ap-chongqing'
bucket = 'name'+'-'+appid

# 对象存储实例
config = CosConfig(Secret_id=secret_id, Secret_key=secret_key, Region=region)
client = CosS3Client(config)

# cos 文件读写
def cosRead(key):
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        txtBytes = response['Body'].get_raw_stream()
        return txtBytes.read().decode()
    except CosServiceError as e:
        return ""

def cosWrite(key, txt):
    try:
        response = client.put_object(
            Bucket=bucket,
            Body=txt.encode(encoding="utf-8"),
            Key=key,
        )
        return True
    except CosServiceError as e:
        return False

def getReplys():
    replyMap = {}
    replyTxt = cosRead('Replys.txt')  # 读取数据
    if len(replyTxt) > 0:
        replyMap = json.loads(replyTxt)
    return replyMap

def addReplys(reply):
    replyMap = getReplys()
    if len(replyMap) > 0:
        replyMap[reply]='我是黑名单'
    return cosWrite('Replys.txt', json.dumps(replyMap, ensure_ascii=False)) if len(replyMap) > 0 else False


def delReplys(reply):
    replyMap = getReplys()
    if len(replyMap) > 0:
        replyMap.pop(reply)
    return cosWrite('Replys.txt', json.dumps(replyMap, ensure_ascii=False)) if len(replyMap) > 0 else False


# 微信公众号对接
wecaht_id = 'wx6183e8cd3263eb02'
WECHAT_TOKEN = 'lty108230999'
encoding_aes_key = 'JOEINtb2xKS0RG5XOsHRVXukar0Oi6MhqxhPGtjUe6v'

crypto = WeChatCrypto(WECHAT_TOKEN, encoding_aes_key, wecaht_id)

# api网关响应集成
def apiReply(reply, txt=False, content_type='application/json', code=200):
    return {
        "isBase64Encoded": False,
        "statusCode": code,
        "headers": {'Content-Type': content_type},
        "body": json.dumps(reply, ensure_ascii=False) if not txt else str(reply)
    }

def replyMessage(msg):
    txt = msg.content
    ip = msg.source
    print('请求信息--->'+ip+'%'+txt)  # 用来在腾讯云控制台打印请求日志
    replysTxtMap = getReplys() # 获取回复关键词
    if '@' in txt:
        keys = txt.split('@')
        if keys[0] == '电影': #do something
            return
        if keys[0] == '音乐': #do something
            return
        if keys[0] == '下架': #do something
            return
        if keys[0] == '上架': #do something
            return
        if keys[0] == '回复': #do something
            return
        if keys[0] == '删除': #do something
            return
    elif txt in replysTxtMap.keys(): # 如果消息在回复关键词内则自动回复
        return create_reply(replysTxtMap[txt], msg)
    return create_reply("喵呜 ฅ'ω'ฅ", msg)

def wechat(httpMethod, requestParameters, body=''):
    if httpMethod == 'GET':
        signature = requestParameters['signature']
        timestamp = requestParameters['timestamp']
        nonce = requestParameters['nonce']
        echo_str = requestParameters['echostr']
        try:
            check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
        except InvalidSignatureException:
            echo_str = 'error'
        return apiReply(echo_str, txt=True, content_type="text/plain")
    elif httpMethod == 'POST':
        msg_signature = requestParameters['msg_signature']
        timestamp = requestParameters['timestamp']
        nonce = requestParameters['nonce']
        try:
            decrypted_xml = crypto.decrypt_message(
                body,
                msg_signature,
                timestamp,
                nonce
            )
        except (InvalidAppIdException, InvalidSignatureException):
            return
        msg = parse_message(decrypted_xml)
        if msg.type == 'text':
            reply = replyMessage(msg)
        elif msg.type == 'image':
            reply = create_reply('哈◔ ‸◔？\n好端端的，给我发图片干啥~', msg)
        elif msg.type == 'voice':
            reply = create_reply('哈◔ ‸◔？\n好端端的，给我发语音干啥~', msg)
        else:
            reply = create_reply('哈◔ ‸◔？\n搞不明白你给我发了啥~', msg)
        reply = reply.render()
        print('返回结果--->'+str(reply))  # 用来在腾讯云控制台打印请求日志
        reply = crypto.encrypt_message(reply, nonce, timestamp)
        return apiReply(reply, txt=True, content_type="application/xml")
    else:
        msg = parse_message(body)
        reply = create_reply("喵呜 ฅ'ω'ฅ", msg)
        reply = reply.render()
        print('返回结果--->'+str(reply))  # 用来在腾讯云控制台打印请求日志
        reply = crypto.encrypt_message(reply, nonce, timestamp)
        return apiReply(reply, txt=True, content_type="application/xml")


@timeout_decorator.timeout(4, timeout_exception=StopIteration)
def myMain(httpMethod, requestParameters, body=''):
    return wechat(httpMethod, requestParameters, body=body)


def timeOutReply(httpMethod, requestParameters, body=''):
    msg_signature = requestParameters['msg_signature']
    timestamp = requestParameters['timestamp']
    nonce = requestParameters['nonce']
    try:
        decrypted_xml = crypto.decrypt_message(
            body,
            msg_signature,
            timestamp,
            nonce
        )
    except (InvalidAppIdException, InvalidSignatureException):
        return
    msg = parse_message(decrypted_xml)
    reply = create_reply("出了点小问题，请稍后再试", msg).render()
    print('返回结果--->'+str(reply))  # 用来在腾讯云控制台打印请求日志
    reply = crypto.encrypt_message(reply, nonce, timestamp)
    return apiReply(reply, txt=True, content_type="application/xml")


def main_handler(event, context):
    body = ''
    httpMethod = event["httpMethod"]
    requestParameters = event['queryString']
    if 'body' in event.keys():
        body = event['body']
    try:
        response = myMain(httpMethod, requestParameters, body=body)
    except:
        response = timeOutReply(httpMethod, requestParameters, body=body)
        print(response)
    return response