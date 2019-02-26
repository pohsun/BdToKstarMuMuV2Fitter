#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : The unit of a run-able job
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 24 Feb 2019 20:18 21:48

from __future__ import print_function

import os
from collections import OrderedDict
from v2Fitter.FlowControl.Logger import Logger
from v2Fitter.FlowControl.SourceManager import SourceManager, FileManager

class Process:
    """A unit of a run-able job."""
    def __init__(self, name, work_dir):
        self.name = name
        self.work_dir = work_dir
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        self.cwd = os.getcwd()

        # Register services
        self._services = OrderedDict()

        self.logger = Logger("runtime.log")
        self._services["logger"] = self.logger
        self.filemanager = FileManager()
        self._services["filemanager"] = self.filemanager
        self.sourcemanager = SourceManager()
        self._services["sourcemanager"] = self.sourcemanager

    def __str__(self):
        return self._sequence.__str__()

    def setSequence(self, seq):
        """Define a sequence of path to be run."""
        self._sequence = seq
        for p in self._sequence:
            setattr(p, "process", self)
            if p.logger is None:
                setattr(p, "logger", self.logger)
        pass

    def addService(self, name, obj):
        """Put object to the dictionary of services."""
        if name in self._services.keys():
            self.logger.logWARNING("Overwritting service with key={0}".format(name))
        self._services[name] = obj

    def getService(self, name):
        """Get object from the dictionary of services."""
        try:
            return self._services[name]
        except KeyError as e:
            self.logger.logERROR("No service labelled with {0} is found.".format(name))

    def beginSeq(self):
        """Initialize all services."""
        os.chdir(self.work_dir)
        for key, s in self._services.items():
            setattr(s, "process", self)
            if s.logger is None:
                setattr(s, "logger", self.logger)
            s._beginSeq()

    def runSeq(self):
        """Run all path."""

        for p in self._sequence:
            self.logger.logDEBUG("Entering Path: {0}".format(p.cfg['name']))
            p._runPath()
            p._addSource()
            # print(self.sourcemanager)
            # print(self.filemanager)

    def endSeq(self):
        """Terminate all services in a reversed order."""
        while self._services:
            key, s = self._services.popitem(True)
            self.logger.logDEBUG("Entering endSeq: {0}".format(key))
            s._endSeq()
        os.chdir(self.cwd)

