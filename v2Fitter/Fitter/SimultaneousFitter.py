#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Ref: rf501_simultaneouspdf.C

import ROOT
from v2Fitter.Fitter.FitterCore import FitterCore

class SimultaneousFitter(FitterCore):
    """A fitter object acts as a path, to be queued in a process.
Following functions to be overloaded to customize the full procedure...
    _preFitSteps
    _runFitSteps
    _postFitSteps
"""
    def __init__(self, cfg):
        super(SimultaneousFitter, self).__init__(cfg)
        self.reset()

    def reset(self):
        super(SimultaneousFitter, self).reset()
        self.category = None
        self.data = []
        self.pdf = []
        self.dataWithCategories = None
        self.minimizer = None

    def _bookPdfData(self):
        """ """
        self.category = ROOT.RooCategory("{0}.category".format(self.name), "")
        dataWithCategoriesCmdArgs = (ROOT.RooFit.Index(self.category),)
        if len(self.cfg['category']) == len(self.cfg['data']) == len(self.cfg['pdf']):
            for category, dataName, pdfName in zip(self.cfg['category'], self.cfg['data'], self.cfg['pdf']):
                self.pdf.append(self.process.sourcemanager.get(pdfName))
                if not hasattr(dataName, "__iter__"):
                    self.data.append(self.process.sourcemanager.get(dataName))
                else:
                    # Alternative way to merge list of input data/toy
                    for dataIdx, dataNameInList in enumerate(dataName):
                        if dataIdx != 0:
                            self.data[-1].append(self.process.sourcemanager.get(data))
                        else:
                            self.data.append(self.process.sourcemanager.get(data).Clone())
                dataWithCategoriesCmdArgs += (ROOT.RooFit.Import(category, self.data[-1]))
            self.dataWithCategories = ROOT.RooDataSet("{0}.dataWithCategories".format(self.name), "", self.pdf[-1].getObservables(self.data[-1]), *dataWithCategoriesCmdArgs)
        else:
            raise RuntimeError("Number of category/data/pdf doesn't match")

    def _bookMinimizer(self):
        """Bind a RooSimultaneous object to bind to self.minimizer at Runtime"""
        self.minimizer = ROOT.RooSimultaneous(self.name, "", )
        for cat, pdf in zip(self.cfg['category'], self.pdf):
            self.minimizer.addPdf(pdf, cat)

    def _preFitSteps(self):
        """Abstract: Do something before main fit loop"""
        for pdf, data in zip(self.pdf, self.data):
            args = pdf.getParameters(data)
            self.ToggleConstVar(args, True)
            self.ToggleConstVar(args, False, self.cfg['argPattern'])

    def _runFitSteps(self):
        """Standard fitting procedure to be overwritten."""
        if len(self.cfg['fitToCmds']) == 0:
            self.minimizer.fitTo(self.dataWithCategories)
        else:
            for cmd in self.cfg['fitToCmds']:
                self.minimizer.fitTo(self.dataWithCategories, *cmd)

    def _postFitSteps(self):
        """ Abstract: Do something after main fit loop"""
        for pdf, data in zip(self.pdf, self.data):
            self.ToggleConstVar(pdf.getParameters(data), True)

    @classmethod
    def templateConfig(cls):
        cfg = {
            'name': "SimultaneousFitter",
            'category': ['cat1', 'cat2'],
            'data': ["data1", "data2"],
            'pdf': ["f1", "f2"],
            'argPattern': [r'^.+$'],
            'fitToCmds': [[],],
        }
        return cfg

    def _runPath(self):
        """Stardard fitting procedure to be overlaoded."""
        self._bookPdfData()
        self._bookMinimizer()
        self._preFitSteps()
        self._runFitSteps()
        self._postFitSteps()
