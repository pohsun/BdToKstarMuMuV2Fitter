#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : SourceManager Service
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 24 Feb 2019 19:15 17:29

from v2Fitter.FlowControl.Service import Service
from v2Fitter.FlowControl.Logger import VerbosityLevels

from collections import OrderedDict

import ROOT
from ROOT import TObject
from ROOT import SetOwnership
from ROOT import TFile

class SourceManager(Service):
    """Source manager"""
    def __init__(self):
        Service.__init__(self)
        self._sources = OrderedDict()

    def _endSeq(self):
        # Dump items with LIFO order
        while len(self._sources) > 0:
            key, f = self._sources.popitem(last=True)

    def __str__(self):
        if self.logger.verbosityLevel == VerbosityLevels.DEBUG:
            for k, v in self._sources.items():
                print(k, v)
        return self._sources.__str__()

    def __contains__(self, item):
        """See https://docs.python.org/3.7/reference/datamodel.html#emulating-container-types"""
        return item in self._sources


    def get(self, key, default=None, addHist=None):
        if key not in self._sources.keys():
            self.logger.logWARNING("No source labeled with {0} is booked.".format(key))
            return default

        # Decorators
        if addHist is not None:
            self._sources[key]['history'].append(addHist)

        return self._sources[key]['obj']

    def update(self, key, obj=None, addHist=None, overwriteExist=True):
        if obj is None:
            self.logger.logWARNING("Update a 'None' with key '{0}'".format(key))
        if key in self._sources.keys() and overwriteExist:
            self.logger.logDEBUG("Overwrite source '{0}'".format(key))
            self._sources[key]['obj'] = obj
        else:
            self._sources[key] = {
                'obj': obj,
                'history':[],
            }

        if addHist is not None:
            self._sources[key]['history'].append(addHist)

    def keys(self):
        return self._sources.keys()

class FileManager(Service):
    """File manager"""
    def __init__(self):
        Service.__init__(self)
        self._files = OrderedDict()

    def __str__(self):
        if self.logger.verbosityLevel == VerbosityLevels.DEBUG:
            for k, v in self._files.items():
                print(k, v)
        return self._files.__str__()

    def _endSeq(self):
        """Close files with LIFO order"""
        while len(self._files) > 0:
            key, f = self._files.popitem(last=True)
            # if hasattr(f, '__exit__'):
            #     f.__exit__()
            # elif hasattr(f, 'InheritsFrom') and f.InheritsFrom('TObject'):
            #     del f
            # else:
            #     raise NotImplementedError
        pass

    def open(self, key, fname, mode):
        if not key in self._files.keys():
            f = TFile.Open(fname, mode)
            self._files[key] = f
        else:
            f = self._files[key]
        return f

    def get(self, key):
        try:
            return self._files[key]
        except KeyError as e:
            self.logger.logINFO("No file labeled with {0} is booked.".format(key))
            return None

    def keys(self):
        return self._files.keys()

