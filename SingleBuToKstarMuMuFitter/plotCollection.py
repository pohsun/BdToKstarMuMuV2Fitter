#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

import types
import shelve
import itertools
import functools

import ROOT

from anaSetup import q2bins
from v2Fitter.Fitter.FitterCore import FitterCore
from v2Fitter.FlowControl.Path import Path
from varCollection import Bmass, CosThetaK, CosThetaL, Mumumass, Kstarmass

from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels

from FitDBPlayer import FitDBPlayer
import dataCollection
import pdfCollection

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
    ROOT.gStyle.SetOptStat(0) #  To display the mean and RMS:   SetOptStat("mr");
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
    ROOT.gStyle.SetOptTitle(0)# 0:turn off the title
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
    ROOT.gStyle.SetPadTickX(1)  #  To get tick marks on the opposite side of the frame
    ROOT.gStyle.SetPadTickY(1)

    #  Change for log plots:
    ROOT.gStyle.SetOptLogx(0)
    ROOT.gStyle.SetOptLogy(0)
    ROOT.gStyle.SetOptLogz(0)

    # My preferences:
    ROOT.gStyle.SetPadTopMargin(0.10)        #  default:0.05, avoid to overlap with 10^n. No Title in paper.
    ROOT.gStyle.SetPadBottomMargin(0.12)     #  default:0.13, avoid to overlap with label
    ROOT.gStyle.SetPadLeftMargin(0.12)       #  default:0.05, avoid to overlap with label
    ROOT.gStyle.SetPadRightMargin(0.05)      #  default:0.05
    ROOT.gStyle.SetPalette(57)               #  default(0), rainbow palette is much prettier.
    ROOT.gStyle.SetPaintTextFormat("5.2f")   #  precision if plotted with "TEXT"

    ROOT.gStyle.SetOptTitle(0)               # turn off the title
    ROOT.gStyle.SetTitleSize(0.05)           # title of hist
    ROOT.gStyle.SetTitleFontSize(0.05)

    ROOT.gStyle.SetTitleSize(0.05, "XYZ")    # title of axis
    ROOT.gStyle.SetTitleOffset(1.0, "X")
    ROOT.gStyle.SetTitleOffset(1.2, "YZ")
    ROOT.gStyle.SetLabelOffset(0.01,"XYZ")   # label of axis
    ROOT.gStyle.SetLabelFont(62, "XYZ")
    ROOT.gStyle.SetLabelSize(0.04, "X")
    ROOT.gStyle.SetLabelSize(0.04, "YZ")
    ROOT.gStyle.SetNdivisions(505, "X")

    ROOT.gStyle.SetHistFillColor(0)
    ROOT.gStyle.SetHistLineWidth(2)
    ROOT.gStyle.SetMarkerStyle(21)            # x(5),.(1),triangle(22),square(21)
    ROOT.gStyle.SetMarkerSize(0.6)

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetStatFontSize(0.04)

    ROOT.gStyle.SetOptFit(0)                 #  default:1
    ROOT.gStyle.SetTextSize(0.05)            #  default:1, won't affect TLegend until ver5.34
    ROOT.gStyle.SetFuncWidth(2)

    ROOT.gStyle.SetLegendBorderSize(0)              #  default:4
    ROOT.gStyle.SetLegendFillColor(ROOT.kWhite)

    ROOT.gStyle.cd()
    pass

class Plotter(Path):
    """The plotter"""
    setStyle()
    canvas = ROOT.TCanvas()

    @staticmethod
    def canvasPrint(name):
        canvas.Update()
        canvas.Print("{0}_{1}.pdf".format(name, q2bins[self.process.cfg['binKey']]['label']))

    latex  = ROOT.TLatex()
    latexCMSMark = staticmethod(lambda x=0.01, y=0.95: latex.DrawLatexNDC(x,y,"#font[22]{CMS} Preliminary"))
    latexCMSSim  = staticmethod(lambda x=0.01, y=0.95: latex.DrawLatexNDC(x,y,"#font[22]{CMS} Simulation"))
    latexLumi    = staticmethod(lambda x=0.88, y=0.95: latex.DrawLatexNDC(x,y,"#font[32]{L} = 19.98 fb^{-1}"))

    frameB = Bmass.frame()
    frameB.SetMinimum(0)
    frameB.SetTitle("")
    frameB_binning = 20

    frameK = CosThetaK.frame()
    frameK.SetMinimum(0)
    frameK.SetTitle("")
    frameK_binning = 20

    frameL = CosThetaL.frame()
    frameL.SetMinimum(0)
    frameL.SetTitle("")
    frameL_binning = 20

    @staticmethod
    def plotFrame(data,  pdf,  fname, frame, binning, dataPlots=[(),], pdfPlots=[(),], marks=[]):
        for p in dataPlots:
            data.plotOn(frame, ROOT.RooFit.Binning(binning), *p)
        for p in pdfPlots:
            pdf.plotOn(frame, ROOT.RooFit.Binning(binning), *p)
        frame.Draw()
        Plotter.latexCMSMark()
        if 'sim' in marks: Plotter.latexCMSSim()
        Plotter.canvasPrint(fname)
    
    plotFrameB = staticmethod(functools.partial(plotFrame.__func__, {'frame': frameB, 'binning': frameB_binning}))
    plotFrameK = staticmethod(functools.partial(plotFrame.__func__, {'frame': frameK, 'binning': frameK_binning}))
    plotFrameL = staticmethod(functools.partial(plotFrame.__func__, {'frame': frameL, 'binning': frameL_binning}))

    @classmethod
    def templateConfig(cls):
        cfg = Path.templateConfig()
        cfg.update({
            'db': "fitResults.db",
            'plotFuncs':[], # (function, kwargs)
        })
        return cfg

    def _runPath(self):
        """"""
        # TODO: NLL plots for afb and fl, https://root.cern.ch/root/html/tutorials/roofit/rf606_nllerrorhandling.C.html
        # https://root.cern.ch/root/html/tutorials/roofit/rf605_profilell.C.html
        for plotter, kwargs in self.cfg['plotFuncs']:
            self._localPlotter = plotter
            self._localPlotter(**kwargs)

def plotEfficiency(self):
    data_name = "effiHistReader.accXrec"
    pdf_name = "effi_sigA"
    data= self.process.sourcemanager.get(data_name)
    pdf = self.process.sourcemanager.get(pdf_name)
    args = pdf.getParameters(data)
    FitDBPlayer.initFromDB(self.cfg.get('db', "fitResults.db"), args)

    binningL = ROOT.RooBinning(len(dataCollection.accXEffThetaLBins)-1, dataCollection.accXEffThetaLBins)
    binningK = ROOT.RooBinning(len(dataCollection.accXEffThetaKBins)-1, dataCollection.accXEffThetaKBins)

    data_accXrec = self.process.sourcemanager.get("effiHistReader.h2_accXrec")
    h2_effi_sigA_fine = pdf.createHistogram("h2_effi_sigA_fine", CosThetaL, ROOT.RooFit.Binning(20), ROOT.RooFit.YVar(CosThetaK, ROOT.RooFit.Binning(20)))
    data_accXrec.SetMinimum(0)
    data_accXrec.SetMaximum(0.00015)
    data_accXrec.SetZTitle("Overall efficiency")
    data_accXrec.Draw("LEGO2")
    h2_effi_sigA_fine.SetLineColor(2)
    h2_effi_sigA_fine.Draw("SURF SAME")
    latexCMSMark()
    canvasPrint("effi_2D")

    h_accXrec_fine_ProjectionX = self.process.sourcemanager.get("effiHistReader.h_accXrec_fine_ProjectionX")
    data_accXrec_fine_ProjectionX = ROOT.RooDataHist("data_accXrec_fine_ProjectionX", "", ROOT.RooArgList(CosThetaL), ROOT.RooFit.Import(h_accXrec_fine_ProjectionX))
    data_accXrec_fine_ProjectionX.plotOn(frameL)
    pdfL = self.process.sourcemanager.get("effi_cosl")
    pdfL.plotOn(frameL, ROOT.RooFit.LineColor(2))
    frameL.Draw()
    latexCMSMark()
    latexCMSSim()
    latex.DrawLatexNDC(.82, .85, "#chi^{{2}}={0:.2f}".format(frameL.chiSquare()))
    canvasPrint("effi_cosl")

    h_accXrec_fine_ProjectionY = self.process.sourcemanager.get("effiHistReader.h_accXrec_fine_ProjectionY")
    data_accXrec_fine_ProjectionY = ROOT.RooDataHist("data_accXrec_fine_ProjectionY", "", ROOT.RooArgList(CosThetaK), ROOT.RooFit.Import(h_accXrec_fine_ProjectionY))
    data_accXrec_fine_ProjectionY.plotOn(frameK)
    pdfK = self.process.sourcemanager.get("effi_cosK")
    pdfK.plotOn(frameK, ROOT.RooFit.LineColor(2))
    frameK.Draw()
    latexCMSMark()
    latexCMSSim()
    latex.DrawLatexNDC(.82, .85, "#chi^{{2}}={0:.2f}".format(frameK.chiSquare()))
    canvasPrint("effi_cosK")

plotter = Plotter({
    'name': "plotter",
})

plots = [
    ("effi_sigA", "effiHistReader.accXrec"),
    ("f_sigM", "sigMCReader.Fit"),
    ("f_sigA", "sigMCGENReader.Fit"),
    ("f_sig2D", "sigMCReader.Fit"),
    ("f_bkgCombA", "dataReader.SB"),
    ("f_final", "dataReader.Fit"),
]

def customize(self):
    self.cfg['db'] = "fitResults_{0}.db".format(q2bins[self.process.cfg['binKey']]['label'])
plotter.customize = types.MethodType(customize, plotter)

if __name__ == '__main__':
    p = Process("testFitCollection", "testProcess")
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
    p.setSequence([dataCollection.effiHistReader, pdfCollection.stdWspaceReader, plotter])
    # p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sigMFitter])
    # p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sig2DFitter])
    # p.setSequence([dataCollection.dataReader, pdfCollection.stdWspaceReader, bkgCombAFitter])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
