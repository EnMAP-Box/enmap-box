from __future__ import print_function
import sys

class ProgressBar(object):
    def setPercentage(self, percentage): pass
    def setText(self, text): pass

class SilentProgressBar(ProgressBar):
    pass

class CUIProgressBar(ProgressBar):
    SILENT = True
    def setPercentage(self, percentage):
        if self.SILENT:
            return
        percentage = int(percentage)
        if percentage == 100:
            print('100%')
        else:
            print('{}%..'.format(percentage), end='')
        try:
            sys.stdout.flush()
        except:
            pass

    def setText(self, text):
        if self.SILENT:
            return

        print(text)
        try:
            sys.stdout.flush()
        except:
            pass
