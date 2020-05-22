#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

from __future__ import print_function

import os
from collections import OrderedDict
from v2Fitter.FlowControl.Logger import Logger
from v2Fitter.FlowControl.SourceManager import SourceManager, FileManager

import ROOT

class Process:
    """A unit of a run-able job."""
    def __init__(self, name="myProcess", work_dir="testProcess", cfg=None):
        self.name = name
        self.work_dir = work_dir
        self.cwd = os.getcwd()
        self.cfg = cfg if cfg is not None else Process.templateConfig()

        # Register services
        self._services = OrderedDict()

        self.addService('logger', Logger("runtime.log"))
        self.addService('filemanager', FileManager())
        self.addService('sourcemanager', SourceManager())

    def __str__(self):
        return self._sequence.__str__()

    def reset(self):
        """ Reset the Paths """
        for seq in self._sequence:
            seq.reset()
        pass

    @classmethod
    def templateConfig(cls):
        cfg = {}
        return cfg

    def setSequence(self, seq):
        """Define a sequence of path to be run."""
        self._sequence = seq
        for p in self._sequence:
            p.hookProcess(self)

    def addService(self, name, obj):
        """Put object to the dictionary of services."""
        if name in self._services.keys():
            print("WARNING\t: Overwritting service with key={0}".format(name))
        setattr(self, name, obj)
        self._services[name] = obj

    def getService(self, name):
        """Get object from the dictionary of services."""
        try:
            return self._services[name]
        except KeyError:
            self.logger.logERROR("No service labelled with {0} is found.".format(name))

    def beginSeq_registerServices(self):
        """Initialize all services."""
        for key, s in self._services.items():
            setattr(s, "process", self)
            if s.logger is None:
                setattr(s, "logger", self.logger)
            s._beginSeq()

    def beginSeq(self):
        """Initialize all services. Start logging."""
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        os.chdir(self.work_dir)
        self.beginSeq_registerServices()
        ROOT.gRandom.SetSeed(0)
        self.logger.logINFO("New process initialized with random seed {0}".format(ROOT.gRandom.GetSeed()))

    def runSeq(self):
        """Run all path."""
        for p in self._sequence:
            self.logger.logDEBUG("Entering Path: {0}".format(p.cfg['name']))
            p.customize()
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
