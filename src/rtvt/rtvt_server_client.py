#encoding=utf8

import sys
sys.path.append("..")
import threading
import hashlib
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







