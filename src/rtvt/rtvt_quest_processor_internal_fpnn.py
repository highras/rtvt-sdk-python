# encoding=utf8

import sys
sys.path.append("..")
import time
from fpnn import *

class RTVTQuestProcessorInternalFPNN(QuestProcessor):
    def __init__(self):
        QuestProcessor.__init__(self)
        self.processor = None

    def set_processor(self, processor):
        self.processor = processor

    def recognizedResult(self, params):
        try:
            self.processor.recognized_result(params)
        except:
            pass

    def recognizedTempResult(self, params):
        try:
            self.processor.recognized_temp_result(params)
        except:
            pass
    
    def translatedResult(self, params):
        try:
            self.processor.translated_result(params)
        except:
            pass
    
    def translatedTempResult(self, params):
        try:
            self.processor.translated_temp_result(params)
        except:
            pass

