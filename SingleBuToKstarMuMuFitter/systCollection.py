#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=0 fdn=2 et:

from __future__ import print_function, division

import os
import sys
import math
import types
import shelve
import functools
import itertools
import tempfile
from copy import copy, deepcopy

import ROOT
import SingleBuToKstarMuMuFitter.cpp
import SingleBuToKstarMuMuFitter.varCollection as varCollection
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection
from SingleBuToKstarMuMuFitter.StdProcess import createNewProcess

from v2Fitter.Fitter.ObjProvider import ObjProvider
from v2Fitter.Fitter.FitterCore import FitterCore
from v2Fitter.Fitter.AbsToyStudier import AbsToyStudier
from v2Fitter.Fitter.DataReader import DataReader
from SingleBuToKstarMuMuFitter.anaSetup import modulePath, q2bins, bMassRegions, cuts_antiResVeto
from SingleBuToKstarMuMuFitter.StdFitter import StdFitter, unboundFlToFl, unboundAfbToAfb
from SingleBuToKstarMuMuFitter.EfficiencyFitter import EfficiencyFitter
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer
from SingleBuToKstarMuMuFitter.Plotter import Plotter

from argparse import ArgumentParser
p = createNewProcess()

# The standard format to keep the result in db file.
def updateToDB_altShape(args, tag, tagFiducial=None):
    """ Template db entry maker for syst """
    db = shelve.open(p.dbplayer.odbfile)
    try:
        if tagFiducial is None:
            fiducial_fl = unboundFlToFl(db['unboundFl']['getVal'])
            fiducial_afb = unboundAfbToAfb(db['unboundAfb']['getVal'], fiducial_fl)
        else:
            fiducial_fl = db["fl_{0}".format(tagFiducial)]['getVal']
            fiducial_afb = db["afb_{0}".format(tagFiducial)]['getVal']
    finally:
        db.close()

    afb = p.sourcemanager.get('afb').getVal()
    fl = p.sourcemanager.get('fl').getVal()
    syst_altShape = {}
    syst_altShape['syst_{0}_afb'.format(tag)] = {
        'afb': afb,
        'getError': math.fabs(afb - fiducial_afb),
        'getErrorHi': math.fabs(afb - fiducial_afb),
        'getErrorLo': -1 * math.fabs(afb - fiducial_afb),
    }
    syst_altShape['syst_{0}_fl'.format(tag)] = {
        'fl': fl,
        'getError': math.fabs(fl - fiducial_fl),
        'getErrorHi': math.fabs(fl - fiducial_fl),
        'getErrorLo': -1 * math.fabs(fl - fiducial_fl),
    }
    print(syst_altShape)

    if args.updateDB:
        print("INFO\t: Update syst uncertainty from {0} to database".format(tag))
        FitDBPlayer.UpdateToDB(p.dbplayer.odbfile, syst_altShape)

# Data-MC discrepancy in terms of efficiency map
# # Determinded by reweight the efficiency map derived from MC with a data-MC ratio from Jpsi CR.
# # Redo the whole fitting procedure using the modified efficiency map.
def create_histo_data2expt(kwargs=None):
    kwargs = {} if kwargs is None else kwargs
    wgtConfig = ["1*(fabs(Bmass-5.28)<0.06) - 0.5*(fabs(Bmass-5.11)<0.06) - 0.5*(fabs(Bmass-5.46)<0.06)",]

    # Data
    tree_data = ROOT.TChain("tree")
    for f in dataCollection.dataReaderCfg['ifile']:
        tree_data.Add(f)
    df_data = ROOT.RDataFrame(tree_data).Define('weight', *wgtConfig).Filter(cuts_antiResVeto).Filter(q2bins['jpsi']['cutString'])

    ptr_h_CosThetaL_data = df_data.Histo1D(("h_CosThetaL", "", 20, -1, 1), "CosThetaL", "weight")
    ptr_h_CosThetaK_data = df_data.Histo1D(("h_CosThetaK", "", 20, -1, 1), "CosThetaK", "weight")
    ptr_h2_sigA_data = df_data.Histo2D(
        ("h2_sigA_data", "",
            len(dataCollection.accXEffThetaLBins) - 1, dataCollection.accXEffThetaLBins, 
            len(dataCollection.accXEffThetaKBins) - 1, dataCollection.accXEffThetaKBins),
        "CosThetaL",
        "CosThetaK",
        "weight"
    )

    # (Unfiltered) MC(GEN)
    tree_expt = ROOT.TChain("tree")
    tree_expt.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/unfilteredJPSI_genonly/*.root")
    df_expt = ROOT.RDataFrame(tree_expt).Define('genWeight', "1").Filter("genQ2 > 8.68 && genQ2 < 10.09")

    ptr_h_CosThetaL_mc = df_expt.Histo1D(("h_genCosThetaL", "", 20, -1, 1), "genCosThetaL", "genWeight")
    ptr_h_CosThetaK_mc = df_expt.Histo1D(("h_genCosThetaK", "", 20, -1, 1), "genCosThetaK", "genWeight")
    ptr_h2_sigA_mc = df_expt.Histo2D(
        ("h2_sigA_mc", "",
            len(dataCollection.accXEffThetaLBins) - 1, dataCollection.accXEffThetaLBins, 
            len(dataCollection.accXEffThetaKBins) - 1, dataCollection.accXEffThetaKBins),
        "genCosThetaL",
        "genCosThetaK",
        "genWeight"
    )

    # Efficiency from MC(GEN+SIM)
    effiFile = ROOT.TFile(modulePath + "/input/wspace_bin2.root")
    effiWspace = effiFile.Get("wspace.bin2")
    effi_sigA = effiWspace.function("effi_sigA")
    effi_cosl = effiWspace.function("effi_cosl")
    effi_cosK = effiWspace.function("effi_cosK")
    FitDBPlayer.initFromDB(
        modulePath + "/testProcess/fitResults_bin2.db",
        effi_sigA.getParameters(ROOT.RooArgSet(varCollection.CosThetaK, varCollection.CosThetaL)))
    FitDBPlayer.initFromDB(
        modulePath + "/testProcess/fitResults_bin2.db",
        effi_cosl.getParameters(ROOT.RooArgSet(varCollection.CosThetaL)))
    FitDBPlayer.initFromDB(
        modulePath + "/testProcess/fitResults_bin2.db",
        effi_cosK.getParameters(ROOT.RooArgSet(varCollection.CosThetaK)))
    h2_effi_sigA = effi_sigA.createHistogram("h2_effi_sigA",
        varCollection.CosThetaL,
        ROOT.RooFit.Binning(dataCollection.rAccXEffThetaLBins),
        ROOT.RooFit.YVar(varCollection.CosThetaK, ROOT.RooFit.Binning(dataCollection.rAccXEffThetaKBins)))
    h_effi_cosl = effi_cosl.createHistogram("h_effi_cosl",
        varCollection.CosThetaL,
        ROOT.RooFit.Binning(20))
    h_effi_cosK = effi_cosK.createHistogram("h_effi_cosK",
        varCollection.CosThetaK,
        ROOT.RooFit.Binning(20))

    # Expected
    h2_sigA_expc = h2_effi_sigA.Clone("h2_sigA_expc")
    h2_sigA_expc.Reset("ICESM")
    for xBin, yBin in itertools.product(range(1, len(dataCollection.accXEffThetaLBins)), range(1, len(dataCollection.accXEffThetaKBins))):
        iBin = h2_sigA_expc.GetBin(xBin, yBin)
        h2_sigA_expc.SetBinContent(iBin, ptr_h2_sigA_mc.GetValue().GetBinContent(iBin) * h2_effi_sigA.GetBinContent(iBin))
    h2_sigA_expc.Scale(ptr_h_CosThetaL_data.Integral()/h2_sigA_expc.Integral())
    h_cosl_expc = h_effi_cosl.Clone("h_cosl_expc")
    h_cosK_expc = h_effi_cosK.Clone("h_cosK_expc")
    h_cosl_expc.Reset("ICESM")
    h_cosK_expc.Reset("ICESM")
    for iBin in range(1, 20+1):
        h_cosl_expc.SetBinContent(iBin, ptr_h_CosThetaL_mc.GetValue().GetBinContent(iBin) * h_effi_cosl.GetBinContent(iBin))
        h_cosK_expc.SetBinContent(iBin, ptr_h_CosThetaK_mc.GetValue().GetBinContent(iBin) * h_effi_cosK.GetBinContent(iBin))
    h_cosl_expc.Scale(ptr_h_CosThetaL_data.Integral(3,18)/h_cosl_expc.Integral(3,18))
    h_cosK_expc.Scale(ptr_h_CosThetaK_data.Integral(3,18)/h_cosK_expc.Integral(3,18))

    # Ratio
    h2_sigA_ratio = h2_effi_sigA.Clone("h2_sigA_ratio")
    h2_sigA_ratio.Reset("ICESM")
    for xBin, yBin in itertools.product(range(1, len(dataCollection.accXEffThetaLBins)), range(1, len(dataCollection.accXEffThetaKBins))):
        iBin = h2_sigA_ratio.GetBin(xBin, yBin)
        h2_sigA_ratio.SetBinContent(iBin, ptr_h2_sigA_data.GetValue().GetBinContent(iBin) / h2_sigA_expc.GetBinContent(iBin))
    h_cosl_ratio = h_effi_cosl.Clone("h_cosl_ratio")
    h_cosK_ratio = h_effi_cosK.Clone("h_cosK_ratio")
    h_cosl_ratio.Reset("ICESM")
    h_cosK_ratio.Reset("ICESM")
    for iBin in range(1, 20+1):
        h_cosl_ratio.SetBinContent(iBin, ptr_h_CosThetaL_data.GetValue().GetBinContent(iBin) / h_cosl_expc.GetBinContent(iBin))
        h_cosK_ratio.SetBinContent(iBin, ptr_h_CosThetaK_data.GetValue().GetBinContent(iBin) / h_cosK_expc.GetBinContent(iBin))

    fout = ROOT.TFile(modulePath + "/systCollection_dataMCDisc.root", "RECREATE")
    hists_to_write = [
        ptr_h_CosThetaL_data.GetValue(),
        ptr_h_CosThetaK_data.GetValue(),
        ptr_h_CosThetaL_mc.GetValue(),
        ptr_h_CosThetaK_mc.GetValue(),
        ptr_h2_sigA_data.GetValue(),
        ptr_h2_sigA_mc.GetValue(),
        h_effi_cosl,
        h_cosl_expc,
        h_cosl_ratio,
        h_effi_cosK,
        h_cosK_expc,
        h_cosK_ratio,
        h2_effi_sigA,
        h2_sigA_expc,
        h2_sigA_ratio,
    ]
    for h in hists_to_write:
        h.SetTitle("")
        h.Write()
    fout.Write()
    fout.Close()

def func_dataMCDisc(args):
    """Redo final fit with weighted efficiency map, where weight from JPsi CR."""
    if not os.path.exists(modulePath + "/systCollection_dataMCDisc.root"):
        create_histo_data2expt()

    weightFile= ROOT.TFile("systCollection_dataMCDisc.root")
    h_CosThetaL = weightFile.Get("h_CosThetaL")
    h_CosThetaK = weightFile.Get("h_CosThetaK")
    h_cosl_ratio = weightFile.Get("h_cosl_ratio")
    h_cosK_ratio = weightFile.Get("h_cosK_ratio")
    h2_sigA_expc = weightFile.Get("h2_sigA_expc")
    h2_sigA_data = weightFile.Get("h2_sigA_data")
    h2_weight = h2_sigA_expc.Clone("h2_sigA_expc")
    h2_weight.Reset("ICESM")
    for xBin, yBin in itertools.product(range(1, h2_weight.GetNbinsX()+1), range(1, h2_weight.GetNbinsY()+1)):
        iBin = h2_weight.GetBin(xBin, yBin)
        h2_weight.SetBinContent(iBin, h2_sigA_data.GetBinContent(iBin)/h2_sigA_expc.GetBinContent(iBin))
        # print("Weight in bin("+str(xBin)+","+str(yBin)+") = "+str(h2_weight.GetBinContent(iBin)))

    accXrecEffHistFile = ROOT.TFile(modulePath + "/data/accXrecEffHists_Run2012.root")
    h2_accXrec = accXrecEffHistFile.Get("h2_accXrec_{0}".format(args.binKey))
    h2_accXrec_weight = h2_accXrec.Clone("h2_accXrec_{0}_weight".format(args.binKey))
    h2_accXrec_weight.Reset("ICESM")
    for xBin, yBin in itertools.product(range(1, h2_weight.GetNbinsX()+1), range(1, h2_weight.GetNbinsY()+1)):
        iBin = h2_weight.GetBin(xBin, yBin)
        h2_accXrec_weight.SetBinContent(iBin, h2_accXrec.GetBinContent(iBin) * h2_weight.GetBinContent(iBin))
        h2_accXrec_weight.SetBinError(iBin, h2_accXrec.GetBinContent(iBin) / math.sqrt(h2_sigA_data.GetBinContent(iBin)))
        # h2_accXrec_weight.SetBinError(iBin, h2_accXrec.GetBinError(iBin)) # This is incorrect. The data-MC ratio has large error from data and it is dominent.

    p.sourcemanager.update("h2_accXrec_weight", h2_accXrec_weight)
    
    h_accXrec_ProjectionX = accXrecEffHistFile.Get("h_accXrec_{0}_ProjectionX".format(args.binKey))
    h_accXrec_ProjectionY = accXrecEffHistFile.Get("h_accXrec_{0}_ProjectionY".format(args.binKey))
    h_accXrec_ProjectionX_weight = h_accXrec_ProjectionX.Clone("h_accXrec_{0}_ProjectionX_weight".format(args.binKey))
    h_accXrec_ProjectionY_weight = h_accXrec_ProjectionY.Clone("h_accXrec_{0}_ProjectionY_weight".format(args.binKey))
    h_accXrec_ProjectionX_weight.Clone("ICESM")
    h_accXrec_ProjectionY_weight.Clone("ICESM")
    for iBin in range(1, 20+1):
        h_accXrec_ProjectionX_weight.SetBinContent(iBin, h_accXrec_ProjectionX.GetBinContent(iBin) * h_cosl_ratio.GetBinContent(iBin))
        h_accXrec_ProjectionY_weight.SetBinContent(iBin, h_accXrec_ProjectionY.GetBinContent(iBin) * h_cosK_ratio.GetBinContent(iBin))
        h_accXrec_ProjectionX_weight.SetBinError(iBin, h_accXrec_ProjectionX_weight.GetBinContent(iBin)/math.sqrt(h_CosThetaL.GetBinError(iBin)))
        h_accXrec_ProjectionY_weight.SetBinError(iBin, h_accXrec_ProjectionY_weight.GetBinContent(iBin)/math.sqrt(h_CosThetaK.GetBinError(iBin)))
    p.sourcemanager.update("h_accXrec_ProjectionX_weight", h_accXrec_ProjectionX_weight)
    p.sourcemanager.update("h_accXrec_ProjectionY_weight", h_accXrec_ProjectionY_weight)

    setupWeightEffiFitter = deepcopy(fitCollection.setupEffiFitter)
    setupWeightEffiFitter.update({
        'hdata': "h2_accXrec_weight",
        'dataX': "h_accXrec_ProjectionX_weight",
        'dataY': "h_accXrec_ProjectionY_weight",
        'noDraw': False, # True in uncertainty estimation.
        'saveToDB': False, # No overwrite default values.
    })
    weightEffiFitter = EfficiencyFitter(setupWeightEffiFitter)

    setupFinalAltEffiFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltEffiFitter.update({
        'argAliasInDB': {'unboundAfb': 'unboundAfb_dataMCDisc', 'unboundFl': 'unboundFl_dataMCDisc', 'fs': 'fs_dataMCDisc', 'as': 'as_dataMCDisc', 'nSig': 'nSig_dataMCDisc', 'nBkgComb': 'nBkgComb_dataMCDisc'},
        'argAliasFromDB': copy(fitCollection.setupFinalFitter['argAliasInDB']),
        'saveToDB': False,
    })
    setupFinalAltEffiFitter['argAliasFromDB'].update({pattern: None for pattern in setupWeightEffiFitter['argPattern']})
    finalAltEffiFitter = StdFitter(setupFinalAltEffiFitter)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.effiHistReader,
        dataCollection.dataReader,
        weightEffiFitter,
        finalAltEffiFitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "dataMCDisc")
    finally:
        p.endSeq()
    accXrecEffHistFile.Close()
    weightFile.Close()
    pass

# # Use histogram instead of smooth map. This actually conclude multiple sources.
def func_dataMCDisc2(args):
    if not os.path.exists(modulePath + "/systCollection_dataMCDisc.root"):
        create_histo_data2expt()

    weightFile= ROOT.TFile("systCollection_dataMCDisc.root")
    h2_sigA_expc = weightFile.Get("h2_sigA_expc")
    h2_sigA_data = weightFile.Get("h2_sigA_data")
    h2_weight = h2_sigA_expc.Clone("h2_sigA_expc")
    h2_weight.Reset("ICESM")
    for xBin, yBin in itertools.product(range(1, h2_weight.GetNbinsX()+1), range(1, h2_weight.GetNbinsY()+1)):
        iBin = h2_weight.GetBin(xBin, yBin)
        h2_weight.SetBinContent(iBin, h2_sigA_data.GetBinContent(iBin)/h2_sigA_expc.GetBinContent(iBin))

    accXrecEffHistFile = ROOT.TFile(modulePath + "/data/accXrecEffHists_Run2012.root")
    h2_accXrec = accXrecEffHistFile.Get("h2_accXrec_{0}".format(args.binKey))
    h2_accXrec_weight = h2_accXrec.Clone("h2_accXrec_{0}_weight".format(args.binKey))
    h2_accXrec_weight.Reset("ICESM")
    for xBin, yBin in itertools.product(range(1, h2_weight.GetNbinsX()+1), range(1, h2_weight.GetNbinsY()+1)):
        iBin = h2_weight.GetBin(xBin, yBin)
        h2_accXrec_weight.SetBinContent(iBin, h2_accXrec.GetBinContent(iBin) * h2_weight.GetBinContent(iBin))
        h2_accXrec_weight.SetBinError(iBin, h2_accXrec.GetBinError(iBin))
    accXrec_weight = ROOT.RooDataHist("accXrec_weight", "", ROOT.RooArgList(varCollection.CosThetaL, varCollection.CosThetaK), ROOT.RooFit.Import(h2_accXrec_weight))

    def buildFinalAltDataMC(self):
        effi_sigAAltDataMC = ROOT.RooHistFunc("effi_sigAAltDataMC", "", ROOT.RooArgSet(varCollection.CosThetaL, varCollection.CosThetaK), accXrec_weight)
        f_sig2DAltDataMC = ROOT.RooEffProd("f_sig2DAltDataMC", "", self.process.sourcemanager.get('f_sigA'), effi_sigAAltDataMC)
        f_sig3DAltDataMC = ROOT.RooProdPdf("f_sig3DAltDataMC", "", self.process.sourcemanager.get('f_sigM'), f_sig2DAltDataMC)
        nSig = self.process.sourcemanager.get("nSig")
        nBkgComb = self.process.sourcemanager.get("nBkgComb")
        f_finalAltDataMC = ROOT.RooAddPdf("f_finalAltDataMC", "", ROOT.RooArgList(f_sig3DAltDataMC, self.process.sourcemanager.get('f_bkgComb')), ROOT.RooArgList(nSig, nBkgComb))
        self.cfg['source']['effi_sigAAltDataMC'] = effi_sigAAltDataMC
        self.cfg['source']['f_sig2DAltDataMC'] = f_sig2DAltDataMC
        self.cfg['source']['f_sig3DAltDataMC'] = f_sig3DAltDataMC
        self.cfg['source']['f_finalAltDataMC'] = f_finalAltDataMC

    setupFinalAltDataMCBuilder = deepcopy(ObjProvider.templateConfig())
    setupFinalAltDataMCBuilder.update({'name': "finalAltDataMCBuilder"})
    setupFinalAltDataMCBuilder['obj']['f_finalAltDataMC'] = [buildFinalAltDataMC]
    finalAltDataMCBuilder = ObjProvider(setupFinalAltDataMCBuilder)

    setupFinalAltEffiFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltEffiFitter.update({
        'pdf': 'f_finalAltDataMC',
        'argAliasInDB': {'unboundAfb': 'unboundAfb_dataMCDisc2', 'unboundFl': 'unboundFl_dataMCDisc2', 'fs': 'fs_dataMCDisc2', 'as': 'as_dataMCDisc2', 'nSig': 'nSig_dataMCDisc2', 'nBkgComb': 'nBkgComb_dataMCDisc2'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalAltEffiFitter = StdFitter(setupFinalAltEffiFitter)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.effiHistReader,
        finalAltDataMCBuilder,
        dataCollection.dataReader,
        finalAltEffiFitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "dataMCDisc2")
    finally:
        p.endSeq()
    accXrecEffHistFile.Close()
    weightFile.Close()
    pass

# # Fit the efficiency histogram produced by generator shape and sub

# Limited MC size
# # Determinded by varying efficiency map with FitDBPlayer.fluctuateFromDB.
def func_randEffi(args):
    """ Typically less than 5% """
    setupFinalRandEffiFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalRandEffiFitter.update({
        'FitMinos': [False, ()],
        'argAliasInDB': {'unboundAfb': 'unboundAfb_randEffi', 'unboundFl': 'unboundFl_randEffi', 'fs': 'fs_randEffi', 'as': 'as_randEffi', 'nSig': 'nSig_randEffi', 'nBkgComb': 'nBkgComb_randEffi'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalRandEffiFitter = StdFitter(setupFinalRandEffiFitter)

    def preFitSteps_randEffi(self):
        self.args = self.pdf.getParameters(self.data)
        self._preFitSteps_initFromDB()

        # Fluctuate cross-term correction w/o considering the correlation
        effiArgs = ROOT.RooArgSet()
        FitterCore.ArgLooper(self.args, lambda iArg: effiArgs.add(iArg), targetArgs=[r"x\d{1,2}", r"l\d", r"k\d"])
        FitDBPlayer.fluctuateFromDB(self.process.dbplayer.odbfile, effiArgs, self.cfg['argAliasInDB'])

        self._preFitSteps_vetoSmallFs()
        self._preFitSteps_preFit()

    finalRandEffiFitter._preFitSteps = types.MethodType(preFitSteps_randEffi, finalRandEffiFitter)

    if args.isBatchTask:
        os.chdir(os.path.abspath("/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/"))
        foutName = "syst_randEffi_{0}_{1}.root".format(q2bins[args.binKey]['label'], next(tempfile._get_candidate_names()))
    else:
        foutName = "syst_randEffi_{0}.root".format(q2bins[args.binKey]['label'])
    class effiStudier(AbsToyStudier):
        def _preSetsLoop(self):
            self.hist_afb = ROOT.TH1F("hist_afb", "", 300, -0.75, 0.75)
            self.hist_afb.GetXaxis().SetTitle("A_{FB}")
            self.hist_fl = ROOT.TH1F("hist_fl", "", 200, 0., 1.)
            self.hist_fl.GetXaxis().SetTitle("F_{L}")

        def _preRunFitSteps(self, setIndex):
            pass

        def _postRunFitSteps(self, setIndex):
            if self.fitter.fitResult["{0}.migrad".format(self.fitter.name)]['status'] == 0:
                afb = self.process.sourcemanager.get('afb')
                fl = self.process.sourcemanager.get('fl')
                self.hist_afb.Fill(afb.getVal())
                self.hist_fl.Fill(fl.getVal())

        def _postSetsLoop(self):
            fout = ROOT.TFile(foutName, "RECREATE")
            fout.cd()
            self.hist_afb.Write()
            self.hist_fl.Write()
            fout.Close()

        def getSubDataEntries(self, setIndex):
            return 1

        def getSubData(self):
            while True:
                yield self.data

    setupStudier = deepcopy(effiStudier.templateConfig())
    setupStudier.update({
        'name': "effiStudier",
        'data': "dataReader.Fit",
        'fitter': finalRandEffiFitter,
        'nSetOfToys': 20 if args.isBatchTask else 200,
    })
    studier = effiStudier(setupStudier)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        studier,
    ])

    try:
        p.beginSeq()
        if os.path.exists("{0}".format(foutName)):
            print("{0} exists, skip fitting procedure".format(foutName))
        else:
            p.runSeq()

        if not args.isBatchTask:
            # ROOT.gStyle.SetOptStat("r")
            ROOT.gStyle.SetOptFit(11)

            fin = ROOT.TFile("{0}".format(foutName))

            hist_fl = fin.Get("hist_fl")
            hist_fl.UseCurrentStyle()
            gaus_fl = ROOT.TF1("gaus_fl", "gaus(0)", 0, 1)
            hist_fl.Fit(gaus_fl, "WLI")

            hist_afb = fin.Get("hist_afb")
            hist_afb.UseCurrentStyle()
            gaus_afb = ROOT.TF1("gaus_afb", "gaus(0)", -0.75, 0.75)
            hist_afb.Fit(gaus_afb, "WLI")

            syst_randEffi = {
                'syst_randEffi_fl': {
                    'getError': gaus_fl.GetParameter(2),
                    'getErrorHi': gaus_fl.GetParameter(2),
                    'getErrorLo': -gaus_fl.GetParameter(2),
                },
                'syst_randEffi_afb': {
                    'getError': gaus_afb.GetParameter(2),
                    'getErrorHi': gaus_afb.GetParameter(2),
                    'getErrorLo': -gaus_afb.GetParameter(2),
                }
            }
            print(syst_randEffi)

            if args.updatePlot:
                canvas = Plotter.canvas.cd()
                hist_afb.GetXaxis().SetTitle("A_{FB}")
                hist_afb.Draw("HIST")
                gaus_afb.Draw("SAME")
                Plotter.latexCMSMark()
                Plotter.latexQ2(args.binKey)
                Plotter.latexCMSExtra()
                canvas.Print("syst_randEffi_afb_{0}.pdf".format(q2bins[args.binKey]['label']))

                hist_fl.GetXaxis().SetTitle("F_{L}")
                hist_fl.Draw("HIST")
                gaus_fl.Draw("SAME")
                Plotter.latexCMSMark()
                Plotter.latexQ2(args.binKey)
                Plotter.latexCMSExtra()
                canvas.Print("syst_randEffi_fl_{0}.pdf".format(q2bins[args.binKey]['label']))

            if args.updateDB:
                FitDBPlayer.UpdateToDB(p.dbplayer.odbfile, syst_randEffi)
    finally:
        p.endSeq()

# Alternate efficiency map
# # Use uncorrelated efficiency map and compare the difference
def func_altEffi(args):
    """ Typically less than 1% """
    setupFinalAltEffiFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltEffiFitter.update({
        'argAliasInDB': {'unboundAfb': 'unboundAfb_altEffi', 'unboundFl': 'unboundFl_altEffi', 'fs': 'fs_altEffi', 'as': 'as_altEffi', 'nSig': 'nSig_altEffi', 'nBkgComb': 'nBkgComb_altEffi'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalAltEffiFitter = StdFitter(setupFinalAltEffiFitter)
    def _preFitSteps_altEffi(self):
        StdFitter._preFitSteps(self)
        hasXTerm = self.args.find("hasXTerm")
        hasXTerm.setVal(0)
    finalAltEffiFitter._preFitSteps = types.MethodType(_preFitSteps_altEffi, finalAltEffiFitter)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        finalAltEffiFitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "altEffi")
    finally:
        p.endSeq()

# # Use histogram instead of smooth map.
def func_altEffi2(args):
    setupFinalAltEffiFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltEffiFitter.update({
        'pdf': 'f_finalAltEffi',
        'argAliasInDB': {'unboundAfb': 'unboundAfb_altEffi2', 'unboundFl': 'unboundFl_altEffi2', 'fs': 'fs_altEffi2', 'as': 'as_altEffi2', 'nSig': 'nSig_altEffi2', 'nBkgComb': 'nBkgComb_altEffi2'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalAltEffiFitter = StdFitter(setupFinalAltEffiFitter)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        finalAltEffiFitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "altEffi2")
    finally:
        p.endSeq()

# Simulation mismodeling
# # Quote the difference between fitting results of unfiltered GEN and that of high stat RECO.
def func_simMismodel(args):
    p.setSequence([])
    try:
        p.beginSeq()
        db = shelve.open(p.dbplayer.odbfile)
        fl_GEN = unboundFlToFl(db['unboundFl_GEN']['getVal'])
        fl_RECO = unboundFlToFl(db['unboundFl_RECO']['getVal'])
        afb_GEN = unboundAfbToAfb(db['unboundAfb_GEN']['getVal'], fl_GEN)
        afb_RECO = unboundAfbToAfb(db['unboundAfb_RECO']['getVal'], fl_RECO)
        db.close()
        syst_simMismodel = {
            'syst_simMismodel_fl': {
                'getError': math.fabs(fl_GEN - fl_RECO),
                'getErrorHi': math.fabs(fl_GEN - fl_RECO),
                'getErrorLo': -math.fabs(fl_GEN - fl_RECO),
            },
            'syst_simMismodel_afb': {
                'getError': math.fabs(afb_GEN - afb_RECO),
                'getErrorHi': math.fabs(afb_GEN - afb_RECO),
                'getErrorLo': -math.fabs(afb_GEN - afb_RECO),
            }
        }
        print(syst_simMismodel)

        if args.updateDB:
            FitDBPlayer.UpdateToDB(p.dbplayer.odbfile, syst_simMismodel)
    finally:
        p.endSeq()

# Alternate sigM shape
# # Use single Gaussian instead of double Gaussian
def func_altSigM(args):
    """ Not used """
    setupFinalAltSigMFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltSigMFitter.update({
        'argAliasInDB': {'unboundAfb': 'unboundAfb_altSigM', 'unboundFl': 'unboundFl_altSigM', 'fs': 'fs_altSigM', 'as': 'as_altSigM', 'nSig': 'nSig_altSigM', 'nBkgComb': 'nBkgComb_altSigM'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalAltSigMFitter = StdFitter(setupFinalAltSigMFitter)
    def _preFitSteps_altSigM(self):
        StdFitter._preFitSteps(self)
        sigM_frac = self.args.find("sigM_frac")
        sigM_frac.setVal(0)
    finalAltSigMFitter._preFitSteps = types.MethodType(_preFitSteps_altSigM, finalAltSigMFitter)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        finalAltSigMFitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "altSigM")
    finally:
        p.endSeq()

# Alternate S-P interference
# # The S-wave is estimated to be around 5%.
# # However, given low stats, the fitted fraction is usually less than 1%.
# # Fix the fraction at 5% and compare the difference
def func_altSP(args, fsRate=0.05):
    """ Set fs to 5% instead of 0% """
    setupFinalAltSPFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltSPFitter.update({
        'argAliasInDB': {'unboundAfb': 'unboundAfb_altSP', 'unboundFl': 'unboundFl_altSP', 'fs': 'fs_altSP', 'as': 'as_altSP', 'nSig': 'nSig_altSP', 'nBkgComb': 'nBkgComb_altSP'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalAltSPFitter = StdFitter(setupFinalAltSPFitter)
    def _preFitSteps_vetoSmallFs_altSP(self):
        """ fs is usually negligible, set the alternative fraction to a fixed rate. """
        if "fs" in self.cfg.get('argPattern'):
            fs = self.args.find("fs")
            transAs = self.args.find("transAs")
            fs.setVal(fsRate)
            fs.setConstant(True)
            transAs.setVal(0)
            transAs.setConstant(False)

    finalAltSPFitter._preFitSteps_vetoSmallFs = types.MethodType(_preFitSteps_vetoSmallFs_altSP, finalAltSPFitter)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        finalAltSPFitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "altSP")
    finally:
        p.endSeq()

# Alternate bkgCombM shape
# # versus expo+linear
def func_altBkgCombM(args):
    """ Not used """
    setupFinalAltBkgCombMFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltBkgCombMFitter.update({
        'pdf': "f_finalAltBkgCombM",
        'argAliasInDB': {'unboundAfb': 'unboundAfb_altBkgCombM', 'unboundFl': 'unboundFl_altBkgCombM', 'fs': 'fs_altBkgCombM', 'as': 'as_altBkgCombM', 'nSig': 'nSig_altBkgCombM', 'nBkgComb': 'nBkgComb_altBkgCombM'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalAltBkgCombMFitter = StdFitter(setupFinalAltBkgCombMFitter)
    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        finalAltBkgCombMFitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "altBkgCombM")
    finally:
        p.endSeq()

# Alternate bkgCombA shape
# # Smooth function versus analytic function
def func_altBkgCombA(args):
    """ Typically less than 10% """
    setupFinalAltBkgCombAFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltBkgCombAFitter.update({
        'pdf': "f_finalAltBkgCombA",
        'argAliasInDB': {'unboundAfb': 'unboundAfb_altBkgCombA', 'unboundFl': 'unboundFl_altBkgCombA', 'fs': 'fs_altBkgCombA', 'as': 'as_altBkgCombA', 'nSig': 'nSig_altBkgCombA', 'nBkgComb': 'nBkgComb_altBkgCombA'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': True, # For later cross check.
    })
    finalAltBkgCombAFitter = StdFitter(setupFinalAltBkgCombAFitter)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        finalAltBkgCombAFitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "altBkgCombA")
    finally:
        p.endSeq()

# # Ananlytic function from different sideband
def func_altBkgCombA2(args):
    """ Background described with ananlytic function from different sidebands. """
    setupBkgCombA2Fitter = deepcopy(fitCollection.setupBkgCombAFitter)
    setupBkgCombA2Fitter.update({
        'data': 'dataReader.innerSB',
    })
    setupBkgCombA2Fitter['argAliasInDB'] = {
        "bkgCombL_c1": "bkgCombL_c1_altBkgCombA2",
        "bkgCombL_c2": "bkgCombL_c2_altBkgCombA2",
        "bkgCombL_c3": "bkgCombL_c3_altBkgCombA2",
        "bkgCombL_c4": "bkgCombL_c4_altBkgCombA2",
        "bkgCombL_c5": "bkgCombL_c5_altBkgCombA2",
        "bkgCombK_c1": "bkgCombK_c1_altBkgCombA2",
        "bkgCombK_c2": "bkgCombK_c2_altBkgCombA2",
        "bkgCombK_c3": "bkgCombK_c3_altBkgCombA2",
        "bkgCombK_c4": "bkgCombK_c4_altBkgCombA2",
        "bkgCombK_c5": "bkgCombK_c5_altBkgCombA2",
    }
    bkgCombA2Fitter = StdFitter(setupBkgCombA2Fitter)

    setupFinalAltBkgCombA2Fitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltBkgCombA2Fitter.update({
        'argAliasInDB': {'unboundAfb': 'unboundAfb_altBkgCombA2', 'unboundFl': 'unboundFl_altBkgCombA2', 'fs': 'fs_altBkgCombA2', 'as': 'as_altBkgCombA2', 'nSig': 'nSig_altBkgCombA2', 'nBkgComb': 'nBkgComb_altBkgCombA2'},
        'argAliasFromDB': copy(fitCollection.setupFinalFitter['argAliasInDB']),
    })
    setupFinalAltBkgCombA2Fitter['argAliasFromDB'].update({pattern: None for pattern in setupBkgCombA2Fitter['argPattern']})
    finalAltBkgCombA2Fitter = StdFitter(setupFinalAltBkgCombA2Fitter)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        bkgCombA2Fitter,
        finalAltBkgCombA2Fitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "altBkgCombA2")
    finally:
        p.endSeq()

# # Vary the parameters of analytic model by 1 sigma
def func_flucBkgCombA(args):
    """ DEPRECATED """
    tag = "flucBkgCombA"
    tagFiducial = None
    p.beginSeq()
    db = shelve.open(p.dbplayer.odbfile)
    p.endSeq()
    try:
        if tagFiducial is None:
            fiducial_fl = unboundFlToFl(db['unboundFl']['getVal'])
            fiducial_afb = unboundAfbToAfb(db['unboundAfb']['getVal'], fiducial_fl)
        else:
            fiducial_fl = db["fl_{0}".format(tagFiducial)]['getVal']
            fiducial_afb = db["afb_{0}".format(tagFiducial)]['getVal']
    finally:
        db.close()

    setupFinalFlucBkgCombAFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalFlucBkgCombAFitter.update({
        'FitMinos': [False, ()],
        'argAliasInDB': {'unboundAfb': 'unboundAfb_flucBkgCombA', 'unboundFl': 'unboundFl_flucBkgCombA', 'fs': 'fs_flucBkgCombA', 'as': 'as_flucBkgCombA', 'nSig': 'nSig_flucBkgCombA', 'nBkgComb': 'nBkgComb_flucBkgCombA'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalFlucBkgCombAFitter = StdFitter(setupFinalFlucBkgCombAFitter)

    flucArgs = {} # Update this from pdfCollection.py
    flucArgs['belowJpsi'] = [
            "bkgCombK_c1",
            "bkgCombK_c2",
            "bkgCombK_c3",
            "bkgCombL_c1",
            "bkgCombL_c2",
            "bkgCombL_c3",
            "bkgCombL_c4",
            "bkgCombL_c5",]
    flucArgs['betweenPeaks'] = [
            "bkgCombK_c1",
            "bkgCombK_c2",
            "bkgCombK_c3",
            "bkgCombK_c4",
            "bkgCombL_c1",
            "bkgCombL_c2",
            "bkgCombL_c3",
            "bkgCombL_c4",
            "bkgCombL_c5",]
    flucArgs['abovePsi2s'] = [
            "bkgCombK_c1",
            "bkgCombK_c2",
            "bkgCombK_c3",
            "bkgCombL_c1",]
    flucArgs['summary'] = flucArgs['belowJpsi']
    sumOfSquaredAfbBias = 0.
    sumOfSquaredFlBias = 0.
    for argName in flucArgs[args.binKey]:
        maxAfbBias = 0.
        maxFlBias = 0.
        for biasSignificance in [1., -1.]:
            def preFitSteps_flucBkgCombA(self):
                print(argName, biasSignificance)
                self.args = self.pdf.getParameters(self.data)
                self._preFitSteps_initFromDB()
                self.ToggleConstVar(self.args, False, self.cfg.get('argPattern'))

                # Shift the parameter by biasSignificance
                FitterCore.ArgLooper(self.args, lambda iArg: iArg.setVal(iArg.getVal()+biasSignificance*iArg.getError()), targetArgs=[argName])

                self._preFitSteps_vetoSmallFs()
                self._preFitSteps_preFit()
            finalFlucBkgCombAFitter._preFitSteps = types.MethodType(preFitSteps_flucBkgCombA, finalFlucBkgCombAFitter)

            pp = createNewProcess()
            pp.setSequence([
                pdfCollection.stdWspaceReader,
                dataCollection.dataReader,
                finalFlucBkgCombAFitter,
            ])
            try:
                pp.beginSeq()
                pp.runSeq()

                # Keep a record of the biases, ignore the case of large bias since it hits boundary.
                afb = pp.sourcemanager.get('afb').getVal()
                afbBias = math.fabs(afb - fiducial_afb)
                maxAfbBias = afbBias if afbBias > maxAfbBias and afbBias < 0.1 else maxAfbBias
                
                fl = pp.sourcemanager.get('fl').getVal()
                flBias = math.fabs(fl - fiducial_fl)
                maxFlBias = flBias if flBias > maxFlBias and flBias < 0.1 else maxFlBias

            finally:
                pp.endSeq()
        sumOfSquaredAfbBias += maxAfbBias*maxAfbBias
        sumOfSquaredFlBias += maxFlBias*maxFlBias
        print("INFO\t: Uncertainty from {0} is {1}(AFB) and {2}(FL)".format(argName, maxAfbBias, maxFlBias))

    # Update summarized result to db, modified from updateToDB_altShape
    syst_altShape = {}
    syst_altShape['syst_{0}_afb'.format(tag)] = {
        'getError': math.sqrt(sumOfSquaredAfbBias),
        'getErrorHi': math.sqrt(sumOfSquaredAfbBias),
        'getErrorLo': -1 * math.sqrt(sumOfSquaredAfbBias),
    }
    syst_altShape['syst_{0}_fl'.format(tag)] = {
        'getError': math.sqrt(sumOfSquaredFlBias),
        'getErrorHi': math.sqrt(sumOfSquaredFlBias),
        'getErrorLo': -1 * math.sqrt(sumOfSquaredFlBias),
    }
    print(syst_altShape)

    if args.updateDB:
        print("INFO\t: Update syst uncertainty from {0} to database".format(tag))
        FitDBPlayer.UpdateToDB(p.dbplayer.odbfile, syst_altShape)

# # Determinded by varying analytic description with correlation matrix considered.
def func_randBkgCombA(args):
    """ Determinded by varying analytic description with correlation matrix considered. Typically less than 5% """
    bkgCombAFitter = fitCollection.bkgCombAFitter
    bkgCombAFitter.cfg['saveToDB'] = False

    setupFinalRandBkgCombAFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalRandBkgCombAFitter.update({
        'FitMinos': [False, ()],
        'argAliasInDB': {'unboundAfb': 'unboundAfb_randBkgCombA', 'unboundFl': 'unboundFl_randBkgCombA', 'fs': 'fs_randBkgCombA', 'as': 'as_randBkgCombA', 'nSig': 'nSig_randBkgCombA', 'nBkgComb': 'nBkgComb_randBkgCombA'},
        'argAliasFromDB': fitCollection.setupFinalFitter['argAliasInDB'],
        'saveToDB': False,
    })
    finalRandBkgCombAFitter = StdFitter(setupFinalRandBkgCombAFitter)

    def preFitSteps_randBkgCombA(self):
        self.args = self.pdf.getParameters(self.data)
        self._preFitSteps_initFromDB()

        # Fluctuate background model, in which the correlation of coefficients is considered.
        # This treatment is necessary when strong correlation is seen in HESSE step
        fitResult = self.process.sourcemanager.get("{0}.minosResult".format(bkgCombAFitter.name))
        randomizedPars = fitResult.randomizePars()
        args_it = randomizedPars.createIterator()
        arg = args_it.Next()
        while arg:
            arg.Print()
            FitterCore.ArgLooper(self.args, lambda iArg: iArg.setVal(arg.getVal()), [arg.GetName()])
            arg = args_it.Next()

        self._preFitSteps_vetoSmallFs()
        self._preFitSteps_preFit()

    finalRandBkgCombAFitter._preFitSteps = types.MethodType(preFitSteps_randBkgCombA, finalRandBkgCombAFitter)

    if args.isBatchTask:
        os.chdir(os.path.abspath("/afs/cern.ch/work/p/pchen/public/BuToKstarMuMu/v2Fitter/SingleBuToKstarMuMuFitter/"))
        foutName = "syst_randBkgCombA_{0}_{1}.root".format(q2bins[args.binKey]['label'], next(tempfile._get_candidate_names()))
    else:
        foutName = "syst_randBkgCombA_{0}.root".format(q2bins[args.binKey]['label'])
    class bkgCombAStudier(AbsToyStudier):
        def _preSetsLoop(self):
            self.hist_afb = ROOT.TH1F("hist_afb", "", 300, -0.75, 0.75)
            self.hist_afb.GetXaxis().SetTitle("A_{FB}")
            self.hist_fl = ROOT.TH1F("hist_fl", "", 200, 0., 1.)
            self.hist_fl.GetXaxis().SetTitle("F_{L}")
            self.hist_nSig = ROOT.TH1F("hist_nSig", "", 200, 0., 200.)
            self.hist_nBkgComb = ROOT.TH1F("hist_nBkgComb", "", 200, 0., 1000.)

        def _preRunFitSteps(self, setIndex):
            pass

        def _postRunFitSteps(self, setIndex):
            if self.fitter.fitResult["{0}.migrad".format(self.fitter.name)]['status'] == 0:
                fl = self.process.sourcemanager.get('fl')
                self.hist_fl.Fill(fl.getVal())
                afb = self.process.sourcemanager.get('afb')
                self.hist_afb.Fill(afb.getVal())
                nSig = self.process.sourcemanager.get('nSig')
                self.hist_nSig.Fill(nSig.getVal())
                nBkgComb = self.process.sourcemanager.get('nBkgComb')
                self.hist_nBkgComb.Fill(nBkgComb.getVal())

        def _postSetsLoop(self):
            fout = ROOT.TFile(foutName, "RECREATE")
            fout.cd()
            self.hist_afb.Write()
            self.hist_fl.Write()
            fout.Close()
            print("Create output file {0}".format(foutName))

        def getSubDataEntries(self, setIndex):
            return 1

        def getSubData(self):
            while True:
                yield self.data

    setupStudier = deepcopy(bkgCombAStudier.templateConfig())
    setupStudier.update({
        'name': "bkgCombAStudier",
        'data': "dataReader.Fit",
        'fitter': finalRandBkgCombAFitter,
        'nSetOfToys': 20 if args.isBatchTask else 200,
    })
    studier = bkgCombAStudier(setupStudier)

    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataCollection.dataReader,
        bkgCombAFitter,
        studier,
    ])

    try:
        p.beginSeq()
        if os.path.exists("{0}".format(foutName)):
            print("{0} exists, skip fitting procedure".format(foutName))
        else:
            p.runSeq()

        if not args.isBatchTask:
            # ROOT.gStyle.SetOptStat("r")
            ROOT.gStyle.SetOptFit(11)

            fin = ROOT.TFile("{0}".format(foutName))

            hist_fl = fin.Get("hist_fl")
            hist_fl.UseCurrentStyle()
            gaus_fl = ROOT.TF1("gaus_fl", "gaus(0)", 0, 1)
            hist_fl.Fit(gaus_fl, "WLI")

            hist_afb = fin.Get("hist_afb")
            hist_afb.UseCurrentStyle()
            gaus_afb = ROOT.TF1("gaus_afb", "gaus(0)", -0.75, 0.75)
            hist_afb.Fit(gaus_afb, "WLI")

            syst_randBkgCombA = {
                'syst_randBkgCombA_fl': {
                    'getError': gaus_fl.GetParameter(2),
                    'getErrorHi': gaus_fl.GetParameter(2),
                    'getErrorLo': -gaus_fl.GetParameter(2),
                },
                'syst_randBkgCombA_afb': {
                    'getError': gaus_afb.GetParameter(2),
                    'getErrorHi': gaus_afb.GetParameter(2),
                    'getErrorLo': -gaus_afb.GetParameter(2),
                }
            }
            print(syst_randBkgCombA)

            if args.updatePlot:
                canvas = Plotter.canvas.cd()
                hist_afb.GetXaxis().SetTitle("A_{FB}")
                hist_afb.Draw("HIST")
                gaus_afb.Draw("SAME")
                Plotter.latexCMSMark()
                Plotter.latexQ2(args.binKey)
                Plotter.latexCMSExtra()
                canvas.Print("syst_randBkgCombA_afb_{0}.pdf".format(q2bins[args.binKey]['label']))

                hist_fl.GetXaxis().SetTitle("F_{L}")
                hist_fl.Draw("HIST")
                gaus_fl.Draw("SAME")
                Plotter.latexCMSMark()
                Plotter.latexQ2(args.binKey)
                Plotter.latexCMSExtra()
                canvas.Print("syst_randBkgCombA_fl_{0}.pdf".format(q2bins[args.binKey]['label']))

            if args.updateDB:
                FitDBPlayer.UpdateToDB(p.dbplayer.odbfile, syst_randBkgCombA)

    finally:
        p.endSeq()

def func_mergeBkgCombShape(args):
    """ Merge the effects on combinatorial background shape. """
    syst_sources = ['syst_altBkgCombA', 'syst_altBkgCombA2', 'syst_randBkgCombA']
    
    p.setSequence([])
    try:
        p.beginSeq()
        db = shelve.open(p.dbplayer.odbfile)
        syst_bkgCombShape = {
            'syst_bkgCombShape_fl': {
                'getError': math.sqrt(sum([pow(db[v + '_fl']['getError'], 2) for v in syst_sources])),
                'getErrorHi': math.sqrt(sum([pow(db[v + '_fl']['getErrorHi'], 2) for v in syst_sources])),
                'getErrorLo': -math.sqrt(sum([pow(db[v + '_fl']['getErrorLo'], 2) for v in syst_sources])),
            },
            'syst_bkgCombShape_afb': {
                'getError': math.sqrt(sum([pow(db[v + '_afb']['getError'], 2) for v in syst_sources])),
                'getErrorHi': math.sqrt(sum([pow(db[v + '_afb']['getErrorHi'], 2) for v in syst_sources])),
                'getErrorLo': -math.sqrt(sum([pow(db[v + '_afb']['getErrorLo'], 2) for v in syst_sources])),
            }
        }
        print(syst_bkgCombShape)

        if args.updateDB:
            FitDBPlayer.UpdateToDB(p.dbplayer.odbfile, syst_bkgCombShape)
    finally:
        p.endSeq()

# Bmass range
# # Vary Fit range
def func_altFitRange(args):
    """ Take wider Fit region """
    dataReaderCfg = deepcopy(dataCollection.dataReaderCfg)
    dataReaderCfg.update({
        'preloadFile': None
    })
    dataReader = DataReader(dataReaderCfg)
    dataReader.customize = types.MethodType(
        functools.partial(dataCollection.customizeOne,
                          targetBMassRegion=['^altFit$']),
        dataReader
    )
    fitterCfg = deepcopy(fitCollection.setupFinalFitter)
    fitterCfg.update({
        'data': "dataReader.altFit",
        'createNLLOpt': [ROOT.RooFit.Range("altFit")],
        'saveToDB': False,
    })
    fitter = StdFitter(fitterCfg)
    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataReader,
        fitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "altFitRange")
    finally:
        p.endSeq()

# Mis-include B -> Jpsi+X backgroud
# # Remove LSB from Fit region
def func_vetoJpsiX(args):
    """ DEPRECATED. Remvoe LSB from Fit region """
    dataReaderCfg = deepcopy(dataCollection.dataReaderCfg)
    dataReaderCfg.update({
        'preloadFile': None
    })
    dataReader = DataReader(dataReaderCfg)
    dataReader.customize = types.MethodType(
        functools.partial(dataCollection.customizeOne,
                          targetBMassRegion=['^altFit_vetoJpsiX$']),
        dataReader
    )
    fitterCfg = deepcopy(fitCollection.setupFinalFitter)
    fitterCfg.update({
        'data': "dataReader.altFit_vetoJpsiX",
        'createNLLOpt': [ROOT.RooFit.Extended(True), ROOT.RooFit.Range("altFit_vetoJpsiX")],
        'saveToDB': False,
    })
    fitter = StdFitter(fitterCfg)
    p.setSequence([
        pdfCollection.stdWspaceReader,
        dataReader,
        fitter,
    ])

    try:
        p.beginSeq()
        p.runSeq()

        updateToDB_altShape(args, "vetoJpsiX")
    finally:
        p.endSeq()

if __name__ == '__main__':
    parser = ArgumentParser(
        description="""
"""
    )
    parser.add_argument(
        '-b',
        '--binKey',
        dest='binKey',
        default=p.cfg['binKey'],
        help="q2 bin",
    )
    parser.add_argument(
        '--noUpdatePlot',
        dest='updatePlot',
        action='store_false',
        help="Want to update plots? (Default: True)",
    )
    parser.add_argument(
        '--noUpdateDB',
        dest='updateDB',
        action='store_false',
        help="Want to update to db file? (Default: True)",
    )
    parser.add_argument(
        '--batchTask',
        dest='isBatchTask',
        action='store_true',
        help="Is the job a batch task? (Default: False)",
    )
    parser.set_defaults(work_dir=p.work_dir)

    subparsers = parser.add_subparsers(help="Functions", dest='Function_name')

    subparser_dataMCDisc = subparsers.add_parser('dataMCDisc')
    subparser_dataMCDisc.set_defaults(func=func_dataMCDisc)

    # subparser_dataMCDisc2 = subparsers.add_parser('dataMCDisc2')
    # subparser_dataMCDisc2.set_defaults(func=func_dataMCDisc2)

    subparser_randEffi = subparsers.add_parser('randEffi')
    subparser_randEffi.set_defaults(func=func_randEffi)

    # subparser_altEffi = subparsers.add_parser('altEffi')
    # subparser_altEffi.set_defaults(func=func_altEffi)

    # subparser_altEffi2 = subparsers.add_parser('altEffi2')
    # subparser_altEffi2.set_defaults(func=func_altEffi2)

    subparser_simMismodel = subparsers.add_parser('simMismodel')
    subparser_simMismodel.set_defaults(func=func_simMismodel)

    # subparser_altSigM = subparsers.add_parser('altSigM')
    # subparser_altSigM.set_defaults(func=func_altSigM)

    subparser_altSP = subparsers.add_parser('altSP')
    subparser_altSP.set_defaults(func=func_altSP)

    # subparser_altBkgCombM = subparsers.add_parser('altBkgCombM')
    # subparser_altBkgCombM.set_defaults(func=func_altBkgCombM)

    subparser_altBkgCombA = subparsers.add_parser('altBkgCombA')
    subparser_altBkgCombA.set_defaults(func=func_altBkgCombA)

    subparser_altBkgCombA2 = subparsers.add_parser('altBkgCombA2')
    subparser_altBkgCombA2.set_defaults(func=func_altBkgCombA2)
    
    # subparser_flucBkgCombA = subparsers.add_parser('flucBkgCombA')
    # subparser_flucBkgCombA.set_defaults(func=func_flucBkgCombA)

    subparser_randBkgCombA = subparsers.add_parser('randBkgCombA')
    subparser_randBkgCombA.set_defaults(func=func_randBkgCombA)

    subparser_mergeBkgCombShape = subparsers.add_parser('mergeBkgCombShape')
    subparser_mergeBkgCombShape.set_defaults(func=func_mergeBkgCombShape)
    
    # subparser_vetoJpsiX = subparsers.add_parser('vetoJpsiX')
    # subparser_vetoJpsiX.set_defaults(func=func_vetoJpsiX)

    # subparser_altFitRange = subparsers.add_parser('altFitRange')
    # subparser_altFitRange.set_defaults(func=func_altFitRange)

    args = parser.parse_args()
    p.cfg['binKey'] = args.binKey

    args.func(args)
    sys.exit()
