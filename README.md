# RTVT Python SDK

[TOC]

## Depends

* Python 3+
* selectors
* msgpack
* cryptography

## Usage

```python
#encoding=utf8
import sys
sys.path.append("/path/to/sdk")
import time
from rtvt import *

import base64
from Cryptodome.Hash import HMAC, SHA256

# 创建RTVTClient， endpoint、pid从网站控制台获取
client = RTVTClient(ENDPOINT, PID, UID)

# 自定义链接状态监控回调，可用实现重连等操作
class MyConnectionCallback(ConnectionCallback):
    # 连接建立时触发
    def connected(self, connection_id, endpoint, connected):
        print(f"connected result: {connected}, endpoint: {endpoint}, connection_id: {connection_id}")
    
    # 连接断开时触发
    def closed(self, connection_id, endpoint, caused_by_error):
        print(f"closed, endpoint: {endpoint}, connection_id: {connection_id}, caused_by_error: {caused_by_error}")

# 向client注册链接监控回调
client.set_connection_callback(MyConnectionCallback())

# 自定义结果通知回调
class ResultProcessor(RTVTServerPushMonitor):
    def __init__(self):
        RTVTServerPushMonitor.__init__(self)

    # 识别最终结果, data格式示例：
    # {'pid': 81700001, 'streamId': 4046519136031866897, 'startTs': 1713354552804, 'endTs': 1713354552824, 'recTs': 1713354555384, 'lang': 'zh', 'taskId': 3, 'asr': '我想作为大家的朋友，'}
    def recognized_result(self, data):
        print(f"识别最终结果: {data}")
    
    # 识别临时结果, data格式示例：
    # {'pid': 81700001, 'streamId': 4046519131736899600, 'startTs': 1713354431399, 'endTs': 1713354431419, 'recTs': 1713354434309, 'lang': 'zh', 'asr': '今天晚上'}
    def recognized_temp_result(self, data):
        print(f"识别临时结果: {data}")
    
    # 翻译最终结果, data格式示例：
    # {'pid': 81700001, 'streamId': 4046519136031866897, 'startTs': 1713354552804, 'endTs': 1713354552824, 'trans': "I want to be everyone's friend,", 'recTs': 1713354555384, 'lang': 'en', 'taskId': 3}
    def translated_result(self, data):
        print(f"翻译最终结果: {data}")
    
    # 翻译临时结果, data格式示例：
    # {'pid': 81700001, 'streamId': 4046519136031866897, 'startTs': 1713354525821, 'endTs': 1713354525841, 'trans': 'Tonight', 'recTs': 1713354528652, 'lang': 'en'}
    def translated_temp_result(self, data):
        print(f"翻译临时结果: {data}")

# 向client注册结果通知回调
client.set_quest_processor(ResultProcessor())

# 鉴权token生成示例，pid与key从网站控制台获取
pid = 81700001
key = 'xxxxxxx'
ts = int(time.time())

core_string = f"{pid}:{ts}"
decoded_key = base64.b64decode(key)
hmac_sha256 = HMAC.new(decoded_key, core_string.encode('utf-8'), SHA256).digest()
token = base64.b64encode(hmac_sha256).decode('utf-8')

# 登录，当登录成功时，successed = True，errorCode = 0，失败时successed = False，errorCode为具体错误码
successed, errorCode = client.login(token, ts)

# 创建流，参数原型：create_stream(srcLang, destLang, needAsrResult, needTempResult, needTransResult, srcAltLanguage = [])
# srcLang: 音频源语言
# destLang: 翻译目标语言
# needAsrResult: 是否需要识别最终结果
# needTransResult: 是否需要翻译最终结果
# needTempResult: 是否需要临时结果（识别与翻译）
# srcAltLanguage: 音频候选语种（可选）
streamId, errorCode = client.create_stream("zh", "en", True, True, True)

# 发送音频流, streamId为create_stream返回的结果，seq为业务自己维护的自增id，data为二进制pcm数据片段
# pcm片段要求为16000采样率 单声道 固定640字节
errorCode = client.send_voice(streamId, seq, data)

# 异步方式不等待确认结果
errorCode = client.send_voice_async(streamId, seq, data)

# 该接口不要求输入pcm片段是640字节，可传递变长音频数据
client.send_voice_variable(streamId, data)

# 关闭流
client.close_stream(streamId)

# 销毁相关资源
client.destory()
```

## Demo

[test/demo.py](test/demo.py)
