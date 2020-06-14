#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

# Description     : Fitter template without specification
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)

import functools
import re
import math
import ROOT
import SingleBuToKstarMuMuFitter.cpp

from v2Fitter.Fitter.FitterCore import FitterCore
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
            'argAliasInDB': {}, # When writes result to DB.
            'argAliasFromDB': {}, # Overwrite argAliasInDB only when initFromDB, or set to None to skip this variable.
            'saveToDB': True,
        })
        return cfg

    def _bookMinimizer(self):
        """"""
        if not hasattr(self, 'fitter'):
            # Re-define ROOT.StdFitter seem to make errors when StdFitter.Init is called again.
            # This hot patch works when we run the same fitter multiple times, but it's not working when changeing the pdf/data.
            self.fitter = ROOT.StdFitter()

        self.fitter.Reset()
        for opt in self.cfg.get("createNLLOpt", []):
            self.fitter.addNLLOpt(opt)
        if hasattr(self.data, "InheritsFrom") and hasattr(self.pdf, "InheritsFrom"):
            self.fitter.Init(self.pdf, self.data)
            self._nll = self.fitter.GetNLL()
        else:
            self.logger.logERROR("Either {data} or {pdf} is not valid.".format(data=self.cfg['data'], pdf=self.cfg['pdf']))
            raise RuntimeError("{name}: Either {data} or {pdf} is not valid.".format(name=self.name, data=self.cfg['data'], pdf=self.cfg['pdf']))

    def _preFitSteps_initFromDB(self):
        """Initialize from DB"""
        argAliasFromDB = {}
        for d in [self.cfg['argAliasInDB'], self.cfg['argAliasFromDB']]:
            for k, v in d.items():
                argAliasFromDB[k] = v
        FitDBPlayer.initFromDB(self.process.dbplayer.odbfile, self.args, argAliasFromDB)
        self.ToggleConstVar(self.args, True)
        self.ToggleConstVar(self.args, False, self.cfg.get('argPattern'))

    def _preFitSteps_preFit(self):
        """ Standard prefit steps """
        unboundFl = self.args.find("unboundFl")
        unboundAfb = self.args.find("unboundAfb")
        if unboundFl != None and unboundAfb != None:
            def isPhysical(uA, uF):
                f = unboundFlToFl(uF)
                a = unboundAfbToAfb(uA, f)
                return abs(a) < (1 - f) * 0.75
            while not isPhysical(unboundAfb.getVal(), unboundFl.getVal()):
                fl = unboundFlToFl(unboundFl.getVal())
                afb = unboundAfbToAfb(unboundAfb.getVal(), fl)
                unboundAfb.setVal(afbToUnboundAfb(0.5 * afb, fl))
                unboundFl.setVal(flToUnboundFl(0.5 * fl))

    def _preFitSteps_vetoSmallFs(self):
        """ fs is usually negligible, set the fraction to 0"""
        if "fs" in self.cfg.get('argPattern'):
            fs = self.args.find("fs")
            transAs = self.args.find("transAs")
            fs.setVal(fs.getMin() * 2)  # Exact min go out-of-domain while setting transAs=0
            fs.setConstant(True)
            transAs.setVal(0)
            transAs.setConstant(True)

    def _preFitSteps(self):
        """ Prefit steps """
        self.args = self.pdf.getParameters(self.data)
        self._preFitSteps_initFromDB()
        self._preFitSteps_vetoSmallFs()
        self._preFitSteps_preFit()

    def _postFitSteps(self):
        """Post-processing"""
        #  FitterCore.ArgLooper(self.args, lambda arg: arg.Print())
        self.ToggleConstVar(self.args, True)
        if self.cfg['saveToDB']:
            def rejectRedundantArgs(iArg):
                if any([re.match(pat, iArg.GetName()) for pat in self.cfg['argPattern']]):
                    self.cfg['argAliasInDB'][iArg.GetName()] = self.cfg['argAliasInDB'].get(iArg.GetName(), iArg.GetName())
                else:
                    self.cfg['argAliasInDB'][iArg.GetName()] = None
            FitterCore.ArgLooper(self.args, rejectRedundantArgs)
            FitDBPlayer.UpdateToDB(self.process.dbplayer.odbfile, self.args, self.cfg['argAliasInDB'])
            FitDBPlayer.UpdateToDB(self.process.dbplayer.odbfile, self.fitResult)

    def _runFitSteps(self):
        self.FitMigrad()
        if self.cfg.get('FitHesse', False):
            self.FitHesse()
        if self.cfg.get('FitMinos', [False, ()])[0]:
            self.FitMinos()

    def FitMigrad(self):
        """Migrad"""
        migradResult = self.fitter.FitMigrad()
        self.fitResult = {
            "{0}.{1}".format(self.name, self.cfg['argAliasInDB'].get('migrad', 'migrad')): {
                'status': migradResult.status(),
                'nll': migradResult.minNll(),
            }
        }
        self.cfg['source']['{0}.migradResult'.format(self.name)] = migradResult

    def FitHesse(self):
        """Hesse"""
        self.fitter.FitHesse()

    def FitMinos(self):
        """Minos"""
        if len(self.cfg['FitMinos']) > 1 and self.cfg['FitMinos'][1]:
            par = ROOT.RooArgSet()
            FitterCore.ArgLooper(self.args, lambda var: par.add(var), self.cfg['FitMinos'][1])
        else:
            par = self.args
        minosResult = self.fitter.FitMinos(par)
        self.fitResult.update({
            "{0}.{1}".format(self.name, self.cfg['argAliasInDB'].get('minos', 'minos')): {
                'status': minosResult.status(),
                'nll': minosResult.minNll(),
            }
        })
        self.cfg['source']['{0}.minosResult'.format(self.name)] = minosResult

        # Dont' draw profiled likelihood scanning with following link
        # https://root.cern.ch/root/html/tutorials/roofit/rf605_profilell.C.html
        # This build-in function doesn't handle variable transformation and unphysical region.

def unboundFlToFl(unboundFl):
    return 0.5 + ROOT.TMath.ATan(unboundFl) / ROOT.TMath.Pi()

def flToUnboundFl(fl):
    return ROOT.TMath.Tan((fl - 0.5) * ROOT.TMath.Pi())

def unboundAfbToAfb(unboundAfb, fl):
    return 1.5 * (1 - fl) * ROOT.TMath.ATan(unboundAfb) / ROOT.TMath.Pi()

def afbToUnboundAfb(afb, fl):
    return ROOT.TMath.Tan(afb * ROOT.TMath.Pi() / 1.5 / (1. - fl))

def decorator_bookMinimizer_addGausConstraints(varNames, vals=None, valerrs=None):
    """ For quick adding gaussian constrint to createNLLOpt.
Assuming no ROOT.RooFit.ExternalConstraints in createNLLOpt by default.
This would be quite useful for proflied Feldman-Cousins method"""
    if vals is None:
        vals = [None] * len(varNames)
    if valerrs is None:
        valerrs = [None] * len(varNames)
    def wrapper(func):
        @functools.wraps(func)
        def wrapped_f(self):
            gausConstraints = ROOT.RooArgSet()
            for varName, val, valerr in zip(varNames, vals, valerrs):
                # assuming all variables are read by WspaceReader
                if varName == "afb":
                    var = self.process.sourcemanager.get("afb")
                    gausC = ROOT.RooGaussian("gausC_afb", "", var, ROOT.RooFit.RooConst(val), ROOT.RooFit.RooConst(valerr if valerr else 0.01))
                elif varName == "fl":
                    var = self.process.sourcemanager.get("fl")
                    gausC = ROOT.RooGaussian("gausC_fl", "", var, ROOT.RooFit.RooConst(val), ROOT.RooFit.RooConst(valerr if valerr else 0.01))
                else:
                    var = self.pdf.getParameters(self.data).find(varName)
                    gausC = ROOT.RooGaussian("gausC_{0}".format(varName), "", var, ROOT.RooFit.RooConst(val if val else var.getVal()), ROOT.RooFit.RooConst(valerr if valerr else var.getError()))
                self.cfg['source'][gausC.GetName()] = gausC
                gausC.Print()
                gausConstraints.add(gausC)
            self.cfg['createNLLOpt'].append(ROOT.RooFit.ExternalConstraints(gausConstraints))
            func(self)
        return wrapped_f
    return wrapper
