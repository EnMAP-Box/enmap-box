from typing import TextIO

from qgis.core import QgsProcessingFeedback
from typeguard import typechecked


@typechecked
class ProcessingFeedback(QgsProcessingFeedback):

    def __init__(self,
                 feedback: QgsProcessingFeedback, pushInfo=True, pushWarning=True, pushDebugInfo=True,
                 pushConsoleInfo=True,
                 pushCommandInfo=True, pushVersionInfo=True, setProgress=True, silenced=False, logfile: TextIO = None,
                 isChildFeedback=False
                 ):
        super().__init__()
        self.feedback = feedback
        self._pushInfo = pushInfo and not silenced
        self._pushWarning = pushWarning and not silenced
        self._pushDebugInfo = pushDebugInfo and not silenced
        self._pushConsoleInfo = pushConsoleInfo and not silenced
        self._pushCommandInfo = pushCommandInfo and not silenced
        self._pushVersionInfo = pushVersionInfo and not silenced
        self._setProgress = setProgress
        if isinstance(feedback, ProcessingFeedback):
            self._pushInfo &= feedback._pushInfo
            self._pushDebugInfo &= feedback._pushDebugInfo
            self._pushConsoleInfo &= feedback._pushConsoleInfo
            self._pushCommandInfo &= feedback._pushCommandInfo
            self._pushVersionInfo &= feedback._pushVersionInfo
            self._setProgress &= feedback._setProgress
        self._logfile = logfile
        self._isChildFeedback = isChildFeedback

    def getQgsFeedback(self):
        if isinstance(self.feedback, ProcessingFeedback):
            return self.feedback.getQgsFeedback()
        return self.feedback

    def isCanceled(self):
        return super().isCanceled()

    def pushInfo(self, info):
        if self._pushInfo:
            info = str(info)
            self.feedback.pushInfo(info)
            self.log(info)
        else:
            pass  # silence

    def pushWarning(self, warning):
        if self._pushWarning:
            warning = str(warning)
            self.feedback.pushWarning(warning)
            self.log(warning)
        else:
            pass  # silence

    def pushDebugInfo(self, info):
        if self._pushDebugInfo:
            self.feedback.pushDebugInfo(info)
            self.log(info)
        else:
            pass  # silence

    def pushConsoleInfo(self, info):
        if self._pushConsoleInfo:
            self.feedback.pushConsoleInfo(info)
            self.log(info)
        else:
            pass  # silence

    def pushCommandInfo(self, info):
        if self._pushCommandInfo:
            self.feedback.pushCommandInfo(info)
            self.log(info)
        else:
            pass  # silence

    def pushVersionInfo(self, provider):
        raise NotImplementedError()

    def setProgress(self, progress):
        if self._setProgress:
            self.feedback.setProgress(progress)
        else:
            pass  # silence

    def pushTiming(self, seconds: float):
        if not self._isChildFeedback:
            self.pushInfo(f'Execution completed in {round(seconds, 2)} seconds')

    def log(self, info: str):
        if self._logfile is not None:
            print(info, file=self._logfile)
