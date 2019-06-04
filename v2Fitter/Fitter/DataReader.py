#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

# Description     : Creating RooDataSet for fitting
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 20 Feb 2019 19:06 17:36

from v2Fitter.FlowControl.Path import Path

from ROOT import TChain
from ROOT import TIter
from ROOT import RooDataSet

class DataReader(Path):
    """Create RooDataSet from a TChain"""
    def __init__(self, cfg):
        """Init"""
        super(DataReader, self).__init__(cfg)
        self.ch = TChain("tree")
        for f in cfg['ifile']:
            self.ch.Add(f)
        if len(self.cfg['ifriend']) > 0:
            self.friend = TChain("tree")
            for f in self.cfg['ifriend']:
                self.friend.Add(f)
            self.friend.BuildIndex(*cfg['ifriendIndex'])
            self.ch.AddFriend(self.friend)
        self.argset = cfg['argset']
        self.reset()
        return

    def reset(self):
        super(DataReader, self).reset()
        self.dataset = {}

    def __str__(self):
        list_of_files = self.ch.GetListOfFiles()
        next_file = TIter(list_of_files)
        print("Input file list is given below.")
        for f in range(list_of_files.GetEntries()):
            print("\t{0}".format(next_file().GetTitle()))
        print("End of the input file list.")
        return ""

    @classmethod
    def templateConfig(cls):
        cfg = {
            'name': "DataReader",
            'ifile': [],
            'ifriend': [],
            'ifriendIndex': ["Run", "Event"],
            'argset': [],
            'dataset': [],
        }
        return cfg

    def createDataSet(self, dname, dcut):
        """Create named dataset"""
        if dname in self.dataset.keys():
            return self.dataset[dname]
        data = RooDataSet(
            dname,
            "",
            self.ch,
            self.argset,
            dcut)
        self.dataset[dname] = data
        return data

    def createDataSets(self, cfg):
        """Create named dataset"""
        for name, cut in cfg:
            self.createDataSet(name, cut)
        return self.dataset

    def _runPath(self):
        self.createDataSets(self.cfg['dataset'])
        pass

    def _addSource(self):
        """Add dataset and arguments to source pool"""
        if not 'source' in self.cfg.keys():
            self.cfg['source'] = {}
        self.cfg['source']['{0}.tree'.format(self.name)] = self.ch
        self.cfg['source']['{0}.argset'.format(self.name)] = self.argset
        if len(self.cfg['ifriend']) > 0:
            self.cfg['source']['{0}.friend'.format(self.name)] = self.friend
        for dname, d in self.dataset.items():
            self.cfg['source'][dname] = d
            self.logger.logINFO("{0} events in {1}.".format(d.sumEntries(), dname))
        super(DataReader, self)._addSource()
