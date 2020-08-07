#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 ft=python fdm=indent fdl=0 fdn=3 et:

# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)

from __future__ import print_function, division
import os
import ROOT
ROOT.gROOT.SetBatch(True)
# ROOT.ROOT.EnableImplicitMT(2)  # MT blocks RooDataSet creation when input tree is fat.

import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer

# Shared global settings
isDEBUG = True
isPreliminary = False
def setStyle():
    """ Ref: https://twiki.cern.ch/twiki/bin/viewauth/CMS/Internal/FigGuidelines """
    ROOT.gROOT.SetBatch(1)

    ROOT.gStyle.SetCanvasBorderMode(0)
    ROOT.gStyle.SetCanvasColor(ROOT.kWhite)
    ROOT.gStyle.SetCanvasDefH(600)   # Height of canvas
    ROOT.gStyle.SetCanvasDefW(600)   # Width of canvas
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
    #  ROOT.gStyle.SetHistFillColor(1)
    #  ROOT.gStyle.SetHistFillStyle(0)
    ROOT.gStyle.SetHistLineColor(1)
    ROOT.gStyle.SetHistLineStyle(0)
    ROOT.gStyle.SetHistLineWidth(1)
    #  ROOT.gStyle.SetLegoInnerR(Float_t rad = 0.5)
    #  ROOT.gStyle.SetNumberContours(Int_t number = 20)

    ROOT.gStyle.SetEndErrorSize(2)
    #  ROOT.gStyle.SetErrorMarker(20)
    #  ROOT.gStyle.SetErrorX(0.)

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
    #  ROOT.gStyle.SetDateX(Float_t x=0.01)
    #  ROOT.gStyle.SetDateY(Float_t y=0.01)

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
    ROOT.gStyle.SetPadBottomMargin(0.13)
    ROOT.gStyle.SetPadLeftMargin(0.16)
    ROOT.gStyle.SetPadRightMargin(0.02)

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
    ROOT.gStyle.SetTitleXOffset(0.9)
    ROOT.gStyle.SetTitleYOffset(1.25)
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

    #  Postscript options
    ROOT.gStyle.SetPaperSize(20., 20.)

    ROOT.gStyle.SetHatchesLineWidth(5)
    ROOT.gStyle.SetHatchesSpacing(0.05)

    # My preferences:
    ROOT.gStyle.SetCanvasDefH(600)           # Height of canvas
    ROOT.gStyle.SetCanvasDefW(800)           # Width of canvas
    ROOT.gStyle.SetPadTopMargin(0.08)        # default:0.05, avoid to overlap with 10^n. No Title in paper.
    ROOT.gStyle.SetPadBottomMargin(0.18)     # default:0.13, avoid to overlap with label
    ROOT.gStyle.SetPadLeftMargin(0.16)       # default:0.16, avoid to overlap with label
    ROOT.gStyle.SetPadRightMargin(0.05)      # default:0.02
    ROOT.gStyle.SetPalette(57)               # default(0), rainbow palette is much prettier.
    ROOT.gStyle.SetPaintTextFormat(".4g" )    # precision if plotted with "TEXT"

    ROOT.gStyle.SetOptTitle(0)               # turn off the title

    ROOT.gStyle.SetTitleSize(0.08, "XYZ")    # title of axis
    ROOT.gStyle.SetTitleOffset(0.95, "X")
    ROOT.gStyle.SetTitleOffset(1.03, "YZ")
    ROOT.gStyle.SetLabelOffset(0.01, "XYZ")  # label of axis
    ROOT.gStyle.SetLabelSize(0.055, "X")
    ROOT.gStyle.SetLabelSize(0.055, "YZ")
    ROOT.gStyle.SetNdivisions(505, "XYZ")

    ROOT.gStyle.SetHistFillColor(0)
    ROOT.gStyle.SetHistLineWidth(2)
    ROOT.gStyle.SetMarkerStyle(21)           # x(5),.(1),triangle(22),square(21),circle(20)
    ROOT.gStyle.SetMarkerSize(0.8)
    ROOT.gStyle.SetEndErrorSize(5)

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetStatFontSize(0.04)

    ROOT.gStyle.SetOptFit(0)                 # default:1
    ROOT.gStyle.SetTextSize(0.08)            # default:1, won't affect TLegend until ROOT 5.34
    ROOT.gStyle.SetFuncWidth(2)

    ROOT.gStyle.SetLegendBorderSize(0)       # default:4
    ROOT.gStyle.SetLegendFillColor(ROOT.kWhite)

    ROOT.gStyle.cd()

    ROOT.TGaxis.SetMaxDigits(4)
    ROOT.TGaxis.SetExponentOffset(-0.09, 0, "Y")
    pass

# RooMsgService settings
# Suppress all message below error during minimization to keep short log file.
msgService = ROOT.RooMsgService.instance()
msgService.getStream(0).removeTopic(64)  # Eval
msgService.getStream(0).removeTopic(4)  # Plotting
msgService.getStream(0).removeTopic(2)  # Minimization
msgService.getStream(1).removeTopic(64)
msgService.getStream(1).removeTopic(16384)  # NumIntegration
msgService.getStream(1).removeTopic(4)
msgService.getStream(1).removeTopic(2)
msgService.addStream(4,
                     #  ROOT.RooFit.Topic(64),
                     ROOT.RooFit.Topic(4),
                     ROOT.RooFit.Topic(2))

# default configuration for Process
processCfg = {
    'isBatchJob': False,
    'binKey': 'summary',
}

dbplayer = FitDBPlayer(absInputDir=os.path.join(anaSetup.modulePath, "input", "selected"))

def createNewProcess():
    p = Process("myProcess", "testProcess", processCfg)
    p.addService("dbplayer", dbplayer)
    return p

p = createNewProcess()

# Developers Area
if isDEBUG:
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
