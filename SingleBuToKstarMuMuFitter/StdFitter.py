#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

# Description     : Fitter template without specification
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)

import ROOT
import SingleBuToKstarMuMuFitter.cpp

from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.anaSetup import q2bins
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer

class StdFitter(FitterCore):
    """Implementation to standard fitting procdeure to BuToKstarMuMu angular analysis"""

    @classmethod
    def templateConfig(cls):
        cfg = FitterCore.templateConfig()
        cfg.update({
            'name': "StdFitter",
            'data': "dataReader.Fit",
            'pdf': "f",
            'FitHesse': True,
            'FitMinos': [True, ()],
            'createNLLOpt': [ROOT.RooFit.Extended(1), ],
            'argPattern': [r'^.+$', ],
            'argAliasInDB': {},
        })
        return cfg

    def _bookMinimizer(self):
        """"""
        self.fitter = ROOT.StdFitter()
        for opt in self.cfg.get("createNLLOpt", []):
            self.fitter.addNLLOpt(opt)
        self.minimizer = self.fitter.Init(self.pdf, self.data)
        self._nll = self.fitter.GetNLL()
        self.minimizer.setPrintLevel(0)
        pass

    def _preFitSteps_initFromDB(self):
        """Initialize from DB"""
        self.args = self.pdf.getParameters(self.data)
        FitDBPlayer.initFromDB(self.process.odbfilename, self.args, self.cfg['argAliasInDB'])
        self.ToggleConstVar(self.args, True)
        self.ToggleConstVar(self.args, False, self.cfg.get('argPattern'))

    def _preFitSteps_vetoSmallFs(self):
        """ fs is usually negligible, set the fraction to 0"""
        if "fs" in self.cfg.get('argPattern'):
            fs = self.args.find("fs")
            transAs = self.args.find("transAs")
            fs.setVal(fs.getMin())
            fs.setConstant(True)
            transAs.setVal(0)
            transAs.setConstant(True)

    def _preFitSteps(self):
        """Initialize to be customized"""
        self._preFitSteps_initFromDB()
        self._preFitSteps_vetoSmallFs()

    def _postFitSteps(self):
        """Post-processing"""
        #  FitterCore.ArgLooper(self.args, lambda arg: arg.Print())
        self.ToggleConstVar(self.args, True)
        FitDBPlayer.UpdateToDB(self.process.odbfilename, self.args, self.cfg['argAliasInDB'])

    def _runFitSteps(self):
        self.FitMigrad()
        if self.cfg.get('FitHesse', False):
            self.FitHesse()
        if self.cfg.get('FitMinos', [False, ()])[0]:
            self.FitMinos()

    def FitMigrad(self):
        """Migrad"""
        self.fitter.FitMigrad()

    def FitHesse(self):
        """Hesse"""
        self.fitter.FitHesse()

    def FitMinos(self):
        """Minos"""
        par = self.pdf.getParameters(self.data)
        if len(self.cfg['FitMinos']) > 1 and self.cfg['FitMinos'][1]:
            FitterCore.ArgLooper(par, lambda var: par.remove(var), self.cfg['FitMinos'][1], True)
        self.fitter.FitMinos(par)

        # Dont' draw profiled likelihood scanning with 
        # https://root.cern.ch/root/html/tutorials/roofit/rf605_profilell.C.html
        # This build-in function doesn't handle variable transformation and unphysical region.

def unboundFlToFl(unboundFl):
    return 0.5 + ROOT.TMath.ATan(unboundFl) / ROOT.TMath.Pi()

def unboundAfbToAfb(unboundAfb, fl):
    return 1.5 * (1 - fl) * ROOT.TMath.ATan(unboundAfb) / ROOT.TMath.Pi()
