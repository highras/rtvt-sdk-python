#encoding=utf8

import sys
sys.path.append("..")
import threading
import hashlib
from collections import deque
from fpnn.tcp_client import *
from fpnn.quest import *
from .rtvt_quest_processor_internal import *

class RTVTClient(object):

    def __init__(self, endpoint, pid, uid):
        arr = endpoint.split(":")
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
            self.processor = RTVTQuestProcessorInternal()
        self.processor.set_processor(processor)
        self.client.set_quest_processor(self.processor)

    def close(self):
        self.require_close = True
        self.client.close()

    def reconnect(self):
        self.client.reconnect()

    def destory(self):
        self.require_close = True
        self.stop = True
        with self.stream_lock:
            self.stream_queue.clear()
            self.stream_seq_map.clear()
        self.client.destory()

    def set_connection_callback(self, callback):
        self.client.set_connection_callback(callback)

    def login(self, token, ts):
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

