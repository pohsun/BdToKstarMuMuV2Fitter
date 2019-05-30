#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

import abc
import ROOT

from v2Fitter.FlowControl.Path import Path

class AbsToyStudier(Path):
    """
A mock of RooFit::RooMCStudy which is useful for low stat analysis.
    Generate a lot of subset from input RooDataSet and run fitter for each.
    """

    def __init__(self, cfg):
        """Init"""
        super(AbsToyStudier, self).__init__(cfg)
        self.reset()

    def reset(self):
        super(AbsToyStudier, self).reset()
        self.data = None
        self.fitter = None

    @classmethod
    def templateConfig(cls):
        cfg = {
            'name': "ToyStudier",
            'data': None,
            'fitter': None,
            'nSetOfToys': 1,
        }
        return cfg

    @abc.abstractmethod
    def getSubData(self):
        """
Decide how the input dataset transform into subsets.
    return an instance of RooFit::RooDataSet
        """
        raise NotImplementedError

    @abc.abstractmethod
    def getSubDataEntries(self, setIdx):
        """
Decide the number of entries of this subset.
    return an integer
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _preSetsLoop(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _postRunFitSteps(self, setIndex):
        raise NotImplementedError

    def _runSetsLoop(self):
        for iSet in range(self.cfg['nSetOfToys']):
            self.process.dbplayer.resetDB(True)

            self.fitter.hookProcess(self.process)
            self.fitter.customize()

            self.currentSubDataEntries = self.getSubDataEntries(iSet)

            self.fitter.pdf = self.process.sourcemanager.get(self.fitter.cfg['pdf'])
            self.fitter.data = self.getSubData().next()
            self.fitter._bookMinimizer()
            self.fitter._preFitSteps()
            self.fitter._runFitSteps()
            self._postRunFitSteps(iSet)

            self.fitter.reset()

    @abc.abstractmethod
    def _postSetsLoop(self):
        raise NotImplementedError

    def _runPath(self):
        """ Chain of pre-run-post steps"""
        self.fitter = self.cfg['fitter']
        self.data = self.process.sourcemanager.get(self.cfg['data'])

        self._preSetsLoop()
        self._runSetsLoop()
        self._postSetsLoop()

def getSubData_random(self, checkCollision=True):
    """ Pick random subset. Input dataset is asseumed to be large enough to avoid collision."""
    sumEntries = int(self.data.sumEntries())
    evtBits = ROOT.TBits(int(sumEntries))
    while True:
        outputBits = ROOT.TBits(sumEntries)
        for entry in range(self.currentSubDataEntries):
            rnd_collisions = 0
            while True:
                rnd = ROOT.gRandom.Integer(sumEntries)
                if checkCollision and evtBits.TestBitNumber(rnd):
                    rnd_collisions = rnd_collisions + 1
                else:
                    evtBits.SetBitNumber(rnd)
                    outputBits.SetBitNumber(rnd)
                    break

            if checkCollision and rnd_collisions * 20 > self.currentSubDataEntries:
                self.logger.logWARNING("Rate of random number collision may over 5%, please use larger input")

        # Sequential reading is highly recommanded by ROOT author
        output = self.data.emptyClone("{0}Subset".format(self.data.GetName()))
        startBit = outputBits.FirstSetBit(0)
        while startBit < sumEntries:
            output.add(self.data.get(startBit))
            startBit = outputBits.FirstSetBit(startBit + 1)
        yield output

def getSubData_seqential(self):
    """Not suggested since source could be mixed with RooDataSet::add() """
    sumEntries = int(self.data.sumEntries())
    currentEntry = 0
    while True:
        output = self.data.emptyClone("{0}Subset".format(self.data.GetName()))
        if currentEntry + self.currentSubDataEntries > sumEntries:
            self.logger.logERROR("Running out of source dataset")
            raise RuntimeError
        for entry in range(self.currentSubDataEntries):
            output.add(self.data.get(currentEntry))
            currentEntry = currentEntry + 1
        yield output
