#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 sts=4 fdm=indent fdl=0 fdn=3 ft=python et:

import types
import functools
import shelve
import copy

import ROOT

import SingleBuToKstarMuMuFitter.cpp
from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Path import Path
from v2Fitter.FlowControl.Logger import VerbosityLevels
from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.anaSetup import q2bins, processCfg, modulePath, bMassRegions

from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer, register_dbfile
from SingleBuToKstarMuMuFitter.varCollection import Bmass, CosThetaK, CosThetaL, Mumumass, Kstarmass
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection

def setStyle():
    ROOT.gROOT.SetBatch(1)

    ROOT.gStyle.SetCanvasBorderMode(0)
    ROOT.gStyle.SetCanvasColor(ROOT.kWhite)
    ROOT.gStyle.SetCanvasDefH(500)   # Height of canvas
    ROOT.gStyle.SetCanvasDefW(700)   # Width of canvas
    ROOT.gStyle.SetCanvasDefX(0)     # Position on screen
    ROOT.gStyle.SetCanvasDefY(0)     # default:0

    #  For the Pad:
    ROOT.gStyle.SetPadBorderMode(0)
    ROOT.gStyle.SetPadColor(ROOT.kWhite)
    ROOT.gStyle.SetPadGridX(False)
    ROOT.gStyle.SetPadGridY(False)
    ROOT.gStyle.SetGridColor(0)
    ROOT.gStyle.SetGridStyle(3)
    ROOT.gStyle.SetGridWidth(1)

    #  For the frame:
    ROOT.gStyle.SetFrameBorderMode(0)
    ROOT.gStyle.SetFrameBorderSize(1)
    ROOT.gStyle.SetFrameFillColor(0)
    ROOT.gStyle.SetFrameFillStyle(0)
    ROOT.gStyle.SetFrameLineColor(1)
    ROOT.gStyle.SetFrameLineStyle(1)
    ROOT.gStyle.SetFrameLineWidth(1)

    #  For the histo:
    #  ROOT.gStyle.SetHistFillColor(63)# pchen modified
    #  ROOT.gStyle.SetHistFillStyle(0)
    ROOT.gStyle.SetHistLineColor(1)
    ROOT.gStyle.SetHistLineStyle(0)
    ROOT.gStyle.SetHistLineWidth(1)
    #  ROOT.gStyle.SetLegoInnerR(Float_t rad = 0.5)
    #  ROOT.gStyle.SetNumberContours(Int_t number = 20)

    #  ROOT.gStyle.SetEndErrorSize(0)
    ROOT.gStyle.SetErrorX(0.)
    #  ROOT.gStyle.SetErrorMarker(20)

    ROOT.gStyle.SetMarkerStyle(20)

    #  For the fit/function:
    #      v = 1  print name/values of parameters
    #      e = 1  print errors (if e=1, v must be 1)
    #      c = 1  print Chisquare/Number of degress of freedom
    #      p = 1  print Probability
    ROOT.gStyle.SetOptFit(1)
    ROOT.gStyle.SetFitFormat("5.4g")
    ROOT.gStyle.SetFuncColor(2)
    ROOT.gStyle.SetFuncStyle(1)
    ROOT.gStyle.SetFuncWidth(1)

    #  the date:
    ROOT.gStyle.SetOptDate(0)
    #  ROOT.gStyle.SetDateX(Float_t x = 0.01)
    #  ROOT.gStyle.SetDateY(Float_t y = 0.01)


    #  For the statistics box:

    # See TStyle
    #      n = 1  name of histogram is printed
    #      e = 1  number of entries printed
    #      m = 1  mean value printed
    #      r = 1  rms printed
    #      u = 1  number of underflows printed
    #      o = 1  number of overflows printed
    ROOT.gStyle.SetOptFile(0)
    ROOT.gStyle.SetOptStat(0)  # To display the mean and RMS:   SetOptStat("mr");
    ROOT.gStyle.SetStatColor(ROOT.kWhite)
    ROOT.gStyle.SetStatFont(42)
    ROOT.gStyle.SetStatFontSize(0.025)
    ROOT.gStyle.SetStatTextColor(1)
    ROOT.gStyle.SetStatFormat("6.4g")
    ROOT.gStyle.SetStatBorderSize(1)
    ROOT.gStyle.SetStatH(0.1)
    ROOT.gStyle.SetStatW(0.15)
    #   ROOT.gStyle.SetStatStyle(Style_t style = 1001)
    #   ROOT.gStyle.SetStatX(Float_t x = 0)
    #   ROOT.gStyle.SetStatY(Float_t y = 0)

    #  Margins:
    ROOT.gStyle.SetPadTopMargin(0.05)
    ROOT.gStyle.SetPadBottomMargin(0.05)
    ROOT.gStyle.SetPadLeftMargin(0.13)
    ROOT.gStyle.SetPadRightMargin(0.05)

    #  For the Global title:
    ROOT.gStyle.SetOptTitle(0)  # 0:turn off the title
    ROOT.gStyle.SetTitleFont(42)
    ROOT.gStyle.SetTitleColor(1)
    ROOT.gStyle.SetTitleTextColor(1)
    ROOT.gStyle.SetTitleFillColor(10)
    ROOT.gStyle.SetTitleFontSize(0.05)
    #  ROOT.gStyle.SetTitleH(0) #  Set the height of the title box
    #  ROOT.gStyle.SetTitleW(0) #  Set the width of the title box
    #  ROOT.gStyle.SetTitleX(0) #  Set the position of the title box
    #  ROOT.gStyle.SetTitleY(0.985) #  Set the position of the title box
    #  ROOT.gStyle.SetTitleStyle(Style_t style = 1001)
    #  ROOT.gStyle.SetTitleBorderSize(2)

    #  For the axis titles:
    ROOT.gStyle.SetTitleColor(1, "XYZ")
    ROOT.gStyle.SetTitleFont(42, "XYZ")
    ROOT.gStyle.SetTitleSize(0.06, "XYZ")
    #  ROOT.gStyle.SetTitleXSize(Float_t size = 0.02) #  Another way to set the size?
    #  ROOT.gStyle.SetTitleYSize(Float_t size = 0.02)
    ROOT.gStyle.SetTitleXOffset(1.8)
    ROOT.gStyle.SetTitleYOffset(1.8)
    #  ROOT.gStyle.SetTitleOffset(1.1, "Y") #  Another way to set the Offset

    #  For the axis labels:
    ROOT.gStyle.SetLabelColor(1, "XYZ")
    ROOT.gStyle.SetLabelFont(42, "XYZ")
    ROOT.gStyle.SetLabelOffset(0.007, "XYZ")
    ROOT.gStyle.SetLabelSize(0.05, "XYZ")

    #  For the axis:
    ROOT.gStyle.SetAxisColor(1, "XYZ")
    ROOT.gStyle.SetStripDecimals(True)
    ROOT.gStyle.SetTickLength(0.03, "XYZ")
    ROOT.gStyle.SetNdivisions(510, "XYZ")
    ROOT.gStyle.SetPadTickX(1)  # To get tick marks on the opposite side of the frame
    ROOT.gStyle.SetPadTickY(1)

    #  Change for log plots:
    ROOT.gStyle.SetOptLogx(0)
    ROOT.gStyle.SetOptLogy(0)
    ROOT.gStyle.SetOptLogz(0)

    # My preferences:
    ROOT.gStyle.SetPadTopMargin(0.10)        # default:0.05, avoid to overlap with 10^n. No Title in paper.
    ROOT.gStyle.SetPadBottomMargin(0.12)     # default:0.13, avoid to overlap with label
    ROOT.gStyle.SetPadLeftMargin(0.12)       # default:0.05, avoid to overlap with label
    ROOT.gStyle.SetPadRightMargin(0.05)      # default:0.05
    ROOT.gStyle.SetPalette(57)               # default(0), rainbow palette is much prettier.
    ROOT.gStyle.SetPaintTextFormat("5.2f")   # precision if plotted with "TEXT"

    ROOT.gStyle.SetOptTitle(0)               # turn off the title
    ROOT.gStyle.SetTitleSize(0.05)           # title of hist
    ROOT.gStyle.SetTitleFontSize(0.05)

    ROOT.gStyle.SetTitleSize(0.05, "XYZ")    # title of axis
    ROOT.gStyle.SetTitleOffset(1.0, "X")
    ROOT.gStyle.SetTitleOffset(1.2, "YZ")
    ROOT.gStyle.SetLabelOffset(0.01, "XYZ")  # label of axis
    ROOT.gStyle.SetLabelFont(62, "XYZ")
    ROOT.gStyle.SetLabelSize(0.04, "X")
    ROOT.gStyle.SetLabelSize(0.04, "YZ")
    ROOT.gStyle.SetNdivisions(505, "X")

    ROOT.gStyle.SetHistFillColor(0)
    ROOT.gStyle.SetHistLineWidth(2)
    ROOT.gStyle.SetMarkerStyle(21)           # x(5),.(1),triangle(22),square(21)
    ROOT.gStyle.SetMarkerSize(0.6)

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetStatFontSize(0.04)

    ROOT.gStyle.SetOptFit(0)                 # default:1
    ROOT.gStyle.SetTextSize(0.05)            # default:1, won't affect TLegend until ver5.34
    ROOT.gStyle.SetFuncWidth(2)

    ROOT.gStyle.SetLegendBorderSize(0)       # default:4
    ROOT.gStyle.SetLegendFillColor(ROOT.kWhite)

    ROOT.gStyle.cd()
    pass

class Plotter(Path):
    """The plotter"""
    setStyle()
    canvas = ROOT.TCanvas()

    def canvasPrint(self, name):
        Plotter.canvas.Update()
        Plotter.canvas.Print("{0}_{1}.pdf".format(name, q2bins[self.process.cfg['binKey']]['label']))

    latex = ROOT.TLatex()
    latexCMSMark = staticmethod(lambda x=0.01, y=0.95: Plotter.latex.DrawLatexNDC(x, y, "CMS #font[22]{Preliminary}"))
    latexCMSSim = staticmethod(lambda x=0.01, y=0.95: Plotter.latex.DrawLatexNDC(x, y, "CMS #font[22]{Simulation}"))
    latexLumi = staticmethod(lambda x=0.78, y=0.95: Plotter.latex.DrawLatexNDC(x, y, "#font[32]{L_{int}} = 19.98 fb^{-1}"))

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

    @staticmethod
    def plotFrame(frame, binning, dataPlots=None, pdfPlots=None, marks=None):
        """
            xxxPlots = [[obj, (options for plotOn)], ]
        """
        cloned_frame = frame.emptyClone("cloned_frame")
        marks = [] if marks is None else marks
        dataPlots = [] if dataPlots is None else dataPlots
        pdfPlots = [] if pdfPlots is None else pdfPlots
        for p, pOption in dataPlots:
            p.plotOn(cloned_frame, ROOT.RooFit.Binning(binning), *pOption)
        for p, pOption in pdfPlots:
            p.plotOn(cloned_frame, *pOption)
        cloned_frame.Draw()
        if 'sim' not in marks:
            Plotter.latexCMSMark()
            Plotter.latexLumi()
        else:
            Plotter.latexCMSSim()

    plotFrameB = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameB, 'binning': frameB_binning}))
    plotFrameK = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameK, 'binning': frameK_binning}))
    plotFrameL = staticmethod(functools.partial(plotFrame.__func__, **{'frame': frameL, 'binning': frameL_binning}))

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


def plotSimpleBLK(self, pltName, dataPlots, pdfPlots, marks, frames='BLK'):
    for p in dataPlots:
        if isinstance(p[0], str):
            p[0] = self.process.sourcemanager.get(p[0])
    for p in pdfPlots:
        if isinstance(p[0], str):
            p[0] = self.process.sourcemanager.get(p[0])
            args = p[0].getParameters(ROOT.RooArgSet(Bmass, CosThetaK, CosThetaL, Mumumass))
            FitDBPlayer.initFromDB(self.process.odbfilename, args)

    plotFuncs = {
        'B': {'func': Plotter.plotFrameB, 'tag': ""},
        'L': {'func': Plotter.plotFrameL, 'tag': "_cosl"},
        'K': {'func': Plotter.plotFrameK, 'tag': "_cosK"},
    }

    for frame in frames:
        plotFuncs[frame]['func'](dataPlots=dataPlots, pdfPlots=pdfPlots, marks=marks)
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
    FitDBPlayer.initFromDB(self.process.odbfilename, args)

    binningL = ROOT.RooBinning(len(dataCollection.accXEffThetaLBins) - 1, dataCollection.accXEffThetaLBins)
    binningK = ROOT.RooBinning(len(dataCollection.accXEffThetaKBins) - 1, dataCollection.accXEffThetaKBins)

    data_accXrec = self.process.sourcemanager.get("effiHistReader.h2_accXrec")
    h2_effi_sigA_fine = pdf.createHistogram("h2_effi_sigA_fine", CosThetaL, ROOT.RooFit.Binning(20), ROOT.RooFit.YVar(CosThetaK, ROOT.RooFit.Binning(20)))
    data_accXrec.SetMinimum(0)
    data_accXrec.SetMaximum(0.00015)
    data_accXrec.SetZTitle("Overall efficiency")
    data_accXrec.Draw("LEGO2")
    h2_effi_sigA_fine.SetLineColor(2)
    h2_effi_sigA_fine.Draw("SURF SAME")
    Plotter.latexCMSSim()
    self.canvasPrint(pltName + "_2D")

    cloned_frameL = Plotter.emptyClone("cloned_frameL")
    h_accXrec_fine_ProjectionX = self.process.sourcemanager.get("effiHistReader.h_accXrec_fine_ProjectionX")
    data_accXrec_fine_ProjectionX = ROOT.RooDataHist("data_accXrec_fine_ProjectionX", "", ROOT.RooArgList(CosThetaL), ROOT.RooFit.Import(h_accXrec_fine_ProjectionX))
    data_accXrec_fine_ProjectionX.plotOn(cloned_frameL)
    pdfL = self.process.sourcemanager.get("effi_cosl")
    pdfL.plotOn(cloned_frameL, ROOT.RooFit.LineColor(2))
    cloned_frameL.Draw()
    Plotter.latexCMSSim()
    Plotter.latex.DrawLatexNDC(.80, .85, "#chi^{{2}}={0:.2f}".format(Plotter.frameL.chiSquare()))
    self.canvasPrint(pltName + "_cosl")

    cloned_frameK = Plotter.emptyClone("cloned_frameK")
    h_accXrec_fine_ProjectionY = self.process.sourcemanager.get("effiHistReader.h_accXrec_fine_ProjectionY")
    data_accXrec_fine_ProjectionY = ROOT.RooDataHist("data_accXrec_fine_ProjectionY", "", ROOT.RooArgList(CosThetaK), ROOT.RooFit.Import(h_accXrec_fine_ProjectionY))
    data_accXrec_fine_ProjectionY.plotOn(cloned_frameK)
    pdfK = self.process.sourcemanager.get("effi_cosK")
    pdfK.plotOn(cloned_frameK, ROOT.RooFit.LineColor(2))
    cloned_frameK.Draw()
    Plotter.latexCMSSim()
    Plotter.latex.DrawLatexNDC(.80, .85, "#chi^{{2}}={0:.2f}".format(cloned_frameK.chiSquare()))
    self.canvasPrint(pltName + "_cosK")
types.MethodType(plotEfficiency, None, Plotter)


def plotPostfitBLK(self, pltName, dataReader, pdfPlots):
    """Specification of plotSimpleBLK for post-fit plots"""
    for p in pdfPlots:
        if isinstance(p[0], str):
            p[0] = self.process.sourcemanager.get(p[0])
            args = p[0].getParameters(ROOT.RooArgSet(Bmass, CosThetaK, CosThetaL))
            FitDBPlayer.initFromDB(self.process.odbfilename, args)
    try:
        inputdb = shelve.open(self.process.odbfilename)
        nSigDB = inputdb['nSig']['getVal']
        nBkgCombDB = inputdb['nBkgComb']['getVal']
    finally:
        inputdb.close()

    if nSigDB < 0 or nBkgCombDB < 0:
        raise ValueError("Non-positive yields. nSig={0}, nBkgComb={1}".format(nSigDB, nBkgCombDB))

    # Calculate normalization and then draw
    args = pdfPlots[0][0].getParameters(ROOT.RooArgSet(Bmass, CosThetaK, CosThetaL))
    sigFrac = {}
    bkgCombFrac = {}
    for regionName in ["Fit", "SR", "LSB", "USB"]:
        dataPlots = [[self.process.sourcemanager.get("{0}.{1}".format(dataReader, regionName)), ()], ]

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
            [pdfPlots[0][0], pdfPlots[0][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent),)],
            [pdfPlots[0][0], pdfPlots[1][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent), ROOT.RooFit.Components(pdfPlots[1][0].GetName()))],
            [pdfPlots[0][0], pdfPlots[2][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent), ROOT.RooFit.Components(pdfPlots[2][0].GetName()))],
        ]

        plotFuncs = {
            'B': {'func': Plotter.plotFrameB, 'tag': ""},
            'L': {'func': Plotter.plotFrameL, 'tag': "_cosl"},
            'K': {'func': Plotter.plotFrameK, 'tag': "_cosK"},
        }

        for frame in 'BLK':
            plotFuncs[frame]['func'](dataPlots=dataPlots, pdfPlots=modified_pdfPlots)
            self.canvasPrint(pltName + '_' + regionName + plotFuncs[frame]['tag'])
types.MethodType(plotPostfitBLK, None, Plotter)

plotterCfg = {
    'name': "plotter",
    'switchPlots': [],
}
plotterCfg_allStyle = (ROOT.RooFit.LineColor(1),)
plotterCfg_sigStyle = (ROOT.RooFit.LineColor(4),)
plotterCfg_bkgStyle = (ROOT.RooFit.LineColor(2), ROOT.RooFit.LineStyle(9))
plotterCfg['plots'] = {
    'effi': {
        'func': [plotEfficiency],
        'kwargs': {
            'data_name': "effiHistReader.accXrec",
            'pdf_name': "effi_sigA"}
    },
    'angular3D_sigM': {
        'func': [functools.partial(plotSimpleBLK, frames='B')],
        'kwargs': {
            'pltName': "angular3D_sigA",
            'dataPlots': [["sigMCReader.Fit", ()], ],
            'pdfPlots': [["f_sigM", plotterCfg_sigStyle],
                        ],
            'marks': ['sim']}
    },
    'angular3D_sig2D': {
        'func': [functools.partial(plotSimpleBLK, frames='LK')],
        'kwargs': {
            'pltName': "angular3D_sig2D",
            'dataPlots': [["sigMCReader.Fit", ()], ],
            'pdfPlots': [["f_sig2D", plotterCfg_sigStyle],
                        ],
            'marks': []}
    },
    'angular3D_bkgCombA': {
        'func': [functools.partial(plotSimpleBLK, frames='LK')],
        'kwargs': {
            'pltName': "angular3D_bkgCombA",
            'dataPlots': [["dataReader.SB", ()], ],
            'pdfPlots': [["f_bkgCombA", plotterCfg_bkgStyle],
                         #  ["f_bkgCombAltA", (ROOT.RooFit.LineColor(4), ROOT.RooFit.LineStyle(9))]
                        ],
            'marks': []}
    },
    'angular3D_final': {
        'func': [plotPostfitBLK],
        'kwargs': {
            'pltName': "angular3D_final",
            'dataReader': "dataReader",
            'pdfPlots': [["f_final", plotterCfg_allStyle],
                         ["f_sig3D", plotterCfg_sigStyle],
                         ["f_bkgComb", plotterCfg_bkgStyle],
                        ],
            }
    },
}
#  plotterCfg['switchPlots'].append("effi")
#  plotterCfg['switchPlots'].append("angular3D_sigM")
#  plotterCfg['switchPlots'].append("angular3D_bkgCombA")
plotterCfg['switchPlots'].append("angular3D_final")


plotter = Plotter(plotterCfg)
customized_register_dbfile = functools.partial(register_dbfile, inputDir="{0}/input/selected/".format(modulePath))  # Copy from fitCollection
def customize(self):
    customized_register_dbfile(self)
plotter.customize = types.MethodType(customize, plotter)

if __name__ == '__main__':
    p = Process("testFitCollection", "testProcess", processCfg)
    #  p.cfg['binKey'] = "belowJpsi"
    #  p.cfg['binKey'] = "betweenPeaks"
    #  p.cfg['binKey'] = "abovePsi2s"
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
    #  p.setSequence([dataCollection.effiHistReader, pdfCollection.stdWspaceReader, plotter])
    #  p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, plotter])
    p.setSequence([dataCollection.dataReader, pdfCollection.stdWspaceReader, plotter])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
