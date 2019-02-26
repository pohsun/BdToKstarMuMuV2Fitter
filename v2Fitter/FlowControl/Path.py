#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : A single step to be run in a process
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 20 Feb 2019 19:04 21:48

from __future__ import print_function

import abc

class Path():
    """Steps to be run in a Process"""
    __metaclass__ = abc.ABCMeta
    def __init__(self, cfg):
        self.cfg = cfg
        self.name = self.cfg['name'].replace('.', '_')
        self.process = None
        self.logger = None
        pass

    def __str__(self):
        return "Path[{0}]".format(self.name)

    # @abc.abstractclassmethod
    def templateConfig(cls):
        """Return template configuration."""
        raise NotImplementedError

    @abc.abstractmethod
    def _runPath(self):
        """Main function to be called in a sequence."""
        raise NotImplementedError

    def _addSource(self):
        """Add shared objects to the source pool."""
        if 'source' in self.cfg.keys():
            for key, val  in self.cfg['source'].items():
                self.process.sourcemanager.update(key, val, addHist=self.name)

