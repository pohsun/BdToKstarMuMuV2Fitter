#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=1 fdn=3 ft=python et:

import types
from copy import deepcopy
import functools
import shelve

from SingleBuToKstarMuMuFitter.anaSetup import q2bins, modulePath
from SingleBuToKstarMuMuFitter.varCollection import Bmass, CosThetaL, CosThetaK

from v2Fitter.Fitter.ToyGenerator import ToyGenerator
from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer
from SingleBuToKstarMuMuFitter.fitCollection import setupSigAFitter

import ROOT

from SingleBuToKstarMuMuFitter.StdProcess import p
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection

CFG = deepcopy(ToyGenerator.templateConfig())
CFG.update({
    'db': "{0}/input/selected/fitResults_{{binLabel}}.db".format(modulePath),
    'argset': ROOT.RooArgSet(Bmass, CosThetaL, CosThetaK),
    'argAliasInDB': {},
    'generateOpt': [],
    'mixWith': "ToyGenerator.mixedToy",
    'scale': 1,
})

def decorator_initParameters(func):
    @functools.wraps(func)
    def wrapped_f(self):
        self.pdf = self.process.sourcemanager.get(self.cfg['pdf'])
        self.argset = self.cfg['argset']
        self.params = self.pdf.getParameters(self.argset)
        FitDBPlayer.initFromDB(self.cfg['db'].format(binLabel=q2bins[self.process.cfg['binKey']]['label']), self.params, self.cfg.get('argAliasInDB', []))

        func(self)
    return wrapped_f

def decorator_setExpectedEvents(yieldVars=None):
    """Generate from fixed dbfile. Default yieldVars  = ["nSig", "nBkgComb"]"""
    if yieldVars is None:
        yieldVars = ["nSig", "nBkgComb"]
    def wrapper(func):
        @functools.wraps(func)
        def wrapped_f(self):
            func(self)

            expectedYields = 0
            try:
                db = shelve.open(self.cfg['db'].format(binLabel=q2bins[self.process.cfg['binKey']]['label']))
                for yVar in yieldVars:
                    try:
                        expectedYields += self.params.find(yVar).getVal()
                    except AttributeError:
                        expectedYields += db[self.cfg['argAliasInDB'].get(yVar, yVar)]['getVal']
            finally:
                self.cfg['expectedYields'] = expectedYields
                #  self.logger.logINFO("Will generate {0} events from p.d.f {1}.".format(expectedYields, self.pdf.GetName()))
                db.close()
        return wrapped_f
    return wrapper

# sigToyGenerator - validation
setupSigToyGenerator = deepcopy(CFG)
setupSigToyGenerator.update({
    'name': "sigToyGenerator",
    'pdf': "f_sig3D",
    'saveAs': "sigToyGenerator.root",
})
sigToyGenerator = ToyGenerator(setupSigToyGenerator)
@decorator_setExpectedEvents(["nSig"])
@decorator_initParameters
def sigToyGenerator_customize(self):
    pass
sigToyGenerator.customize = types.MethodType(sigToyGenerator_customize, sigToyGenerator)

# bkgCombToyGenerator - validation
setupBkgCombToyGenerator = deepcopy(CFG)
setupBkgCombToyGenerator.update({
    'name': "bkgCombGenerator",
    'pdf': "f_bkgComb",
    'saveAs': "bkgCombToyGenerator.root",
})
bkgCombToyGenerator = ToyGenerator(setupBkgCombToyGenerator)
@decorator_setExpectedEvents(["nBkgComb"])
@decorator_initParameters
def bkgCombToyGenerator_customize(self):
    pass
bkgCombToyGenerator.customize = types.MethodType(bkgCombToyGenerator_customize, bkgCombToyGenerator)

# Systematics

# sigAToyGenerator - systematics
setupSigAToyGenerator = deepcopy(CFG)
setupSigAToyGenerator.update({
    'name': "sigAToyGenerator",
    'pdf': "f_sigA",
    'argAliasInDB': setupSigAFitter['argAliasInDB'],
    'saveAs': "sigAToyGenerator.root",
})
sigAToyGenerator = ToyGenerator(setupSigAToyGenerator)
@decorator_setExpectedEvents(["nSig"])
@decorator_initParameters
def sigAToyGenerator_customize(self):
    pass
sigAToyGenerator.customize = types.MethodType(sigAToyGenerator_customize, sigAToyGenerator)

if __name__ == '__main__':
    try:
        p.setSequence([pdfCollection.stdWspaceReader, sigToyGenerator])
        #  p.setSequence([pdfCollection.stdWspaceReader, bkgCombToyGenerator])
        p.beginSeq()
        p.runSeq()
        p.sourcemanager.get('ToyGenerator.mixedToy').Print()
    finally:
        p.endSeq()
