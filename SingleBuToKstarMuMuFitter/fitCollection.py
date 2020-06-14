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
setupTemplateFitter.update({
    'createNLLOpt': [ROOT.RooFit.Range("Fit")], # This works only when the range is labelled during making wspace from `pdfCollection.py`.
})

setupEffiFitter = deepcopy(EfficiencyFitter.templateConfig())
setupEffiFitter.update({
    'name': "effiFitter",
    'data': "effiHistReader.accXrec",
    'dataX': "effiHistReader.h_accXrec_fine_ProjectionX",
    'dataY': "effiHistReader.h_accXrec_fine_ProjectionY",
    'pdf': "effi_sigA",
    'pdfX': "effi_cosl",
    'pdfY': "effi_cosK",
    'argPattern': [r"^l\d+$", r"^k\d+$", r"x(\d{1,2})", "effi_norm", "hasXTerm"], # Not used in EfficiencyFitter, but useful if init is not needed in StdFitter.
})
effiFitter = EfficiencyFitter(setupEffiFitter)

setupSigMFitter = deepcopy(setupTemplateFitter)
setupSigMFitter.update({
    'name': "sigMFitter",
    'data': "sigMCReader.Fit",
    'pdf': "f_sigM",
    'argPattern': ['sigMGauss[12]_sigma', 'sigMGauss_mean', 'sigM_frac'],
    'argAliasInDB': {'sigMGauss1_sigma': 'sigMGauss1_sigma_RECO', 'sigMGauss2_sigma': 'sigMGauss2_sigma_RECO', 'sigMGauss_mean': 'sigMGauss_mean_RECO', 'sigM_frac': 'sigM_frac_RECO'},
})
sigMFitter = StdFitter(setupSigMFitter)

setupSigAFitter = deepcopy(setupTemplateFitter)
setupSigAFitter.update({
    'name': "sigAFitter",
    'data': "sigMCGENReader.Fit",
    'pdf': "f_sigA",
    'argPattern': ['unboundAfb', 'unboundFl'],
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
})
bkgCombMFitter = StdFitter(setupBkgCombMFitter)

setupFinalFitter = deepcopy(setupTemplateFitter)
setupFinalFitter.update({
    'name': "finalFitter",
    'data': "dataReader.Fit",
    'pdf': "f_final",
    'argPattern': ['nSig', 'unboundAfb', 'unboundFl', 'fs', 'transAs', 'nBkgComb', r'bkgCombM_c[\d]+'],
    'createNLLOpt': [ROOT.RooFit.Extended(True), ROOT.RooFit.Range("Fit")],
    'FitMinos': [True, ('nSig', 'unboundAfb', 'unboundFl', 'nBkgComb')],
    'argAliasFromDB': dict(setupSigMFitter['argAliasInDB'].items() + setupSigAFitter['argAliasInDB'].items()),
    'argAliasInDB': {'nSig': 'nSig', 'unboundAfb': 'unboundAfb', 'unboundFl': 'unboundFl', 'fs': 'fs', 'transAs': 'transAs', 'nBkgComb': 'nBkgComb'},
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


# For additional tests
setupFinalFitter_altFit0 = deepcopy(setupFinalFitter)
setupFinalFitter_altFit0.update({
    'createNLLOpt': [ROOT.RooFit.Extended(True), ROOT.RooFit.Range("altFit0")],
    'argAliasInDB': {'nSig': 'nSig_altFit0', 'unboundAfb': 'unboundAfb_altFit0', 'unboundFl': 'unboundFl_altFit0', 'fs': 'fs_altFit0', 'transAs': 'transAs_altFit0', 'nBkgComb': 'nBkgComb_altFit0'},
})
finalFitter_altFit0 = StdFitter(setupFinalFitter_altFit0)

setupFinalFitter_altFit1 = deepcopy(setupFinalFitter)
setupFinalFitter_altFit1.update({
    'createNLLOpt': [ROOT.RooFit.Extended(True), ROOT.RooFit.Range("altFit1")],
    'argAliasInDB': {'nSig': 'nSig_altFit1', 'unboundAfb': 'unboundAfb_altFit1', 'unboundFl': 'unboundFl_altFit1', 'fs': 'fs_altFit1', 'transAs': 'transAs_altFit1', 'nBkgComb': 'nBkgComb_altFit1'},
})
finalFitter_altFit1 = StdFitter(setupFinalFitter_altFit1)

setupFinalFitter_altFit2 = deepcopy(setupFinalFitter)
setupFinalFitter_altFit2.update({
    'pdf': "f_final_altFit2",
    'createNLLOpt': [ROOT.RooFit.Extended(True), ROOT.RooFit.Range("Fit")],
    'argAliasInDB': {'nSig': 'nSig_altFit2', 'unboundAfb': 'unboundAfb_altFit2', 'unboundFl': 'unboundFl_altFit2', 'fs': 'fs_altFit2', 'transAs': 'transAs_altFit2', 'nBkgComb': 'nBkgComb_altFit2'},
})
finalFitter_altFit2 = StdFitter(setupFinalFitter_altFit2)

setupFinalFitter_altFit3 = deepcopy(setupFinalFitter)
setupFinalFitter_altFit3.update({
    'pdf': "f_final_altFit3",
    'createNLLOpt': [ROOT.RooFit.Extended(True), ROOT.RooFit.Range("Fit")],
    'argAliasInDB': {'nSig': 'nSig_altFit3', 'unboundAfb': 'unboundAfb_altFit3', 'unboundFl': 'unboundFl_altFit3', 'fs': 'fs_altFit3', 'transAs': 'transAs_altFit3', 'nBkgComb': 'nBkgComb_altFit3'},
})
finalFitter_altFit3 = StdFitter(setupFinalFitter_altFit3)

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
