# encoding=utf8

import sys
sys.path.append("..")
import time
from fpnn import *

class RTVTQuestProcessorInternal(QuestProcessor):
    def __init__(self):
        QuestProcessor.__init__(self)
        self.processor = None

    def set_processor(self, processor):
        self.processor = processor

    def recognizedResult(self, connection, quest):
        connection.send_answer(Answer())
        try:
            self.processor.recognized_result(quest.params_map)
        except:
            pass
    
    def recognizedTempResult(self, connection, quest):
        connection.send_answer(Answer())
        try:
            self.processor.recognized_temp_result(quest.params_map)
        except:
            pass
    
    def translatedResult(self, connection, quest):
        connection.send_answer(Answer())
        try:
            self.processor.translated_result(quest.params_map)
        except:
            pass
    
    def translatedTempResult(self, connection, quest):
        connection.send_answer(Answer())
        try:
            self.processor.translated_temp_result(quest.params_map)
        except:
            pass

