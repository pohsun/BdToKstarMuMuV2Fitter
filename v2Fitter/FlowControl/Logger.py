#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : MessageLogger service
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 20 Feb 2019 19:25 00:10

from v2Fitter.FlowControl.Service import Service

import os
from enum import IntEnum
from functools import partial
from datetime import datetime

class VerbosityLevels(IntEnum):
    """Verbosity levels for message logger."""
    DEBUG = 999
    INFO = 0
    WARNING = -1
    ERROR = -2
    SILENT = -999

    DEFAULT = 0

class partialmethod(partial):
    """Stolen from https://gist.github.com/carymrobbins/8940382"""
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(self.func, instance, *(self.args or ()), **(self.keywords or {}))

class Logger(Service):
    """A message logger."""
    def __init__(self, logfilename=None, verbosityLevel=VerbosityLevels.DEFAULT):
        Service.__init__(self)
        if logfilename is None:
            self._logmethod = self.logPrint
        else:
            self._logmethod = self.logWrite
            self._logfilename = logfilename
        self.verbosityLevel = verbosityLevel

    def __del__(self):
        if hasattr(self, "_logfile"):
            self._logfile.close()

    def _compileMsg(self, msg, lv):
        """Compose message"""
        return "{time} {vlevel}\t: {msg}\n".format(time=datetime.utcnow().strftime("UTC %Y%m%d %H:%M:%S"), vlevel=lv.name, msg=msg)

    def setAbsLogfileDir(self, dirname):
        """ In case you want to specify the directory """
        if os.path.isabs(dirname):
            self.dirname = dirname

    def logPrint(self, msg, lv):
        """Print to stdout"""
        print(self._compileMsg(msg, lv))

    def logWrite(self, msg, lv):
        """Write down a log"""
        if not hasattr(self, "_logfile"):
            if hasattr(self, 'filedir'):
                if not os.path.isdir(self.filedir):
                    os.mkdir(self.filedir)
                self._logfile = open(os.path.join(self.filedir, self._logfilename), 'w+')
            else:
                self._logfile = open(self._logfilename, 'w+')
            self._logfile.write(self._compileMsg("New process spawned.", lv))
        self._logfile.write(self._compileMsg(msg, lv))

    def _logDefine(self, msg, lv):
        """Define a function to keep a log at given level"""
        if self.verbosityLevel >= lv:
            self._logmethod(msg, lv)

    logINFO = partialmethod(_logDefine, lv=VerbosityLevels.INFO)
    logWARNING = partialmethod(_logDefine, lv=VerbosityLevels.WARNING)
    logERROR = partialmethod(_logDefine, lv=VerbosityLevels.ERROR)
    logDEBUG = partialmethod(_logDefine, lv=VerbosityLevels.DEBUG)
