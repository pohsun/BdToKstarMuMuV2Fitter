#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 sts=4 fdm=indent fdl=0 fdn=3 ft=python et:

import types
from copy import deepcopy

import ROOT

import SingleBuToKstarMuMuFitter.cpp
from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.StdFitter import StdFitter, flToUnboundFl, afbToUnboundAfb
from SingleBuToKstarMuMuFitter.EfficiencyFitter import EfficiencyFitter

from SingleBuToKstarMuMuFitter.StdProcess import p
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
    self.process.dbplayer.saveSMPrediction()
    StdFitter._bookPdfData(self)
    self.data.changeObservableName("genCosThetaK", "CosThetaK")
    self.data.changeObservableName("genCosThetaL", "CosThetaL")
sigAFitter._bookPdfData = types.MethodType(sigAFitter_bookPdfData, sigAFitter)

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
    'FitMinos': [True, ()],
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
    'createNLLOpt': [ROOT.RooFit.Extended(True), ],
    'FitMinos': [True, ('nSig', 'unboundAfb', 'unboundFl', 'nBkgComb')],
    'argAliasInDB': dict(setupSigMFitter['argAliasInDB'].items() + setupSigAFitter['argAliasInDB'].items()),
    'argAliasWhenSaveToDB': False, # Init with argAlias, save to db without argAlias.
})
finalFitter = StdFitter(setupFinalFitter)

setupBkgJpsiMFitter = deepcopy(setupSigMFitter)
setupBkgJpsiMFitter.update({
    'name': "bkgJpsiMFitter",
    'data': "bkgJpsiMCReader.Fit_noResVeto",
    'argAliasInDB': {'sigMGauss1_sigma': 'sigMGauss1_sigma_bkgJpsi', 'sigMGauss2_sigma': 'sigMGauss2_sigma_bkgJpsi', 'sigMGauss_mean': 'sigMGauss_mean_bkgJpsi', 'sigM_frac': 'sigM_frac_bkgJpsi'},
})
bkgJpsiMFitter = StdFitter(setupBkgJpsiMFitter)

setupBkgPsi2sMFitter = deepcopy(setupBkgJpsiMFitter)
setupBkgPsi2sMFitter.update({
    'name': "bkgPsi2sMFitter",
    'data': "bkgPsi2sMCReader.Fit_noResVeto",
    'argAliasInDB': {'sigMGauss1_sigma': 'sigMGauss1_sigma_bkgPsi2s', 'sigMGauss2_sigma': 'sigMGauss2_sigma_bkgPsi2s', 'sigMGauss_mean': 'sigMGauss_mean_bkgPsi2s', 'sigM_frac': 'sigM_frac_bkgPsi2s'},
})
bkgPsi2sMFitter = StdFitter(setupBkgPsi2sMFitter)

if __name__ == '__main__':
    #  p.setSequence([dataCollection.effiHistReader, pdfCollection.stdWspaceReader, effiFitter])
    #  p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sigMFitter])
    #  p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sig2DFitter])
    #  p.setSequence([dataCollection.bkgJpsiMCReader, pdfCollection.stdWspaceReader, bkgJpsiMFitter])
    #  p.setSequence([dataCollection.bkgPsi2sMCReader, pdfCollection.stdWspaceReader, bkgPsi2sMFitter])
    #  p.setSequence([dataCollection.dataReader, pdfCollection.stdWspaceReader, bkgCombAFitter])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
