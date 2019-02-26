#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : Fitter template without specification
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 26 Feb 2019 08:12 01:24

from v2Fitter.Fitter.FitterCore import FitterCore

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
        })
        return cfg

    def _initArgs(self, args):
        """Parameter initialization from db file"""
        db = shelve.open(self.cfg.get('db', "fitResults.db"))
        def initFromDB(iArg):
            argName = iArg.GetName()
            funcPair = [
                ('setVal', 'getVal'),
                ('setError', 'getError'),
                ('setAsymError', 'getErrorHi'),
                ('setAsymError', 'getErrorLo'),
                ('setConstant', 'isConstant'),
                ('setMax', 'getMax'),
                ('setMin', 'getMin')]
            if argName in db:
                for setter, getter in funcPair:
                    getattr(iArg, setter)(
                        *{
                            'getErrorHi': (db[argName]['getErrorLo'], db[argName][getter]),
                            'getErrorLo': (db[argName][getter], db[argName]['getErrorHi']),
                        }.get(getter, (db[argName][getter],))
                    )
            else:
                self.logger.logINFO("Found new variable {0}".format(argName))
        FitterCore.ArgLooper(args, initFromDB)
        db.close()

    def _preFitSteps(self):
        """Initialize """
        args = self.pdf.getParameters(self.data)
        self._initArgs(args)
        self.ToggleConstVar(args, True)
        self.ToggleConstVar(args, False, self.cfg.get('argPattern', [r'^.+$',]))

    def _updateArgs(self, args):
        """Update fit result to db file"""
        db = shelve.open(self.cfg.get('db', "fitResults.db"), writeback=True)
        def updateToDB(iArg):
            argName = iArg.GetName()
            funcPair = [
                ('setVal', 'getVal'),
                ('setError', 'getError'),
                ('setAsymError', 'getErrorHi'),
                ('setAsymError', 'getErrorLo'),
                ('setConstant', 'isConstant'),
                ('setMax', 'getMax'),
                ('setMin', 'getMin')]
            if argName not in db:
                self.logger.logINFO("Book new variable {0} to db file".format(argName))
                db[argName] = {}
            for setter, getter in funcPair:
                db[argName][getter] = getattr(iArg, getter)()
        FitterCore.ArgLooper(args, updateToDB)
        db.close()

    def _postFitSteps(self):
        """Post-processing"""
        args = self.pdf.getParameters(self.data)
        self.ToggleConstVar(args, True)
        self._updateArgs(args)


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

