#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 sts=4 fdm=indent fdl=0 fdn=3 ft=python et:

import os
import re
import math
import types
import functools
import shelve
from array import array

import ROOT

import SingleBuToKstarMuMuFitter.cpp
from v2Fitter.FlowControl.Path import Path
from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.anaSetup import q2bins, modulePath, bMassRegions
from SingleBuToKstarMuMuFitter.StdFitter import unboundFlToFl, unboundAfbToAfb, flToUnboundFl, afbToUnboundAfb

from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer
from SingleBuToKstarMuMuFitter.varCollection import Bmass, CosThetaK, CosThetaL, Mumumass, Kstarmass, Kshortmass

from SingleBuToKstarMuMuFitter.StdProcess import p, setStyle
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection

class Plotter(Path):
    """The plotter"""
    setStyle()
    canvas = ROOT.TCanvas()

    def canvasPrint(self, name, withBinLabel=True):
        Plotter.canvas.Update()
        if withBinLabel:
            Plotter.canvas.Print("{0}_{1}.pdf".format(name, q2bins[self.process.cfg['binKey']]['label']))
        else:
            Plotter.canvas.Print("{0}.pdf".format(name))

    latex = ROOT.TLatex()
    latexCMSMark = staticmethod(lambda x=0.19, y=0.89: Plotter.latex.DrawLatexNDC(x, y, "#font[61]{CMS}"))
    latexCMSSim = staticmethod(lambda x=0.19, y=0.89: Plotter.latex.DrawLatexNDC(x, y, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}"))
    latexCMSToy = staticmethod(lambda x=0.19, y=0.89: Plotter.latex.DrawLatexNDC(x, y, "#font[61]{CMS} #font[52]{#scale[0.8]{Post-fit Toy}}"))
    latexCMSMix = staticmethod(lambda x=0.19, y=0.89: Plotter.latex.DrawLatexNDC(x, y, "#font[61]{CMS} #font[52]{#scale[0.8]{Toy + Simu.}}"))
    latexCMSExtra = staticmethod(lambda x=0.19, y=0.85: Plotter.latex.DrawLatexNDC(x, y, "#font[52]{#scale[0.8]{Preliminary}}") if True else None)
    latexLumi = staticmethod(lambda x=0.78, y=0.96: Plotter.latex.DrawLatexNDC(x, y, "#scale[0.8]{19.98 fb^{-1} (8 TeV)}"))
    @staticmethod
    def latexDataMarks(marks):
        if 'sim' in marks:
            Plotter.latexCMSSim()
            Plotter.latexCMSExtra()
        elif 'toy' in marks:
            Plotter.latexCMSToy()
            Plotter.latexCMSExtra()
        elif 'mix' in marks:
            Plotter.latexCMSMix()
            Plotter.latexCMSExtra()
        else:
            Plotter.latexCMSMark()
            Plotter.latexLumi()
            Plotter.latexCMSExtra()

    frameB = Bmass.frame()
    frameB.SetMinimum(0)
    frameB.SetTitle("")
    frameB_binning = 15

    frameK = CosThetaK.frame()
    frameK.SetMinimum(0)
    frameK.SetTitle("")
    frameK_binning = 10

    frameL = CosThetaL.frame()
    frameL.SetMinimum(0)
    frameL.SetTitle("")
    frameL_binning = 10

    legend = ROOT.TLegend(.75, .70, .95, .90)
    legend.SetFillColor(0)
    legend.SetBorderSize(0)

    def initPdfPlotCfg(self, p):
        """ [Name, plotOnOpt, argAliasInDB, LegendName] """
        pdfPlotTemplate = ["", plotterCfg_allStyle, None, None]
        p = p + pdfPlotTemplate[len(p):]
        if isinstance(p[0], str):
            self.logger.logDEBUG("Initialize pdfPlot {0}".format(p[0]))
            p[0] = self.process.sourcemanager.get(p[0])
            if p[0] == None:
                self.logger.logERROR("pdfPlot not found in source manager.")
                raise RuntimeError
        args = p[0].getParameters(ROOT.RooArgSet(Bmass, CosThetaK, CosThetaL, Mumumass, Kstarmass, Kshortmass))
        FitDBPlayer.initFromDB(self.process.dbplayer.odbfile, args, p[2])
        return p

    def initDataPlotCfg(self, p):
        """ [Name, plotOnOpt, LegendName] """
        dataPlotTemplate = ["", plotterCfg_dataStyle, "Data"]
        p = p + dataPlotTemplate[len(p):]
        if isinstance(p[0], str):
            self.logger.logDEBUG("Initialize dataPlot {0}".format(p[0]))
            p[0] = self.process.sourcemanager.get(p[0])
            if p[0] == None:
                self.logger.logERROR("dataPlot not found in source manager.")
                raise RuntimeError
        return p

    @staticmethod
    def plotFrame(frame, binning, dataPlots=None, pdfPlots=None, marks=None, scaleYaxis=1.8):
        """
            Use initXXXPlotCfg to ensure elements in xxxPlots fit the format
        """
        # Major plot
        cloned_frame = frame.emptyClone("cloned_frame")
        marks = [] if marks is None else marks
        dataPlots = [] if dataPlots is None else dataPlots
        pdfPlots = [] if pdfPlots is None else pdfPlots
        for pIdx, p in enumerate(dataPlots):
            p[0].plotOn(cloned_frame,
                        ROOT.RooFit.Name("dataP{0}".format(pIdx)),
                        ROOT.RooFit.Binning(binning),
                        *p[1])
        for pIdx, p in enumerate(pdfPlots):
            p[0].plotOn(cloned_frame,
                        ROOT.RooFit.Name("pdfP{0}".format(pIdx)),
                        *p[1])
        cloned_frame.SetMaximum(scaleYaxis * cloned_frame.GetMaximum())
        cloned_frame.Draw()

        # Legend
        Plotter.legend.Clear()
        for pIdx, p in enumerate(dataPlots):
            if p[2] is not None:
                Plotter.legend.AddEntry("dataP{0}".format(pIdx), p[2], "LPFE")
        for pIdx, p in enumerate(pdfPlots):
            if p[3] is not None:
                Plotter.legend.AddEntry("pdfP{0}".format(pIdx), p[3], "LF")
        Plotter.legend.Draw()

        # Some marks
        Plotter.latexDataMarks(marks)

    plotFrameB = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameB, 'binning': frameB_binning}))
    plotFrameK = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameK, 'binning': frameK_binning}))
    plotFrameL = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameL, 'binning': frameL_binning}))
    plotFrameB_fine = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameB, 'binning': frameB_binning * 2}))
    plotFrameK_fine = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameK, 'binning': frameK_binning * 2}))
    plotFrameL_fine = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameL, 'binning': frameL_binning * 2}))

    @classmethod
    def templateConfig(cls):
        cfg = Path.templateConfig()
        cfg.update({
            'db': "fitResults.db",
            'plotFuncs': [],  # (function, kwargs)
        })
        return cfg

    def _runPath(self):
        """"""
        for pltName, pCfg in self.cfg['plots'].items():
            if pltName not in self.cfg['switchPlots']:
                continue
            for func in pCfg['func']:
                func(self, **pCfg['kwargs'])


def plotSpectrumWithSimpleFit(self, pltName, dataPlots, marks):
    """ Assuming len(dataPlots) == 1, fit to the data. """
    for pIdx, plt in enumerate(dataPlots):
        dataPlots[pIdx] = self.initDataPlotCfg(plt)
    wspace = ROOT.RooWorkspace("wspace")
    getattr(wspace, 'import')(Bmass)
    wspace.factory("RooGaussian::gauss1(Bmass,mean[5.28,5.25,5.39],sigma1[0.02,0.01,0.05])")
    wspace.factory("RooGaussian::gauss2(Bmass,mean,sigma2[0.08,0.05,0.40])")
    wspace.factory("SUM::sigM(sigFrac[0.8,0,1]*gauss1,gauss2)")
    wspace.factory("c1[-5.6,-20,20]")
    wspace.factory("EXPR::bkgCombM('exp(c1*Bmass)',{Bmass,c1})")
    wspace.factory("SUM::model(tmp_nSig[1,1e5]*sigM,tmp_nBkg[20,1e5]*bkgCombM)")
    pdfPlots = [
        [wspace.pdf('model'), plotterCfg_allStyle, None, "Fit"],
        [wspace.pdf('model'), (ROOT.RooFit.Components('sigM'),) + plotterCfg_sigStyle, None, "Signal"],
        [wspace.pdf('model'), (ROOT.RooFit.Components('bkgCombM'),) + plotterCfg_bkgStyle, "Background"],
    ]

    pdfPlots[0][0].fitTo(dataPlots[0][0], ROOT.RooFit.Minos(True), ROOT.RooFit.Extended(True))
    Plotter.plotFrameB(dataPlots=dataPlots, pdfPlots=pdfPlots, marks=marks)
    self.canvasPrint(pltName)

def plotSimpleBLK(self, pltName, dataPlots, pdfPlots, marks, frames='BLK'):
    for pIdx, plt in enumerate(dataPlots):
        dataPlots[pIdx] = self.initDataPlotCfg(plt)
    for pIdx, plt in enumerate(pdfPlots):
        pdfPlots[pIdx] = self.initPdfPlotCfg(plt)

    args = pdfPlots[0][0].getParameters(ROOT.RooArgSet(Bmass, CosThetaK, CosThetaL))
    nSigDB = args.find('nSig').getVal()
    nSigErrorDB = args.find('nSig').getError()
    nBkgCombDB = args.find('nBkgComb').getVal()
    nBkgCombErrorDB = args.find('nBkgComb').getError()
    flDB = unboundFlToFl(args.find('unboundFl').getVal())
    afbDB = unboundAfbToAfb(args.find('unboundAfb').getVal(), flDB)

    plotFuncs = {
        'B': {'func': Plotter.plotFrameB_fine, 'tag': ""},
        'L': {'func': Plotter.plotFrameL, 'tag': "_cosl"},
        'K': {'func': Plotter.plotFrameK, 'tag': "_cosK"},
    }

    for frame in frames:
        plotFuncs[frame]['func'](dataPlots=dataPlots, pdfPlots=pdfPlots, marks=marks)
        if frame == 'B':
            Plotter.latex.DrawLatexNDC(.19, .77, "Y_{Signal}")
            Plotter.latex.DrawLatexNDC(.35, .77, "= {0:.2f}".format(nSigDB))
            Plotter.latex.DrawLatexNDC(.50, .77, "#pm {0:.2f}".format(nSigErrorDB))
            Plotter.latex.DrawLatexNDC(.19, .70, "Y_{Background}")
            Plotter.latex.DrawLatexNDC(.35, .70, "= {0:.2f}".format(nBkgCombDB))
            Plotter.latex.DrawLatexNDC(.50, .70, "#pm {0:.2f}".format(nBkgCombErrorDB))
        elif frame == 'L':
            Plotter.latex.DrawLatexNDC(.19, .77, "A_{{FB}} = {0:.2f}".format(afbDB))
        elif frame == 'K':
            Plotter.latex.DrawLatexNDC(.19, .77, "F_{{L}} = {0:.2f}".format(flDB))
        self.canvasPrint(pltName + plotFuncs[frame]['tag'])
types.MethodType(plotSimpleBLK, None, Plotter)

def plotEfficiency(self, data_name, pdf_name):
    pltName = "effi"
    data = self.process.sourcemanager.get(data_name)
    pdf = self.process.sourcemanager.get(pdf_name)
    if data == None or pdf == None:
        self.logger.logWARNING("Skip plotEfficiency. pdf or data not found")
        return
    args = pdf.getParameters(data)
    FitDBPlayer.initFromDB(self.process.dbplayer.odbfile, args)

    binningL = ROOT.RooBinning(len(dataCollection.accXEffThetaLBins) - 1, dataCollection.accXEffThetaLBins)
    binningK = ROOT.RooBinning(len(dataCollection.accXEffThetaKBins) - 1, dataCollection.accXEffThetaKBins)

    data_accXrec = self.process.sourcemanager.get("effiHistReader.h2_accXrec")
    h2_effi_sigA_fine = pdf.createHistogram("h2_effi_sigA_fine", CosThetaL, ROOT.RooFit.Binning(20), ROOT.RooFit.YVar(CosThetaK, ROOT.RooFit.Binning(20)))
    data_accXrec.SetMinimum(0)
    data_accXrec.SetMaximum(0.00015)
    data_accXrec.SetTitleOffset(1.6, "X")
    data_accXrec.SetTitleOffset(1.8, "Y")
    data_accXrec.SetTitleOffset(1.5, "Z")
    data_accXrec.SetZTitle("Overall efficiency")
    data_accXrec.Draw("LEGO2")
    h2_effi_sigA_fine.SetLineColor(2)
    h2_effi_sigA_fine.Draw("SURF SAME")
    Plotter.latexCMSSim(.08, .93)
    Plotter.latexCMSExtra(.08, .89)
    self.canvasPrint(pltName + "_2D")

    cloned_frameL = Plotter.frameL.emptyClone("cloned_frameL")
    h_accXrec_fine_ProjectionX = self.process.sourcemanager.get("effiHistReader.h_accXrec_fine_ProjectionX")
    data_accXrec_fine_ProjectionX = ROOT.RooDataHist("data_accXrec_fine_ProjectionX", "", ROOT.RooArgList(CosThetaL), ROOT.RooFit.Import(h_accXrec_fine_ProjectionX))
    data_accXrec_fine_ProjectionX.plotOn(cloned_frameL)
    pdfL = self.process.sourcemanager.get("effi_cosl")
    pdfL.plotOn(cloned_frameL, *plotterCfg_sigStyle)
    cloned_frameL.SetMaximum(1.5 * cloned_frameL.GetMaximum())
    cloned_frameL.Draw()
    Plotter.latexCMSSim()
    Plotter.latexCMSExtra()
    Plotter.latex.DrawLatexNDC(.85, .89, "#chi^{{2}}={0:.2f}".format(cloned_frameL.chiSquare()))
    self.canvasPrint(pltName + "_cosl")

    cloned_frameK = Plotter.frameK.emptyClone("cloned_frameK")
    h_accXrec_fine_ProjectionY = self.process.sourcemanager.get("effiHistReader.h_accXrec_fine_ProjectionY")
    data_accXrec_fine_ProjectionY = ROOT.RooDataHist("data_accXrec_fine_ProjectionY", "", ROOT.RooArgList(CosThetaK), ROOT.RooFit.Import(h_accXrec_fine_ProjectionY))
    data_accXrec_fine_ProjectionY.plotOn(cloned_frameK)
    pdfK = self.process.sourcemanager.get("effi_cosK")
    pdfK.plotOn(cloned_frameK, *plotterCfg_sigStyle)
    cloned_frameK.SetMaximum(1.5 * cloned_frameK.GetMaximum())
    cloned_frameK.Draw()
    Plotter.latexCMSSim()
    Plotter.latexCMSExtra()
    Plotter.latex.DrawLatexNDC(.85, .89, "#chi^{{2}}={0:.2f}".format(cloned_frameK.chiSquare()))
    self.canvasPrint(pltName + "_cosK")
types.MethodType(plotEfficiency, None, Plotter)

def plotPostfitBLK(self, pltName, dataReader, pdfPlots):
    """Specification of plotSimpleBLK for post-fit plots"""
    for pIdx, plt in enumerate(pdfPlots):
        pdfPlots[pIdx] = self.initPdfPlotCfg(plt)

    # Calculate normalization and then draw
    args = pdfPlots[0][0].getParameters(ROOT.RooArgSet(Bmass, CosThetaK, CosThetaL))
    nSigDB = args.find('nSig').getVal()
    nSigErrorDB = args.find('nSig').getError()
    nBkgCombDB = args.find('nBkgComb').getVal()
    nBkgCombErrorDB = args.find('nBkgComb').getError()
    flDB = unboundFlToFl(args.find('unboundFl').getVal())
    afbDB = unboundAfbToAfb(args.find('unboundAfb').getVal(), flDB)
    sigFrac = {}
    bkgCombFrac = {}
    for regionName in ["Fit", "SR", "LSB", "USB"]:
        dataPlots = [["{0}.{1}".format(dataReader, regionName), plotterCfg_dataStyle, "Data"], ]
        for pIdx, p in enumerate(dataPlots):
            dataPlots[pIdx] = self.initDataPlotCfg(p)

        # Bind the 'Bmass' defined in PDF with 'getObservables' to createIntegral
        obs = pdfPlots[1][0].getObservables(dataPlots[0][0])
        FitterCore.ArgLooper(obs, lambda p: p.setRange(regionName, *bMassRegions[regionName]['range']), ["Bmass"])
        sigFrac[regionName] = pdfPlots[1][0].createIntegral(
            obs,
            ROOT.RooFit.NormSet(obs),
            ROOT.RooFit.Range(regionName)).getVal()

        obs = pdfPlots[2][0].getObservables(dataPlots[0][0])
        FitterCore.ArgLooper(obs, lambda p: p.setRange(regionName, *bMassRegions[regionName]['range']), ["Bmass"])
        bkgCombFrac[regionName] = pdfPlots[2][0].createIntegral(
            obs,
            ROOT.RooFit.NormSet(obs),
            ROOT.RooFit.Range(regionName)).getVal()
        nTotal_local = nSigDB * sigFrac[regionName] + nBkgCombDB * bkgCombFrac[regionName]

        # Correct the shape of f_final
        args.find("nSig").setVal(nSigDB * sigFrac[regionName])
        args.find("nBkgComb").setVal(nBkgCombDB * bkgCombFrac[regionName])

        modified_pdfPlots = [
            [pdfPlots[0][0],
             pdfPlots[0][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent),),
             None,
             "Fit"],
            [pdfPlots[0][0],
             pdfPlots[1][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent), ROOT.RooFit.Components(pdfPlots[1][0].GetName())),
             None,
             "Sig"],
            [pdfPlots[0][0],
             pdfPlots[2][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent), ROOT.RooFit.Components(pdfPlots[2][0].GetName())),
             None,
             "Bkg"],
        ]

        plotFuncs = {
            'B': {'func': Plotter.plotFrameB, 'tag': ""},
            'L': {'func': Plotter.plotFrameL, 'tag': "_cosl"},
            'K': {'func': Plotter.plotFrameK, 'tag': "_cosK"},
        }

        for frame in 'BLK':
            plotFuncs[frame]['func'](dataPlots=dataPlots, pdfPlots=modified_pdfPlots)
            if frame == 'B':
                Plotter.latex.DrawLatexNDC(.19, .77, "Y_{Signal}")
                Plotter.latex.DrawLatexNDC(.35, .77, "= {0:.2f}".format(nSigDB * sigFrac[regionName]))
                Plotter.latex.DrawLatexNDC(.50, .77, "#pm {0:.2f}".format(nSigErrorDB * sigFrac[regionName]))
                Plotter.latex.DrawLatexNDC(.19, .70, "Y_{Background}")
                Plotter.latex.DrawLatexNDC(.35, .70, "= {0:.2f}".format(nBkgCombDB * bkgCombFrac[regionName]))
                Plotter.latex.DrawLatexNDC(.50, .70, "#pm {0:.2f}".format(nBkgCombErrorDB * bkgCombFrac[regionName]))
            elif frame == 'L':
                Plotter.latex.DrawLatexNDC(.19, .77, "A_{{FB}} = {0:.2f}".format(afbDB))
            elif frame == 'K':
                Plotter.latex.DrawLatexNDC(.19, .77, "F_{{L}} = {0:.2f}".format(flDB))
            self.canvasPrint(pltName + '_' + regionName + plotFuncs[frame]['tag'])
types.MethodType(plotPostfitBLK, None, Plotter)

def plotSummaryAfbFl(self, pltName, dbSetup, drawSM=False, marks=None):
    """ 'dbSetup': [["name", "/path/fitResults_{binLabel}.db", statErrorKey, withSystError, drawOpt, argAliasInDB, fillColor, fillStyle],] """
    if marks is None:
        marks = []
    binKeys = ['belowJpsi', 'betweenPeaks', 'abovePsi2s']

    xx = array('d', [sum(q2bins[binKey]['q2range']) / 2 for binKey in binKeys])
    xxErr = array('d', map(lambda t: (t[1] - t[0]) / 2, [q2bins[binKey]['q2range'] for binKey in binKeys]))

    grFls = []
    grAfbs = []

    def quadSum(lst):
        return math.sqrt(sum(map(lambda i: i**2, lst)))

    def calcSystError(db):
        """ FlErrHi, FlErrLo, AfbErrHi, AfbErrLo"""
        flSystErrorHi = []
        flSystErrorLo = []
        afbSystErrorHi = []
        afbSystErrorLo = []
        systErrorSourceBlackList = []
        for key, val in db.items():
            if re.match("^syst_.*_afb$", key) and not any([re.match(pat, key) for pat in systErrorSourceBlackList]):
                afbSystErrorHi.append(db[key]['getErrorHi'])
                afbSystErrorLo.append(db[key]['getErrorLo'])
            if re.match("^syst_.*_fl$", key) and not any([re.match(pat, key) for pat in systErrorSourceBlackList]):
                flSystErrorHi.append(db[key]['getErrorHi'])
                flSystErrorLo.append(db[key]['getErrorLo'])
        return quadSum(flSystErrorHi), quadSum(flSystErrorLo), quadSum(afbSystErrorHi), quadSum(afbSystErrorLo)

    def getStatError_FeldmanCousins(db):
        """ FlErrHi, FlErrLo, AfbErrHi, AfbErrLo"""
        return db['stat_FC_fl']['getErrorHi'], -db['stat_FC_fl']['getErrorLo'], db['stat_FC_afb']['getErrorHi'], -db['stat_FC_afb']['getErrorLo']

    def getStatError_Minuit(db):
        """ FlErrHi, FlErrLo, AfbErrHi, AfbErrLo"""
        unboundFl = db[argAliasInDB.get("unboundFl", "unboundFl")]
        unboundAfb = db[argAliasInDB.get("unboundAfb", "unboundAfb")]

        fl = unboundFlToFl(unboundFl['getVal'])
        afb = unboundAfbToAfb(unboundAfb['getVal'], fl)

        yyFlErrHi = unboundFlToFl(unboundFl['getVal'] + unboundFl['getErrorHi']) - fl
        yyFlErrLo = fl - unboundFlToFl(unboundFl['getVal'] + unboundFl['getErrorLo'])
        yyAfbErrHi = unboundAfbToAfb(unboundAfb['getVal'] + unboundAfb['getErrorHi'], fl) - afb
        yyAfbErrLo = afb - unboundAfbToAfb(unboundAfb['getVal'] + unboundAfb['getErrorLo'], fl)
        return yyFlErrHi, yyFlErrLo, yyAfbErrHi, yyAfbErrLo

    statErrorMethods = {
        'FeldmanCousins': getStatError_FeldmanCousins,
        'Minuit': getStatError_Minuit,
    }
    for name, dbPat, statErrorKey, withSystError, drawOpt, argAliasInDB, fillColor, fillStyle in dbSetup:

        yyFl = array('d', [0] * len(binKeys))
        yyFlStatErrHi = array('d', [0] * len(binKeys))
        yyFlStatErrLo = array('d', [0] * len(binKeys))
        yyFlSystErrHi = array('d', [0] * len(binKeys))
        yyFlSystErrLo = array('d', [0] * len(binKeys))
        yyFlErrHi = array('d', [0] * len(binKeys))
        yyFlErrLo = array('d', [0] * len(binKeys))

        yyAfb = array('d', [0] * len(binKeys))
        yyAfbStatErrHi = array('d', [0] * len(binKeys))
        yyAfbStatErrLo = array('d', [0] * len(binKeys))
        yyAfbSystErrHi = array('d', [0] * len(binKeys))
        yyAfbSystErrLo = array('d', [0] * len(binKeys))
        yyAfbErrHi = array('d', [0] * len(binKeys))
        yyAfbErrLo = array('d', [0] * len(binKeys))
        for binKeyIdx, binKey in enumerate(binKeys):
            if not os.path.exists(dbPat.format(binLabel=q2bins[binKey]['label'])):
                self.logger.logERROR("Input db file {0} NOT found. Skip.".format(dbPat.format(binLable=q2bins[binKey]['label'])))
                continue
            try:
                db = shelve.open(dbPat.format(binLabel=q2bins[binKey]['label']))
                unboundFl = db[argAliasInDB.get("unboundFl", "unboundFl")]
                unboundAfb = db[argAliasInDB.get("unboundAfb", "unboundAfb")]

                fl = unboundFlToFl(unboundFl['getVal'])
                afb = unboundAfbToAfb(unboundAfb['getVal'], fl)

                yyFl[binKeyIdx] = fl
                yyAfb[binKeyIdx] = afb
                yyFlStatErrHi[binKeyIdx], yyFlStatErrLo[binKeyIdx],\
                    yyAfbStatErrHi[binKeyIdx], yyAfbStatErrLo[binKeyIdx] = statErrorMethods.get(statErrorKey, getStatError_Minuit)(db)
                if withSystError:
                    yyFlSystErrHi[binKeyIdx], yyFlSystErrLo[binKeyIdx],\
                        yyAfbSystErrHi[binKeyIdx], yyAfbSystErrLo[binKeyIdx] = calcSystError(db)
                else:
                    yyFlSystErrHi[binKeyIdx], yyFlSystErrLo[binKeyIdx],\
                        yyAfbSystErrHi[binKeyIdx], yyAfbSystErrLo[binKeyIdx] = 0, 0, 0, 0
                yyFlErrHi[binKeyIdx] = min(quadSum([yyFlStatErrHi[binKeyIdx], yyFlSystErrHi[binKeyIdx]]), 1. - yyFl[binKeyIdx])
                yyFlErrLo[binKeyIdx] = min(quadSum([yyFlStatErrLo[binKeyIdx], yyFlSystErrLo[binKeyIdx]]), yyFl[binKeyIdx])
                yyAfbErrHi[binKeyIdx] = min(quadSum([yyAfbStatErrHi[binKeyIdx], yyAfbSystErrHi[binKeyIdx]]), 0.75 - yyAfb[binKeyIdx])
                yyAfbErrLo[binKeyIdx] = min(quadSum([yyAfbStatErrLo[binKeyIdx], yyAfbSystErrLo[binKeyIdx]]), 0.75 + yyAfb[binKeyIdx])
            finally:
                db.close()

        grAfb = ROOT.TGraphAsymmErrors(len(binKeys), xx, yyAfb, xxErr, xxErr, yyAfbErrLo, yyAfbErrHi)
        grAfb.SetMarkerColor(fillColor if fillColor else 2)
        grAfb.SetLineColor(fillColor if fillColor else 2)
        grAfb.SetFillColor(fillColor if fillColor else 2)
        grAfb.SetFillStyle(fillStyle if fillStyle else 3001)
        grAfbs.append(grAfb)

        grFl = ROOT.TGraphAsymmErrors(len(binKeys), xx, yyFl, xxErr, xxErr, yyFlErrLo, yyFlErrHi)
        grFl.SetMarkerColor(fillColor if fillColor else 2)
        grFl.SetLineColor(fillColor if fillColor else 2)
        grFl.SetFillColor(fillColor if fillColor else 2)
        grFl.SetFillStyle(fillStyle if fillStyle else 3001)
        grFls.append(grFl)

    # TODO
    if drawSM:
        pass

    for grIdx, gr in enumerate(grAfbs):
        gr.SetTitle("")
        gr.GetXaxis().SetTitle("q^{2} [(GeV/c^{2})^{2}]")
        gr.GetYaxis().SetTitle("A_{FB}")
        gr.GetYaxis().SetRangeUser(-0.75, 1.5)
        gr.SetLineWidth(2)
        drawOpt = dbSetup[grIdx][4] if isinstance(dbSetup[grIdx][4], list) else [dbSetup[grIdx][4]]
        for opt in drawOpt:
            gr.Draw(opt if grIdx == 0 else opt + " SAME")
    Plotter.latexDataMarks(marks)
    self.canvasPrint(pltName + '_afb', False)

    for grIdx, gr in enumerate(grFls):
        gr.SetTitle("")
        gr.GetXaxis().SetTitle("q^{2} [(GeV/c^{2})^{2}]")
        gr.GetYaxis().SetTitle("F_{L}")
        gr.GetYaxis().SetRangeUser(0, 1.5)
        gr.SetLineWidth(2)
        drawOpt = dbSetup[grIdx][4] if isinstance(dbSetup[grIdx][4], list) else [dbSetup[grIdx][4]]
        for opt in drawOpt:
            gr.Draw(opt if grIdx == 0 else opt + " SAME")
    Plotter.latexDataMarks(marks)
    self.canvasPrint(pltName + '_fl', False)

types.MethodType(plotSpectrumWithSimpleFit, None, Plotter)


plotterCfg = {
    'name': "plotter",
    'switchPlots': [],
}
plotterCfg_dataStyle = ()
plotterCfg_mcStyle = ()
plotterCfg_allStyle = (ROOT.RooFit.LineColor(1),)
plotterCfg_sigStyle = (ROOT.RooFit.LineColor(4),)
plotterCfg_bkgStyle = (ROOT.RooFit.LineColor(2), ROOT.RooFit.LineStyle(9))
plotterCfg['plots'] = {
    'simpleSpectrum': {
        'func': [plotSpectrumWithSimpleFit],
        'kwargs': {
            'pltName': "h_Bmass",
            'dataPlots': [["dataReader.Fit", plotterCfg_dataStyle], ],
            'marks': []}
    },
    'effi': {
        'func': [plotEfficiency],
        'kwargs': {
            'data_name': "effiHistReader.accXrec",
            'pdf_name': "effi_sigA"}
    },
    'angular3D_sigM': {
        'func': [functools.partial(plotSimpleBLK, frames='B')],
        'kwargs': {
            'pltName': "angular3D_sigM",
            'dataPlots': [["sigMCReader.Fit", plotterCfg_mcStyle, "Simulation"], ],
            'pdfPlots': [["f_sigM", plotterCfg_sigStyle, fitCollection.setupSigMFitter['argAliasInDB'], "Fit"],
                        ],
            'marks': ['sim']}
    },
    'angular3D_sig2D': {
        'func': [functools.partial(plotSimpleBLK, frames='LK')],
        'kwargs': {
            'pltName': "angular3D_sig2D",
            'dataPlots': [["sigMCReader.Fit", plotterCfg_mcStyle, "Simulation"], ],
            'pdfPlots': [["f_sig2D", plotterCfg_sigStyle, fitCollection.setupSig2DFitter['argAliasInDB'], None],
                        ],
            'marks': []}
    },
    'angular3D_bkgCombA': {
        'func': [functools.partial(plotSimpleBLK, frames='LK')],
        'kwargs': {
            'pltName': "angular3D_bkgCombA",
            'dataPlots': [["dataReader.SB", plotterCfg_dataStyle, "Data"], ],
            'pdfPlots': [["f_bkgCombA", plotterCfg_bkgStyle, None, "Analytic"],
                         #  ["f_bkgCombAltA", (ROOT.RooFit.LineColor(4), ROOT.RooFit.LineStyle(9)), None, "Smooth"],
                        ],
            'marks': []}
    },
    'simpleBLK': {  # Most general case, to be customized by user
        'func': [functools.partial(plotSimpleBLK, frames='BLK')],
        'kwargs': {
            'pltName': "simpleBLK",
            'dataPlots': [["ToyGenerator.mixedToy", plotterCfg_mcStyle, "Toy"], ],
            'pdfPlots': [["f_sigM", plotterCfg_sigStyle, None, None],
                        ],
            'marks': ['sim']}
    },
    'angular3D_final': {
        'func': [plotPostfitBLK],
        'kwargs': {
            'pltName': "angular3D_final",
            'dataReader': "dataReader",
            'pdfPlots': [["f_final", plotterCfg_allStyle, None, "Fit"],
                         ["f_sig3D", plotterCfg_sigStyle, None, "Sig"],
                         ["f_bkgComb", plotterCfg_bkgStyle, None, "Bkg"],
                        ],
        }
    },
    'angular3D_summary': {
        'func': [plotSummaryAfbFl],
        'kwargs': {
            'pltName': "angular3D_summary",
            'dbSetup': [["Data", p.dbplayer.absInputDir + "/fitResults_{binLabel}.db", 'FeldmanCousins', False, ["A2", "P0"], {}, 2, 3001],
                        ["Data", p.dbplayer.absInputDir + "/fitResults_{binLabel}.db", 'FeldmanCousins', True, "P0", {}, 2, 3001],
                       ],
        },
    },
    'angular3D_summary_RECO2GEN': {
        'func': [plotSummaryAfbFl],
        'kwargs': {
            'pltName': "angular3D_summary_RECO2GEN",
            'dbSetup': [["RECO", p.dbplayer.absInputDir + "/fitResults_{binLabel}.db",
                         'Minuit', False, ["A2", "P0"],
                         {'unboundFl': 'unboundFl_RECO', 'unboundAfb': 'unboundAfb_RECO'},
                         2, 3001],
                        ["GEN", p.dbplayer.absInputDir + "/fitResults_{binLabel}.db",
                         'Minuit', False, "2P0",
                         {'unboundFl': 'unboundFl_GEN', 'unboundAfb': 'unboundAfb_GEN'},
                         4, 3001],
                       ],
            'marks': ['sim']
        },
    },
}
#  plotterCfg['switchPlots'].append('simpleSpectrum')
#  plotterCfg['switchPlots'].append('effi')
#  plotterCfg['switchPlots'].append('angular3D_sigM')
#  plotterCfg['switchPlots'].append('angular3D_bkgCombA')
#  plotterCfg['switchPlots'].append('angular3D_final')
#  plotterCfg['switchPlots'].append('angular3D_summary')
#  plotterCfg['switchPlots'].append('angular3D_summary_RECO2GEN')

plotter = Plotter(plotterCfg)

if __name__ == '__main__':
    #  p.cfg['binKey'] = "abovePsi2s"
    #  plotter.cfg['switchPlots'].append('simpleSpectrum')
    #  plotter.cfg['switchPlots'].append('effi')
    #  plotter.cfg['switchPlots'].append('angular3D_sigM')
    #  plotter.cfg['switchPlots'].append('angular3D_bkgCombA')
    #  plotter.cfg['switchPlots'].append('angular3D_final')
    #  plotter.cfg['switchPlots'].append('angular3D_summary')
    plotterCfg['switchPlots'].append('angular3D_summary')
    plotterCfg['switchPlots'].append('angular3D_summary_RECO2GEN')
    p.setSequence([dataCollection.effiHistReader, dataCollection.sigMCReader, dataCollection.dataReader, pdfCollection.stdWspaceReader, plotter])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
