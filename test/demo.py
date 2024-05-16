#encoding=utf8
import sys
sys.path.append("../src")
import time
from rtvt import *

import base64
from Cryptodome.Hash import HMAC, SHA256

if  __name__ == "__main__":

    client = RTVTClient("rtvt.ilivedata.com:14001", 81700001, 123456)

    class MyConnectionCallback(ConnectionCallback):
        def connected(self, connection_id, endpoint, connected):
            print(f"connected result: {connected}, endpoint: {endpoint}, connection_id: {connection_id}")
        
        def closed(self, connection_id, endpoint, caused_by_error):
            print(f"closed, endpoint: {endpoint}, connection_id: {connection_id}, caused_by_error: {caused_by_error}")

    client.set_connection_callback(MyConnectionCallback())

    class ResultProcessor(RTVTServerPushMonitor):
        def __init__(self):
            RTVTServerPushMonitor.__init__(self)

        def recognized_result(self, data):
            print(f"识别最终结果: {data}")
        
        def recognized_temp_result(self, data):
            print(f"识别临时结果: {data}")
        
        def translated_result(self, data):
            print(f"翻译最终结果: {data}")
        
        def translated_temp_result(self, data):
            print(f"翻译临时结果: {data}")

    client.set_quest_processor(ResultProcessor())

    pid = 81700001
    key = 'xxxxxxxxx'
    ts = int(time.time())

    core_string = f"{pid}:{ts}"
    decoded_key = base64.b64decode(key)
    hmac_sha256 = HMAC.new(decoded_key, core_string.encode('utf-8'), SHA256).digest()
    token = base64.b64encode(hmac_sha256).decode('utf-8')

    successed, errorCode = client.login(token, ts)
    
    print(successed)
    print(errorCode)


    streamId, errorCode = client.create_stream("zh", "en", True, True, True)

    print(streamId)
    print(errorCode)

    # 设置每次读取的字节数
    chunk_size = 320
    # WAV文件头部大小，通常是44字节
    wav_header_size = 44

    seq = 0
    with open('guailing.wav', 'rb') as file:
        # 跳过头部
        file.seek(wav_header_size)

        while True:
            # 读取固定大小的数据块
            chunk = file.read(chunk_size)
            
            # 如果没有读取到数据，说明已到达文件末尾
            if not chunk:
                break
            
            # 如果读取的数据块小于640字节，用0填充剩余的部分
            if len(chunk) < chunk_size:
                chunk += bytes(chunk_size - len(chunk))

            client.send_voice_variable(streamId, chunk)

            seq += 1
            
            time.sleep(0.01)

    print("识别完成")
    time.sleep(10)

    client.close_stream(streamId)
    client.destory()



