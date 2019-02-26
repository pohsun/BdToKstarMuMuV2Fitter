#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:
# 
# Description     : Generic object provider to process.sources
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 20 Feb 2019 19:07 

from v2Fitter.FlowControl.Path import Path
from collections import OrderedDict

class ObjProvider(Path):
    """Book generic object to SourceManager if it is not defined"""

    def __init__(self, cfg):
        super(ObjProvider, self).__init__(cfg)
        self.cfg['source'] = {}

    @classmethod
    def templateConfig(cls):
        cfg = {
            'name': "ObjProvider",
            'obj': OrderedDict([
                # ('key', []), # Key, List of instancemethod
            ]),
        }
        return cfg

    def _runPath(self):
        """Get variables from process.sources"""
        for key, builders in self.cfg['obj'].items():
            if not key in self.process.sourcemanager.keys():
                for builder in builders:
                    builder(self)
                    if key in self.cfg['source'].keys():
                        break
            else:
                self.logger.logDEBUG("Skipped booked object {0}.".format(key))
