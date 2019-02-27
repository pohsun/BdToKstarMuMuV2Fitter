#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 27 Feb 2019 18:46 

import re, types
from copy import deepcopy
import functools

import ROOT

from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter import SingleBuToKstarMuMuFitter

from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels

from anaSetup import q2bins
import dataCollection
import pdfCollection

setupTemplateFitter = SingleBuToKstarMuMuFitter.templateConfig()

setupEffiFitter = deepcopy(setupTemplateFitter)
setupEffiFitter.update({
    'name': "effiFitter",
    'data': "effiHistReader.accXrec",
    'pdf': "effi_sigA",
    'createNLLOpt': [],
})
effiFitter = SingleBuToKstarMuMuFitter(setupEffiFitter)
def effiFitter_preFitSteps(self):
    """Prefit uncorrelated term"""
    args = self.pdf.getParameters(self.data)
    self._initArgs(args)
    self.ToggleConstVar(args, isConst=True)

    # Disable xTerm correction
    args.find('hasXTerm').setVal(0)
    args.find('effi_norm').setConstant(False)
    self.ToggleConstVar(args, isConst=True, targetArgs=[r"^x\d+$"])
    self.ToggleConstVar(args, isConst=False, targetArgs=[r"^k\d+$"])
    self.ToggleConstVar(args, isConst=False, targetArgs=[r"^l\d+$"])
    for i in range(6):
        self.minimizer.migrad()

    # Fix uncorrelated term and for later update with xTerms in main fit step
    args.find('hasXTerm').setVal(1)
    args.find('effi_norm').setConstant(True)
    self.ToggleConstVar(args, isConst=True, targetArgs=[r"^l\d+$"])
    self.ToggleConstVar(args, isConst=True, targetArgs=[r"^k\d+$"])
    self.ToggleConstVar(args, isConst=False, targetArgs=[r"^x\d+$"])

effiFitter._preFitSteps = types.MethodType(effiFitter_preFitSteps, effiFitter)

setupSigMFitter = deepcopy(setupTemplateFitter)
setupSigMFitter.update({
    'name': "sigMFitter",
    'data': "sigMCReader.Fit",
    'pdf': "f_sigM",
    'argPattern': ['sigMGauss[12]_sigma', 'sigMGauss_mean', 'sigM_frac'],
    'createNLLOpt': [],
})
sigMFitter = SingleBuToKstarMuMuFitter(setupSigMFitter)

setupSig2DFitter = deepcopy(setupTemplateFitter)
setupSig2DFitter.update({
    'name': "sig2DFitter",
    'data': "sigMCReader.Fit",
    'pdf': "f_sig2D",
    'argPattern': ['afb', 'fl', 'fs', 'as'],
    'createNLLOpt': [],
})
sig2DFitter = SingleBuToKstarMuMuFitter(setupSig2DFitter)


setupBkgCombAFitter = deepcopy(setupTemplateFitter)
setupBkgCombAFitter.update({
    'name': "bkgCombAFitter",
    'data': "dataReader.SB",
    'pdf': "f_bkgCombA",
    'FitHesse':False,
    'FitMinos': [False, ()],
    'createNLLOpt': [],
})
bkgCombAFitter = SingleBuToKstarMuMuFitter(setupBkgCombAFitter)

setupFinalFitter = deepcopy(setupTemplateFitter)
setupFinalFitter.update({
    'name': "finalFitter",
    'data': "dataReader.Fit",
    'pdf': "f_final",
    'argPattern': ['afb', 'fl', 'fs', 'as'],
    'createNLLOpt': [],
})
finalFitter = SingleBuToKstarMuMuFitter(setupFinalFitter)

def customize(binKey):
    for fitter in [effiFitter, sigMFitter, sig2DFitter, bkgCombAFitter, finalFitter]:
        fitter.cfg['db'] = "fitResults_{0}.db".format(q2bins[binKey]['label'])

if __name__ == '__main__':
    binKey = 'belowJpsi'
    dataCollection.customize(binKey, ['SR', 'LSB', 'USB', 'test'])
    pdfCollection.customize(binKey)
    customize(binKey)
    p = Process("testFitCollection", "testProcess")
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
    p.setSequence([dataCollection.effiHistReader, pdfCollection.stdWspaceReader, effiFitter])
    # p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sigMFitter])
    # p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sig2DFitter])
    # p.setSequence([dataCollection.dataReader, pdfCollection.stdWspaceReader, bkgCombAFitter])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
