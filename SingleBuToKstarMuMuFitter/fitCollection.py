#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 sts=4 fdm=indent fdl=0 fdn=3 ft=python et:

import types
import functools
from copy import deepcopy

import ROOT

import SingleBuToKstarMuMuFitter.cpp
from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.StdFitter import StdFitter
from SingleBuToKstarMuMuFitter.EfficiencyFitter import EfficiencyFitter
from SingleBuToKstarMuMuFitter.FitDBPlayer import register_dbfile

from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels

from SingleBuToKstarMuMuFitter.anaSetup import processCfg, modulePath
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection

setupTemplateFitter = StdFitter.templateConfig()

setupEffiFitter = deepcopy(EfficiencyFitter.templateConfig())
setupEffiFitter.update({
    'name': "effiFitter",
    'data': "effiHistReader.accXrec",
    'dataX': "effiHistReader.h_accXrec_fine_ProjectionX",
    'dataY': "effiHistReader.h_accXrec_fine_ProjectionY",
    'pdf': "effi_sigA",
    'pdfX': "effi_cosl",
    'pdfY': "effi_cosK",
})
effiFitter = EfficiencyFitter(setupEffiFitter)

setupSigMFitter = deepcopy(setupTemplateFitter)
setupSigMFitter.update({
    'name': "sigMFitter",
    'data': "sigMCReader.Fit",
    'pdf': "f_sigM",
    'argPattern': ['sigMGauss[12]_sigma', 'sigMGauss_mean', 'sigM_frac'],
    'createNLLOpt': [],
    'argAliasInDB': {'sigMGauss1_sigma': 'sigMGauss1_sigma_RECO', 'sigMGauss2_sigma': 'sigMGauss2_sigma_RECO', 'sigMGauss_mean': 'sigMGauss_mean_RECO', 'sigM_frac': 'sigM_frac_RECO'},
})
sigMFitter = StdFitter(setupSigMFitter)

setupSigAFitter = deepcopy(setupTemplateFitter)
setupSigAFitter.update({
    'name': "sigAFitter",
    'data': "sigMCGENReader.Fit",
    'pdf': "f_sigA",
    'argPattern': ['unboundAfb', 'unboundFl'],
    'createNLLOpt': [],
    'argAliasInDB': {'unboundAfb': 'unboundAfb_GEN', 'unboundFl': 'unboundFl_GEN'},
})
sigAFitter = StdFitter(setupSigAFitter)
def sigAFitter_bookPdfData(self):
    StdFitter._bookPdfData(self)
    self.data.changeObservableName("genCosThetaK", "CosThetaK")
    self.data.changeObservableName("genCosThetaL", "CosThetaL")
sigAFitter._bookPdfData = types.MethodType(sigAFitter_bookPdfData, sigAFitter)
def sigAFitter_preFitSteps(self):
    self._preFitSteps_initFromDB()
    FitterCore.ArgLooper(self.args, lambda arg: arg.setVal(0), ["fs", "transAs"])
    FitterCore.ArgLooper(self.args, lambda arg: arg.Print())
    FitterCore.ToggleConstVar(self.args, True, ["fs", "transAs"])
sigAFitter._preFitSteps = types.MethodType(sigAFitter_preFitSteps, sigAFitter)

setupSig2DFitter = deepcopy(setupTemplateFitter)
setupSig2DFitter.update({
    'name': "sig2DFitter",
    'data': "sigMCReader.Fit",
    'pdf': "f_sig2D",
    'argPattern': ['unboundAfb', 'unboundFl'],
    'createNLLOpt': [],
    'argAliasInDB': {'unboundAfb': 'unboundAfb_RECO', 'unboundFl': 'unboundFl_RECO'},
})
sig2DFitter = StdFitter(setupSig2DFitter)

setupBkgCombAFitter = deepcopy(setupTemplateFitter)
setupBkgCombAFitter.update({
    'name': "bkgCombAFitter",
    'data': "dataReader.SB",
    'pdf': "f_bkgCombA",
    'argPattern': [r'bkgComb[KL]_c[\d]+', ],
    'FitHesse': False,
    'FitMinos': [False, ()],
    'createNLLOpt': [],
})
bkgCombAFitter = StdFitter(setupBkgCombAFitter)

setupBkgCombMFitter = deepcopy(setupTemplateFitter)
setupBkgCombMFitter.update({
    'name': "bkgCombMFitter",
    'data': "dataReader.SB",
    'pdf': "f_bkgCombM",
    'argPattern': [r'bkgCombM_c[\d]+', ],
    'FitHesse': False,
    'FitMinos': [False, ()],
    'createNLLOpt': [],
})
bkgCombMFitter = StdFitter(setupBkgCombMFitter)

setupFinalFitter = deepcopy(setupTemplateFitter)
setupFinalFitter.update({
    'name': "finalFitter",
    'data': "dataReader.Fit",
    'pdf': "f_final",
    'argPattern': ['nSig', 'unboundAfb', 'unboundFl', 'fs', 'transAs', 'nBkgComb', r'bkgCombM_c[\d]+'],
    'createNLLOpt': [ROOT.RooFit.Extended(), ],
    #  'FitMinos': [True, ('nSig', 'unboundAfb', 'unboundFl', 'nBkgComb')],
})
finalFitter = StdFitter(setupFinalFitter)

customized_register_dbfile = functools.partial(register_dbfile, inputDir="{0}/input/selected/".format(modulePath))
def customize(self):
    customized_register_dbfile(self)
for fitter in [effiFitter, sigMFitter, sigAFitter, sig2DFitter, bkgCombAFitter, bkgCombMFitter, finalFitter]:
    fitter.customize = types.MethodType(customize, fitter)

if __name__ == '__main__':
    p = Process("testFitCollection", "testProcess", processCfg)
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
    #  p.setSequence([dataCollection.effiHistReader, pdfCollection.stdWspaceReader, effiFitter])
    #  p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sigMFitter])
    #  p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sig2DFitter])
    #  p.setSequence([dataCollection.dataReader, pdfCollection.stdWspaceReader, bkgCombAFitter])
    p.setSequence([])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
