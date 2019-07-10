#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdn=3 et:

from __future__ import print_function

import os
import sys
import math
import types
import shelve
import functools
from copy import deepcopy

import ROOT
import SingleBuToKstarMuMuFitter.cpp

from v2Fitter.Fitter.FitterCore import FitterCore
from v2Fitter.Fitter.AbsToyStudier import AbsToyStudier
from v2Fitter.Fitter.DataReader import DataReader
from SingleBuToKstarMuMuFitter.anaSetup import q2bins, cut_kshortWindow
from SingleBuToKstarMuMuFitter.StdFitter import StdFitter, unboundFlToFl, unboundAfbToAfb
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer
from SingleBuToKstarMuMuFitter.plotCollection import Plotter, plotter

import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection

from SingleBuToKstarMuMuFitter.StdProcess import p

from argparse import ArgumentParser

# Limited MC size
# # Determinded by varying efficiency map with FitDBPlayer.fluctuateFromDB.
def func_randEffi(args):
    """ Typically less than 5% """
    setupFinalRandEffiFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalRandEffiFitter.update({
        'FitMinos': [False, ()],
        'argAliasInDB': {'afb': 'afb_randEffi', 'fl': 'fl_randEffi', 'fs': 'fs_randEffi', 'as': 'as_randEffi'},
        'saveToDB': False,
    })
    finalRandEffiFitter = StdFitter(setupFinalRandEffiFitter)

    def preFitSteps_randEffi(self):
        self.args = self.pdf.getParameters(self.data)
        self._preFitSteps_initFromDB()

        # Fluctuate cross-term correction
        effiArgs = ROOT.RooArgSet()
        FitterCore.ArgLooper(self.args, lambda iArg: effiArgs.add(iArg), targetArgs=[r"x\d{1,2}"])
        FitDBPlayer.fluctuateFromDB(self.process.dbplayer.odbfile, effiArgs, self.cfg['argAliasInDB'])

        self._preFitSteps_vetoSmallFs()
        self._preFitSteps_preFit()

    finalRandEffiFitter._preFitSteps = types.MethodType(preFitSteps_randEffi, finalRandEffiFitter)

    foutName = "syst_randEffi_{0}.root".format(q2bins[args.binKey]['label'])
    class effiStudier(AbsToyStudier):
        def _preSetsLoop(self):
            self.hist_afb = ROOT.TH1F("hist_afb", "", 300, -0.75, 0.75)
            self.hist_afb.GetXaxis().SetTitle("A_{{FB}}")
            self.hist_fl = ROOT.TH1F("hist_fl", "", 200, 0., 1.)
            self.hist_fl.GetXaxis().SetTitle("F_{{L}}")

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
        'nSetOfToys': 200,
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

        fin = ROOT.TFile("{0}".format(foutName))

        hist_fl = fin.Get("hist_fl")
        gaus_fl = ROOT.TF1("gaus_fl", "gaus(0)", 0, 1)
        hist_fl.Fit(gaus_fl, "WI")

        hist_afb = fin.Get("hist_afb")
        gaus_afb = ROOT.TF1("gaus_afb", "gaus(0)", -0.75, 0.75)
        hist_afb.Fit(gaus_afb, "WI")

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
            hist_afb.Draw("HIST")
            Plotter.latexCMSMark()
            Plotter.latexCMSExtra()
            Plotter.latexCMSSim()
            canvas.Print("syst_randEffi_afb_{0}.pdf".format(q2bins[args.binKey]['label']))

            hist_fl.GetXaxis().SetTitle("F_{{L}}")
            hist_fl.Draw("HIST")
            Plotter.latexCMSMark()
            Plotter.latexCMSExtra()
            Plotter.latexCMSSim()
            canvas.Print("syst_randEffi_fl_{0}.pdf".format(q2bins[args.binKey]['label']))

        if args.updateDB:
            FitDBPlayer.UpdateToDB(p.dbplayer.odbfile, syst_randEffi)
    finally:
        p.endSeq()

# Alternate efficiency map
# # Use uncorrelated efficiency map and compare the difference
def updateToDB_altShape(args, tag):
    """ Template db entry maker for syst """
    db = shelve.open(p.dbplayer.odbfile)
    nominal_fl = unboundFlToFl(db['unboundFl']['getVal'])
    nominal_afb = unboundAfbToAfb(db['unboundAfb']['getVal'], nominal_fl)
    db.close()
    afb = p.sourcemanager.get('afb').getVal()
    fl = p.sourcemanager.get('fl').getVal()
    syst_altShape = {}
    syst_altShape['syst_{0}_afb'.format(tag)] = {
        'getError': math.fabs(afb - nominal_afb),
        'getErrorHi': math.fabs(afb - nominal_afb),
        'getErrorLo': -1 * math.fabs(afb - nominal_afb),
    }
    syst_altShape['syst_{0}_fl'.format(tag)] = {
        'getError': math.fabs(fl - nominal_fl),
        'getErrorHi': math.fabs(fl - nominal_fl),
        'getErrorLo': -1 * math.fabs(fl - nominal_fl),
    }
    print(syst_altShape)

    if args.updateDB:
        FitDBPlayer.UpdateToDB(p.dbplayer.odbfile, syst_altShape)

def func_altEffi(args):
    """ Typically less than 1% """
    setupFinalAltEffiFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltEffiFitter.update({
        'argAliasInDB': {'afb': 'afb_altEffi', 'fl': 'fl_altEffi', 'fs': 'fs_altEffi', 'as': 'as_altEffi'},
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
        'argAliasInDB': {'afb': 'afb_altSigM', 'fl': 'fl_altSigM', 'fs': 'fs_altSigM', 'as': 'as_altSigM'},
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
def func_altSP(args):
    """ Set fs to 5% instead of 0% """
    setupFinalAltSPFitter = deepcopy(fitCollection.setupFinalFitter)
    setupFinalAltSPFitter.update({
        'argAliasInDB': {'afb': 'afb_altSP', 'fl': 'fl_altSP', 'fs': 'fs_altSP', 'as': 'as_altSP'},
        'saveToDB': False,
    })
    finalAltSPFitter = StdFitter(setupFinalAltSPFitter)
    def _preFitSteps_vetoSmallFs_altSP(self):
        """ fs is usually negligible, set the alternative fraction to 0.05 """
        if "fs" in self.cfg.get('argPattern'):
            fs = self.args.find("fs")
            transAs = self.args.find("transAs")
            fs.setVal(0.05)
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
        'argAliasInDB': {'afb': 'afb_altBkgCombM', 'fl': 'fl_altBkgCombM', 'fs': 'fs_altBkgCombM', 'as': 'as_altBkgCombM'},
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
        'argAliasInDB': {'afb': 'afb_altBkgCombA', 'fl': 'fl_altBkgCombA', 'fs': 'fs_altBkgCombA', 'as': 'as_altBkgCombA'},
        'saveToDB': False,
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
                          targetBMassRegion=['^altFit$'],
                          extraCuts=cut_kshortWindow),
        dataReader
    )
    fitterCfg = deepcopy(fitCollection.setupFinalFitter)
    fitterCfg.update({
        'data': "dataReader.altFit",
        'saveToDB': False
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
    """ Remvoe LSB from Fit region """
    dataReaderCfg = deepcopy(dataCollection.dataReaderCfg)
    dataReaderCfg.update({
        'preloadFile': None
    })
    dataReader = DataReader(dataReaderCfg)
    dataReader.customize = types.MethodType(
        functools.partial(dataCollection.customizeOne,
                          targetBMassRegion=['altFit_vetoJpsiX'],
                          extraCuts=cut_kshortWindow),
        dataReader
    )
    fitterCfg = deepcopy(fitCollection.setupFinalFitter)
    fitterCfg.update({
        'data': "dataReader.altFit_vetoJpsiX",
        'saveToDB': False
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

# Make latex table
def func_makeLatexTable(args):
    """ Make table. Force the input db files from StdProcess.dbplayer.absInputDir """
    for var in ["fl", "afb"]:
        dbKeyToLine = {
            'syst_randEffi': [r"Limited MC size"],
            'syst_altEffi': [r"Eff.\ mapping"],
            'syst_simMismodel': [r"Simu.\ mismodel"],
            'syst_altSP': [r"$S$ - $P$ wave interf.\ "],
            'syst_altBkgCombA': [r"Comb.\ Bkg.\ shape"],
            'syst_vetoJpsiX': [r"$B$ mass range"],
        }
        totalErrorLine = ["Total"]
        for binKey in ['belowJpsi', 'betweenPeaks', 'abovePsi2s', 'summary']:
            db = shelve.open("{0}/fitResults_{1}.db".format(p.dbplayer.absInputDir, q2bins[binKey]['label']))
            totalSystErr = 0.
            for systKey, latexLine in dbKeyToLine.items():
                err = db["{0}_{1}".format(systKey, var)]['getError']
                latexLine.append("{0:.03f}".format(err))
                totalSystErr += pow(err, 2)
            db.close()
            totalErrorLine.append("{0:.03f}".format(math.sqrt(totalSystErr)))

        print("Printing table of syst. unc. for {0}".format(var))
        indent = "  "
        print(indent * 2 + r"\begin{tabular}{|l|c|c|c|c|}")
        print(indent * 3 + r"\hline")
        print(indent * 3 + r"Syst.\ err.\ $\backslash$ $q^2$ bin & 1 & 3 & 5 & 0 \\")
        print(indent * 3 + r"\hline")
        print(indent * 3 + r"\hline")
        print(indent * 3 + r"\multicolumn{5}{|c|}{Uncorrelated systematic uncertainties} \\")
        print(indent * 3 + r"\hline")
        for systKey, latexLine in dbKeyToLine.items():
            print(indent * 3 + " & ".join(latexLine) + r" \\")
        print(indent * 3 + r"\hline")
        print(indent * 3 + " & ".join(totalErrorLine) + r" \\")
        print(indent * 3 + r"\hline")
        print(indent * 2 + r"\end{tabular}")

if __name__ == '__main__':
    parser = ArgumentParser(
        description="""
"""
    )
    parser.add_argument(
        '--binKey',
        dest='binKey',
        default=p.cfg['binKey'],
        help="q2 bin",
    )
    parser.add_argument(
        '--updatePlot',
        dest='updatePlot',
        action='store_false',
        help="Want to update plots? (Default: True)",
    )
    parser.add_argument(
        '--updateDB',
        dest='updateDB',
        action='store_false',
        help="Want to update to db file? (Default: True)",
    )
    parser.set_defaults(work_dir=p.work_dir)

    subparsers = parser.add_subparsers(help="Functions", dest='Function_name')

    subparser_randEffi = subparsers.add_parser('randEffi')
    subparser_randEffi.set_defaults(func=func_randEffi)

    subparser_altEffi = subparsers.add_parser('altEffi')
    subparser_altEffi.set_defaults(func=func_altEffi)

    subparser_simMismodel = subparsers.add_parser('simMismodel')
    subparser_simMismodel.set_defaults(func=func_simMismodel)

    #  subparser_altSigM = subparsers.add_parser('altSigM')
    #  subparser_altSigM.set_defaults(func=func_altSigM)

    subparser_altSP = subparsers.add_parser('altSP')
    subparser_altSP.set_defaults(func=func_altSP)

    #  subparser_altBkgCombM = subparsers.add_parser('altBkgCombM')
    #  subparser_altBkgCombM.set_defaults(func=func_altBkgCombM)

    subparser_altBkgCombA = subparsers.add_parser('altBkgCombA')
    subparser_altBkgCombA.set_defaults(func=func_altBkgCombA)

    subparser_vetoJpsiX = subparsers.add_parser('vetoJpsiX')
    subparser_vetoJpsiX.set_defaults(func=func_vetoJpsiX)

    #  subparser_altFitRange = subparsers.add_parser('altFitRange')
    #  subparser_altFitRange.set_defaults(func=func_altFitRange)

    subparser_makeLatexTable = subparsers.add_parser('makeLatexTable')
    subparser_makeLatexTable.set_defaults(func=func_makeLatexTable)

    args = parser.parse_args()
    p.cfg['binKey'] = args.binKey

    args.func(args)
    sys.exit()
