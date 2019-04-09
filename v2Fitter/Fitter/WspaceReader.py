#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : Read pdf and var from RooWorkspace
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 24 Feb 2019 19:01 17:36

from v2Fitter.FlowControl.Path import Path

import os
from collections import OrderedDict

import ROOT
from ROOT import TFile, RooWorkspace
from ROOT import RooRealVar, RooAbsPdf

class WspaceReader(Path):
    """Read objects from RooWorkspace"""
    def __init__(self, cfg):
        """Init"""
        super(WspaceReader, self).__init__(cfg)
        self.reset()
        return

    def reset(self):
        super(WspaceReader, self).reset()
        self.ifile = None
        self.wspace = None

    @classmethod
    def templateConfig(cls):
        cfg = {
            'name': "WspaceReader",
            'fileName': "wspace.root",
            'wspaceTag': "DEFAULT",
            'obj': OrderedDict([
                # ('source_key', 'wspace_key'),
            ]),
        }
        return cfg

    def _runPath(self):
        # Hook to registerd file
        fileName = self.cfg.get('fileName', "")
        if os.path.exists(fileName):
            self.ifile = self.process.filemanager.open(str(hex(id(self))), fileName, 'READ')

        # Load wspace
        wspaceName = "wspace.{0}".format(self.cfg['wspaceTag'])
        if wspaceName in self.process.sourcemanager.keys():
            self.wspace = self.process.sourcemanager.get(wspaceName)
        elif not self.ifile == None:
            self.wspace = self.ifile.Get(wspaceName)

        # Load desired objects
        if self.wspace == None:
            self.logger.logINFO("RooWorkspace {0} not found. Create new workspace without booking target objects.".format(wspaceName))
            self.wspace = RooWorkspace(wspaceName)
            self.cfg['source'][wspaceName] = self.wspace

            # Update results only for new workspace.
            # By design you CANNOT overwrite items in RooWorkspace by `Write` or `writeToFile`.
            self.bookEndSeq()
        else:
            self.logger.logINFO("RooWorkspace {0} found. Loading objects...".format(wspaceName))
            self.cfg['source'][wspaceName] = self.wspace
            def readObjs():
                """Exactly define how to read varaiables"""
                for source_key, wspace_key in self.cfg['obj'].items():
                    if source_key in self.process.sourcemanager.keys():
                        self.cfg['source'][source_key] = self.process.sourcemanager.get(source_key)
                    else:
                        obj = self.wspace.obj(wspace_key)
                        if obj == None:
                            self.logger.logWARNING("No Variable {0} is found.".format(wspace_key))
                        else:
                            self.cfg['source'][source_key] = obj
            readObjs()

    def bookEndSeq(self):
        """Book to p.endSeq stack. Assign new order in case of multiple calls."""
        if hex(id(self.wspace)) in self.process._services.keys():
            del self.process._services[id(self.wspace)]
        self.process._services[hex(id(self.wspace))] = self

    def _endSeq(self):
        """Write wspace to registered file"""
        if self.ifile == None and 'fileName' in self.cfg.keys():
            self.wspace.writeToFile(self.cfg['fileName'], True)

if __name__ == '__main__':
    pass
