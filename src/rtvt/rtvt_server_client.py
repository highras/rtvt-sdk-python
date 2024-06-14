#encoding=utf8

import sys
sys.path.append("..")
import threading
import hashlib
from collections import deque
from fpnn.tcp_client import *
from fpnn.fpnn_client import *
from fpnn.quest import *
from .rtvt_quest_processor_internal import *
from .rtvt_quest_processor_internal_fpnn import *

class RTVTClient(object):

    def __init__(self, endpoint, pid, uid):
        arr = endpoint.split(":")

        if sys.platform == 'win32':
            self.client = FPNNTCPClient(arr[0], int(arr[1]), True, 5)
        else:
            self.client = TCPClient(arr[0], int(arr[1]))
            self.client.set_quest_timeout(5000)
            self.client.set_connect_timeout(1000)

        self.endpoint = endpoint
        self.pid = pid
        self.uid = uid
        self.require_close = False
        self.processor = None
        self.stream_lock = threading.Lock()
        self.stream_queue = {}
        self.stream_seq_map = {}

    def set_quest_timeout(self, timeout):
        self.client.set_quest_timeout(timeout * 1000)

    def set_connect_timeout(self, timeout):
        self.client.set_connect_timeout(timeout * 1000)

    def set_connection_callback(self, callback):
        self.connect_callback = callback

    def set_quest_processor(self, processor):
        if self.processor == None:
            if sys.platform == 'win32':
                self.processor = RTVTQuestProcessorInternalFPNN()
            else:
                self.processor = RTVTQuestProcessorInternal()
        self.processor.set_processor(processor)
        self.client.set_quest_processor(self.processor)

    def close(self):
        self.require_close = True
        self.client.close()

    def reconnect(self):
        self.client.reconnect()

    def delay_destory(self):
        time.sleep(1.5)
        self.require_close = True
        self.stop = True
        with self.stream_lock:
            self.stream_queue.clear()
            self.stream_seq_map.clear()
        if sys.platform != 'win32':
            self.client.destory()
        else:
            self.client.close()

    def destory(self):
        threading.Thread(target=self.delay_destory).start()

    def set_connection_callback(self, callback):
        if sys.platform == 'win32':

            class MyConnectedCallback(FpnnConnectedCallback):
                def __init__(self, endpoint, connection_id, connectionCallback):
                    self.endpoint = endpoint
                    self.connection_id = connection_id
                    self.connectionCallback = connectionCallback
                def callback(self):
                    self.connectionCallback.connected(self.connection_id, self.endpoint, True)

            class MyConnectionWillCloseCallback(FpnnConnectionWillCloseCallback):
                def __init__(self, endpoint, connection_id, connectionCallback):
                    self.endpoint = endpoint
                    self.connection_id = connection_id
                    self.connectionCallback = connectionCallback

                def callback(self, causedByError):
                    self.connectionCallback.closed(self.connection_id, self.endpoint, causedByError)

            self.client.setConnectionConnectedCallback(MyConnectedCallback(self.endpoint, self.client.connection_id, callback))
            self.client.setConnectionWillCloseCallback(MyConnectionWillCloseCallback(self.endpoint, self.client.connection_id, callback))
        else:
            self.client.set_connection_callback(callback)

    def login(self, token, ts):

        if sys.platform == 'win32':
            try:
                answer = self.client.sendQuestSync('login', {
                    'pid': self.pid, 'token': token,
                    'ts': ts, "uid": self.uid,
                    'version': "rtvt_python_sdk"
                })
                if ('successed' in answer):
                     return  answer['successed'] == True, 0
                return False, 0
            except Exception as ex:
                return False, 10001
        else:
            quest = Quest("login")
            quest.param("pid", self.pid)
            quest.param("token", token)
            quest.param("ts", ts)
            quest.param("uid", self.uid)
            quest.param("version", "rtvt_python_sdk")

            answer = self.client.send_quest(quest)

            if answer.is_error():
                return False, answer.error_code
            else:
                try:
                    successed = answer.want("successed")
                    return successed == True, 0
                except:
                    return False, 10001

    def create_stream(self, srcLang, destLang, needAsrResult, needTempResult, needTransResult, srcAltLanguage = []):
        if sys.platform == 'win32':
            try:
                params = {
                    'asrResult': needAsrResult, 'asrTempResult': needTempResult,
                    'transResult': needTransResult, "srcLanguage": srcLang,
                    'destLanguage': destLang
                }

                if len(srcAltLanguage) > 0:
                    params['srcAltLanguage'] = srcAltLanguage

                answer = self.client.sendQuestSync('voiceStart', params)

                streamId = 0
                if ('streamId' in answer):
                    streamId = answer['streamId']

                with self.stream_lock:
                    self.stream_queue[streamId] = deque()
                    self.stream_seq_map[streamId] = 1

                return streamId, 0
            
            except Exception as ex:
                return -1, 10001
        else:
            quest = Quest("voiceStart")
            quest.param("asrResult", needAsrResult)
            quest.param("asrTempResult", needTempResult)
            quest.param("transResult", needTransResult)
            quest.param("srcLanguage", srcLang)
            quest.param("destLanguage", destLang)

            if len(srcAltLanguage) > 0:
                quest.param("srcAltLanguage", srcAltLanguage)

            answer = self.client.send_quest(quest)

            if answer.is_error():
                return -1, answer.error_code
            else:
                try:
                    streamId = answer.want("streamId")

                    with self.stream_lock:
                        self.stream_queue[streamId] = deque()
                        self.stream_seq_map[streamId] = 1

                    return streamId, 0
                except:
                    return -1, 10001

    def close_stream(self, streamId):
        if sys.platform == 'win32':
            try:
                answer = self.client.sendQuestSync('voiceEnd', {'streamId': streamId})
                return 0
            except Exception as ex:
                return 10001
        else:
            quest = Quest("voiceEnd")
            quest.param("streamId", streamId)

            answer = self.client.send_quest(quest)

            if answer.is_error():
                return answer.error_code
            else:
                with self.stream_lock:
                    del self.stream_queue[streamId]
                    del self.stream_seq_map[streamId]
                return 0

    def send_voice(self, streamId, seq, data):
        if sys.platform == 'win32':
            try:
                answer = self.client.sendQuestSync('voiceData', {
                    'streamId': streamId,
                    'seq': seq,
                    'data': data,
                    'ts': int(time.time() * 1000)
                })
                return 0
            except Exception as ex:
                return 10001
        else:
            quest = Quest("voiceData")
            quest.param("streamId", streamId)
            quest.param("seq", seq)
            quest.param("data", data)
            quest.param("ts", int(time.time() * 1000))

            answer = self.client.send_quest(quest)

            if answer.is_error():
                return answer.error_code
            else:
                return 0

    def send_voice_async(self, streamId, seq, data):
        if sys.platform == 'win32':
            class MyQuestCallback(FpnnCallback):
                def callback(self, answer, exception):
                    pass

            self.client.sendQuest('voiceData', {
                'streamId': streamId,
                'seq': seq,
                'data': data,
                'ts': int(time.time() * 1000)
            }, MyQuestCallback())
        else:
            quest = Quest("voiceData")
            quest.param("streamId", streamId)
            quest.param("seq", seq)
            quest.param("data", data)
            quest.param("ts", int(time.time() * 1000))

            class MyCallback(QuestCallback):
                def callback(self, answer):
                    pass
            self.client.send_quest(quest, MyCallback())
            return 0

    def send_voice_variable(self, streamId, data):
        if isinstance(data, (bytes, bytearray)):
            with self.stream_lock:
                if streamId in self.stream_queue:
                    self.stream_queue[streamId].extend(data)
                    sendLength = int(len(self.stream_queue[streamId]) / 640)
                    if sendLength > 0:
                        for i in range(sendLength):
                            data = bytes([self.stream_queue[streamId].popleft() for _ in range(640)])
                            self.send_voice_async(streamId, self.stream_seq_map[streamId], data)
                            self.stream_seq_map[streamId] += 1
            return 0
        else:
            raise ValueError("data must be bytes or bytearray.")

