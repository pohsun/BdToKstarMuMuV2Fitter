#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : Fitter template without specification
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)

from v2Fitter.Fitter.FitterCore import FitterCore
from anaSetup import q2bins
from FitDBPlayer import FitDBPlayer

import os
import shutil
import shelve
import functools

import ROOT

class SingleBuToKstarMuMuFitter(FitterCore):
    """Implementation to standard fitting procdeure to BuToKstarMuMu angular analysis"""

    @classmethod
    def templateConfig(cls):
        cfg = FitterCore.templateConfig()
        cfg.update({
            'name': "SingleBuToKstarMuMuFitter",
            'data': "dataReader.Fit",
            'pdf' : "f",
            'db'  : "fitResults.db",
            'FitHesse':True,
            'FitMinos': [True, ()],
            'createNLLOpt': [ROOT.RooFit.Extended(1),],
            'updateArgs': True,
            'systematics': [],
            'argPattern':[r'^.+$',],
            'argAliasInDB':{},
            'plotters': None,
        })
        return cfg

    def _preFitSteps(self):
        """Initialize """
        args = self.pdf.getParameters(self.data)
        FitDBPlayer.initFromDB(self.cfg.get('db', FitDBPlayer.outputfilename), args, self.cfg['argAliasInDB'])
        self.ToggleConstVar(args, True)
        self.ToggleConstVar(args, False, self.cfg.get('argPattern'))

        # customization for systematics
        for syst in self.cfg['systematics']:
            if syst == "AltEfficiency":
                hasXTerm = args.find("hasXTerm")
                hasXTerm.setVal(0)
            else:
                self.logger.logERROR("Unknown source of systematic uncertainty.")
                raise NotImplementedError

    def _postFitSteps(self):
        """Post-processing"""
        args = self.pdf.getParameters(self.data)
        self.ToggleConstVar(args, True)
        if self.cfg['updateArgs']:
            ofilename = "{0}_{1}.db".format(os.path.splitext(FitDBPlayer.outputfilename)[0], q2bins[self.process.cfg['binKey']]['label'])
            if not os.path.exists(ofilename) and self.process.cfg.has_key("db"):
                shutil.copy(self.process.cfg["db"], ofilename)
            FitDBPlayer.UpdateToDB(ofilename, args, self.cfg['argAliasInDB'])
        if self.cfg.get('plotters', False):
            for plotter, kwargs in self.cfg['plotters']:
                plotter(self, **kwargs)



    def _runFitSteps(self):
        self.FitMigrad()
        if self.cfg.get('FitHesse', False):
            self.FitHesse()
        if self.cfg.get('FitMinos', [False, ()])[0]:
            self.FitMinos()

    def FitMigrad(self):
        """Migrad"""
        isMigradConverge=[-1,0]

        maxMigradCall = 10
        for iL in range(maxMigradCall):
            isMigradConverge[0]=self.minimizer.migrad()
            if isMigradConverge[0] == 0:
                break
        isMigradConverge[1] = self._nll.getVal()
        return isMigradConverge

    def FitHesse(self):
        """Hesse"""
        isHesseValid = self.minimizer.hesse()
        return isHesseValid

    def FitMinos(self):
        """Minos"""
        isMinosValid = -1

        par = self.pdf.getParameters(self.data)
        if len(self.cfg['FitMinos']) > 1 and self.cfg['FitMinos'][1]:
            iter = par.createIterator()
            var = iter.Next()
            while var:
                if var.GetName() not in self.cfg['FitMinos'][1]:
                    par.remove(var)
                var = iter.Next()
                par.Print()

        maxMinosCall = 3
        for iL in range(maxMinosCall):
            isMinosValid = self.minimizer.minos(par)
            if isMinosValid == 0:
                break
        return isMinosValid

