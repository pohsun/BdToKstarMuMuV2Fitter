#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 sts=4 fdm=indent fdl=0 fdn=1 ft=python et:

import os
import re
import math
import types
import functools
import shelve
from array import array
from argparse import ArgumentParser

import ROOT

import SingleBuToKstarMuMuFitter.cpp
from SingleBuToKstarMuMuFitter.anaSetup import q2bins
from SingleBuToKstarMuMuFitter.StdFitter import unboundFlToFl, unboundAfbToAfb, flToUnboundFl, afbToUnboundAfb

from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer
from SingleBuToKstarMuMuFitter.varCollection import Bmass, CosThetaK, CosThetaL, Mumumass, Q2, Kstarmass, Kshortmass, genCosThetaK, genCosThetaL

from SingleBuToKstarMuMuFitter.StdProcess import p, setStyle, isPreliminary
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.pdfCollection as pdfCollection
import SingleBuToKstarMuMuFitter.fitCollection as fitCollection

from SingleBuToKstarMuMuFitter.Plotter import Plotter, defaultPlotRegion, plotterCfg_styles

def plotSpectrumWithSimpleFit(self, pltName, dataPlots, marks):
    """ Assuming len(dataPlots) == 1, fit to the data. """
    for pIdx, plt in enumerate(dataPlots):
        dataPlots[pIdx] = self.initDataPlotCfg(plt)
    wspace = ROOT.RooWorkspace("wspace")
    getattr(wspace, 'import')(Bmass)
    Bmass.setRange("Fit", 4.76, 5.80)
    wspace.factory("RooGaussian::gauss1(Bmass,mean[5.28,5.25,5.39],sigma1[0.02,0.01,0.04])")
    wspace.factory("RooGaussian::gauss2(Bmass,mean,sigma2[0.08,0.04,0.10])")
    wspace.factory("SUM::sigM(sigFrac[0.8,0,1]*gauss1,gauss2)")
    wspace.factory("c1[-5.6,-20,20]")
    wspace.factory("EXPR::bkgCombM('exp(c1*Bmass)',{Bmass,c1})")
    #  wspace.factory("c2[0,-20,20]")
    #  wspace.factory("c3[0,-20,20]")
    #  wspace.factory("EXPR::bkgCombM('exp(c1*Bmass)+c2+c3*Bmass',{Bmass,c1,c2,c3})")
    wspace.factory("SUM::model(tmp_nSig[0,1e5]*sigM,tmp_nBkg[0,1e5]*bkgCombM)")
    pdfPlots = [
        [wspace.pdf('model'), plotterCfg_styles['allStyle'], None, "Total fit"],
        [wspace.pdf('model'), plotterCfg_styles['sigStyle'] + (ROOT.RooFit.Components('sigM'),), None, "Signal"],
        [wspace.pdf('model'), plotterCfg_styles['bkgStyle'] + (ROOT.RooFit.Components('bkgCombM'),), None, "Background"],
    ]

    pdfPlots[0][0].fitTo(dataPlots[0][0], ROOT.RooFit.Range(defaultPlotRegion), ROOT.RooFit.Minos(True), ROOT.RooFit.Extended(True))

    def avgWidth(fr, w1, w2):
        return math.sqrt(fr * w1**2 + (1. - fr) * w2**2)
    self.logger.logINFO("Averaged peak width is {0}".format(avgWidth(wspace.var('sigFrac').getVal(), wspace.var('sigma1').getVal(), wspace.var('sigma2').getVal())))

    if dataPlots[0][0].sumEntries() > 2e3:
        Plotter.plotFrameB_fine(dataPlots=dataPlots, pdfPlots=pdfPlots, marks=marks, legend=True)
    else:
        Plotter.plotFrameB_fine(dataPlots=dataPlots, pdfPlots=pdfPlots, marks=marks, legend=True)

    self.canvasPrint(pltName)
types.MethodType(plotSpectrumWithSimpleFit, None, Plotter)

def plotSimpleBLK(self, pltName, dataPlots, pdfPlots, marks, frames='BLK', shareDataNorm=False):
    for pIdx, plt in enumerate(dataPlots):
        dataPlots[pIdx] = self.initDataPlotCfg(plt)
        if shareDataNorm and pIdx != 0:
            dataPlots[pIdx][1] += (ROOT.RooFit.Rescale(dataPlots[0][0].sumEntries() / dataPlots[pIdx][0].sumEntries()),)
    for pIdx, plt in enumerate(pdfPlots):
        pdfPlots[pIdx] = self.initPdfPlotCfg(plt)

    plotFuncs = {
        'B': {'func': Plotter.plotFrameB_fine, 'tag': ""},
        'L': {'func': Plotter.plotFrameL, 'tag': "_cosl"},
        'K': {'func': Plotter.plotFrameK, 'tag': "_cosK"},
    }

    for frame in frames:
        plotFuncs[frame]['func'](dataPlots=dataPlots, pdfPlots=pdfPlots, marks=marks, process=self.process, legend=True)
        Plotter.latexQ2(self.process.cfg['binKey'])
        self.canvasPrint(pltName + plotFuncs[frame]['tag'])
types.MethodType(plotSimpleBLK, None, Plotter)

def plotEfficiency(self, dataName, pdfName, argAliasInDB=None, pltName="effi"):
    data = self.process.sourcemanager.get(dataName)
    pdf = self.process.sourcemanager.get(pdfName)
    if data == None or pdf == None:
        self.logger.logWARNING("Skip plotEfficiency. pdf or data not found")
        return
    args = pdf.getParameters(data)
    FitDBPlayer.initFromDB(self.process.dbplayer.odbfile, args, argAliasInDB)

    binningL = ROOT.RooBinning(len(dataCollection.accXEffThetaLBins) - 1, dataCollection.accXEffThetaLBins)
    binningK = ROOT.RooBinning(len(dataCollection.accXEffThetaKBins) - 1, dataCollection.accXEffThetaKBins)

    data_accXrec = self.process.sourcemanager.get("effiHistReader.h2_accXrec")
    data_accXrec.Scale(100)
    data_accXrec.SetMinimum(0)
    data_accXrec.SetMaximum(0.1 if self.process.cfg['binKey'] in ['jpsi', 'psi2s'] else 0.020)  # Z axis in percentage
    h2_effi_sigA_fine = pdf.createHistogram("h2_effi_sigA_fine", CosThetaL, ROOT.RooFit.Binning(20), ROOT.RooFit.YVar(CosThetaK, ROOT.RooFit.Binning(20)))
    h2_effi_sigA_fine.Scale(100 * h2_effi_sigA_fine.GetNbinsX()/2 * h2_effi_sigA_fine.GetNbinsY()/2)

    data_accXrec.SetXTitle(CosThetaL.GetTitle())
    data_accXrec.SetYTitle(CosThetaK.GetTitle())
    data_accXrec.SetZTitle("Efficiency [%]")
    data_accXrec.SetTitleOffset(1.3, "X")
    data_accXrec.SetTitleOffset(1.5, "Y")
    data_accXrec.SetTitleOffset(1.5, "Z")
    data_accXrec.Draw("LEGO2")
    h2_effi_sigA_fine.SetLineColor(2)
    h2_effi_sigA_fine.Draw("SURF SAME0")
    Plotter.latexCMSSim(.08, .93)
    # Plotter.latexCMSExtra(.08, .87)
    Plotter.latexQ2(self.process.cfg['binKey'], .50, .93)
    self.canvasPrint(pltName + "_2D")

    data_accXrec.Scale(0.01)  # Scale back, Normalization to be handled with RooFit in 1D plot

    cloned_frameL = Plotter.frameL.emptyClone("cloned_frameL")
    h_accXrec_fine_ProjectionX = self.process.sourcemanager.get("effiHistReader.h_accXrec_fine_ProjectionX")
    data_accXrec_fine_ProjectionX = ROOT.RooDataHist("data_accXrec_fine_ProjectionX", "", ROOT.RooArgList(CosThetaL), ROOT.RooFit.Import(h_accXrec_fine_ProjectionX))
    data_accXrec_fine_ProjectionX.plotOn(cloned_frameL, ROOT.RooFit.Name("dataL"), ROOT.RooFit.Rescale(100), *plotterCfg_styles['mcStyleBase'])
    pdfL = self.process.sourcemanager.get("effi_cosl")
    pdfL.plotOn(cloned_frameL, ROOT.RooFit.Normalization(100, ROOT.RooAbsReal.Relative), ROOT.RooFit.Name("pdfL"), *plotterCfg_styles['sigStyleNoFillBase'])
    cloned_frameL.GetYaxis().SetTitle("Efficiency [%]")
    # cloned_frameL.GetYaxis().SetTitleOffset(1.)
    cloned_frameL.SetMaximum(1.5 * cloned_frameL.GetMaximum())
    cloned_frameL.Draw()
    legend = ROOT.TLegend(.7,.7,.95,.9)
    legend.SetFillColor(0)
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    legend.AddEntry(cloned_frameL.findObject("dataL").GetHistogram(), "MC", "PE")
    histL = cloned_frameL.findObject("pdfL").GetHistogram()
    histL.SetLineColor(4)
    legend.AddEntry(histL, "Fit", "LF")
    legend.Draw()
    Plotter.latexDataMarks(['sim'])
    Plotter.latexQ2(self.process.cfg['binKey'])
    #  Plotter.latex.DrawLatexNDC(.85, .89, "#chi^{{2}}={0:.2f}".format(cloned_frameL.chiSquare()))
    self.canvasPrint(pltName + "_cosl")

    cloned_frameK = Plotter.frameK.emptyClone("cloned_frameK")
    h_accXrec_fine_ProjectionY = self.process.sourcemanager.get("effiHistReader.h_accXrec_fine_ProjectionY")
    data_accXrec_fine_ProjectionY = ROOT.RooDataHist("data_accXrec_fine_ProjectionY", "", ROOT.RooArgList(CosThetaK), ROOT.RooFit.Import(h_accXrec_fine_ProjectionY))
    data_accXrec_fine_ProjectionY.plotOn(cloned_frameK, ROOT.RooFit.Name("dataK"), ROOT.RooFit.Rescale(100), *plotterCfg_styles['mcStyleBase'])
    pdfK = self.process.sourcemanager.get("effi_cosK")
    pdfK.plotOn(cloned_frameK, ROOT.RooFit.Normalization(100, ROOT.RooAbsReal.Relative), ROOT.RooFit.Name("pdfK"), *plotterCfg_styles['sigStyleNoFillBase'])
    cloned_frameK.GetYaxis().SetTitle("Efficiency [%]")
    # cloned_frameK.GetYaxis().SetTitleOffset(1.)
    cloned_frameK.SetMaximum(1.5 * cloned_frameK.GetMaximum())
    cloned_frameK.Draw()
    legend.Clear()
    legend.AddEntry(cloned_frameK.findObject("dataK").GetHistogram(), "MC", "PE")
    histK = cloned_frameK.findObject("pdfK").GetHistogram()
    histK.SetLineColor(4)
    legend.AddEntry(histK, "Fit", "LF")
    legend.Draw()
    Plotter.latexDataMarks(['sim'])
    Plotter.latexQ2(self.process.cfg['binKey'])
    #  Plotter.latex.DrawLatexNDC(.85, .89, "#chi^{{2}}={0:.2f}".format(cloned_frameK.chiSquare()))
    self.canvasPrint(pltName + "_cosK")
types.MethodType(plotEfficiency, None, Plotter)

def plotPostfitBLK(self, pltName, dataReader, pdfPlots):
    """ Specification of plotSimpleBLK for post-fit plots. WARNING: Order of pdfPlots matters! """

    ROOT.gStyle.SetTitleOffset(0.95, "Y")

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
    for regionName in ["Fit", "SR", "LSB", "USB", "SB", "innerSB", "outerSB"]:
        drawRegionName = {'SB': "LSB,USB", 'innerSB': "innerLSB,innerUSB", 'outerSB': "outerLSB,outerUSB"}.get(regionName, regionName)
        dataPlots = [["{0}.{1}".format(dataReader, "Full"), plotterCfg_styles['dataStyle'] + (ROOT.RooFit.CutRange(drawRegionName),), "Data"], ]
        for pIdx, p in enumerate(dataPlots):
            dataPlots[pIdx] = self.initDataPlotCfg(p)

        # Bind the 'Bmass' defined in PDF with 'getObservables' to createIntegral
        # WARNING: Integral to multiple ranges with RooExtendPdf seems to be buggy, be very careful!
        #          Order of pdfPlots[0,1,2] do matters.
        obs = pdfPlots[1][0].getObservables(dataPlots[0][0])
        sigFrac[regionName] = pdfPlots[1][0].createIntegral(
            obs,
            ROOT.RooFit.NormSet(obs),
            ROOT.RooFit.Range(regionName)).getVal()

        obs = pdfPlots[2][0].getObservables(dataPlots[0][0])
        bkgCombFrac[regionName] = pdfPlots[2][0].createIntegral(
            obs,
            ROOT.RooFit.NormSet(obs),
            ROOT.RooFit.Range(regionName)).getVal()

        if regionName in ["SB", "innerSB"]:
            sigFrac[regionName] -= sigFrac['SR']
            bkgCombFrac[regionName] -= bkgCombFrac['SR']
        elif regionName == "outerSB":
            sigFrac[regionName] -= sigFrac['SR']
            sigFrac[regionName] -= sigFrac['innerSB']
            bkgCombFrac[regionName] -= bkgCombFrac['SR']
            bkgCombFrac[regionName] -= bkgCombFrac['innerSB']

        nTotal_local = nSigDB * sigFrac[regionName] + nBkgCombDB * bkgCombFrac[regionName]
        self.logger.logDEBUG("{0}: {1}, {2}, {3}, {4}".format(regionName, nSigDB, sigFrac[regionName], nBkgCombDB, bkgCombFrac[regionName]))
        self.logger.logINFO("{0}: {1}, {2}, {3}".format(regionName, nSigDB * sigFrac[regionName], nBkgCombDB * bkgCombFrac[regionName], nTotal_local))

        if regionName not in ['SB', 'innerSB', 'outerSB']:
            modified_pdfPlots = [
                [pdfPlots[0][0],
                 pdfPlots[0][1] + (ROOT.RooFit.ProjectionRange(drawRegionName),),
                 pdfPlots[0][2],
                 pdfPlots[0][3]],
                [pdfPlots[0][0],
                 pdfPlots[1][1] + (ROOT.RooFit.ProjectionRange(drawRegionName), ROOT.RooFit.Components(pdfPlots[1][0].GetName())),
                 pdfPlots[1][2],
                 pdfPlots[1][3]],
                [pdfPlots[0][0],
                 pdfPlots[2][1] + (ROOT.RooFit.ProjectionRange(drawRegionName), ROOT.RooFit.Components(pdfPlots[2][0].GetName())),
                 pdfPlots[2][2],
                 pdfPlots[2][3]],
                [pdfPlots[0][0],
                 pdfPlots[0][1] + (ROOT.RooFit.ProjectionRange(drawRegionName),),
                 pdfPlots[0][2],
                 None], # Duplication of the Total fit to overwrite components. Legend is ignored.
            ]
        else:
            # WARNING: An expedient to create post-fit plots in multiple regions.
            #   There seems to be a bug for RooExtendPdf that normalization blows up in multiple regions case.

            # Correct the shape of f_final
            args.find("nSig").setVal(nSigDB * sigFrac[regionName])
            args.find("nBkgComb").setVal(nBkgCombDB * bkgCombFrac[regionName])
        
            modified_pdfPlots = [
                [pdfPlots[0][0],
                 pdfPlots[0][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent),),
                 pdfPlots[0][2],
                 pdfPlots[0][3]],
                [pdfPlots[0][0],
                 pdfPlots[1][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent), ROOT.RooFit.Components(pdfPlots[1][0].GetName())),
                 pdfPlots[1][2],
                 pdfPlots[1][3]],
                [pdfPlots[0][0],
                 pdfPlots[2][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent), ROOT.RooFit.Components(pdfPlots[2][0].GetName())),
                 pdfPlots[2][2],
                 pdfPlots[2][3]],
                [pdfPlots[0][0],
                 pdfPlots[0][1] + (ROOT.RooFit.Normalization(nTotal_local, ROOT.RooAbsReal.NumEvent),),
                 pdfPlots[0][2],
                 None], # Duplication of the Total fit to overwrite components. Legend is ignored.
            ]

        legend = ROOT.TLegend(.64, .60, .94, .90)
        legend.SetFillColor(0)
        legend.SetFillStyle(0)
        legend.SetBorderSize(0)
        
        plotFuncs = {
            'B': {'func': Plotter.plotFrameB_fine, 'tag': "", 'scaleYaxis': 1.2, 'legend': legend},
            'L': {'func': Plotter.plotFrameL, 'tag': "_cosl", 'scaleYaxis': 1.6, 'legend': legend},
            'K': {'func': Plotter.plotFrameK, 'tag': "_cosK", 'scaleYaxis': 1.6, 'legend': legend},
        }

        drawLatexFitResults = False
        for frame in 'BLK':
            plotFuncs[frame]['func'](
                    dataPlots=dataPlots,
                    pdfPlots=modified_pdfPlots,
                    marks={'extraArgs': {'msg': ""}} if regionName == "Fit" else None,
                    legend=plotFuncs[frame].get('legend', legend),
                    scaleYaxis=plotFuncs[frame]['scaleYaxis'])
            if drawLatexFitResults:
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
            else:
                self.logger.logINFO("Y_{{Signal}} = {0:.2f}".format(nSigDB * sigFrac[regionName]))
                self.logger.logINFO("Y_{{Background}} = {0:.2f}".format(nBkgCombDB * bkgCombFrac[regionName]))
                self.logger.logINFO("A_{{FB}} = {0:.2f}".format(afbDB))
                self.logger.logINFO("F_{{L}} = {0:.2f}".format(flDB))

            Plotter.latexQ2(self.process.cfg['binKey'])
            self.canvasPrint(pltName + '_' + regionName + plotFuncs[frame]['tag'])
types.MethodType(plotPostfitBLK, None, Plotter)

def plotSummaryAfbFl(self, pltName, dbSetup, drawSM=False, marks=None):
    """ Check carefully the keys in 'dbSetup' """
    if marks is None:
        marks = {'marks': None,
                'extraArgs': {'y': 0.86},
                }
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
        systErrorSourceBlackList = ["^syst_altFitRange_.*$"]
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

        # Sanity check, bound error to boundary when MINOS is FAILED.
        minimum_err = 1e-4  # 1e-3 is too wide for full signal MC
        if yyFlErrHi < minimum_err:
            yyFlErrHi = (1 - 4 * abs(afb) / 3) - fl
        if yyFlErrLo < minimum_err:
            yyFlErrLo = fl
        if yyAfbErrHi < minimum_err:
            yyAfbErrHi = 0.75 * (1 - fl) - afb
        if yyAfbErrLo < minimum_err:
            yyAfbErrLo = afb + 0.75 * (1- fl)
        return yyFlErrHi, yyFlErrLo, yyAfbErrHi, yyAfbErrLo

    statErrorMethods = {
        'FeldmanCousins': getStatError_FeldmanCousins,
        'Minuit': getStatError_Minuit,
    }

    legendFl = ROOT.TLegend(.78, .72, .95, .92)
    legendFl.SetFillColor(0)
    legendFl.SetFillStyle(0)
    legendFl.SetBorderSize(0)

    legendAfb = ROOT.TLegend(.78, .20, .95, .40)
    legendAfb.SetFillColor(0)
    legendAfb.SetFillStyle(0)
    legendAfb.SetBorderSize(0)

    for dbsIdx, dbs in enumerate(dbSetup):
        title = dbs.get('title', None)
        dbPat = dbs.get('dbPat', self.process.dbplayer.absInputDir + "/fitResults_{binLabel}.db")
        argAliasInDB = dbs.get('argAliasInDB', {})
        withSystError = dbs.get('withSystError', False)
        statErrorKey = dbs.get('statErrorKey', 'Minuit')
        drawOpt = dbs.get('drawOpt', ["P0"])
        fillColor = dbs.get('fillColor', 2)
        fillStyle = dbs.get('fillStyle', 3003)
        legendOpt = dbs.get('legendOpt', None)
        dbs.update({
            'drawOpt': drawOpt,
            'legendOpt': legendOpt,
        })

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
        grAfb.SetMarkerSize(2)
        grAfb.SetLineColor(fillColor if fillColor else 2)
        grAfb.SetFillColor(fillColor if fillColor else 2)
        grAfb.SetFillStyle(fillStyle if fillStyle else 3003)
        grAfbs.append(grAfb)

        grFl = ROOT.TGraphAsymmErrors(len(binKeys), xx, yyFl, xxErr, xxErr, yyFlErrLo, yyFlErrHi)
        grFl.SetMarkerColor(fillColor if fillColor else 2)
        grFl.SetMarkerSize(2)
        grFl.SetLineColor(fillColor if fillColor else 2)
        grFl.SetFillColor(fillColor if fillColor else 2)
        grFl.SetFillStyle(fillStyle if fillStyle else 3003)
        grFls.append(grFl)

        if legendOpt:
            legendAfb.AddEntry(grAfb, title, legendOpt)
            legendFl.AddEntry(grFl, title, legendOpt)

    if drawSM:
        dbSetup.insert(0, {
            'drawOpt': ["2", "ZP0"],
        })
        yyFl = array('d', [0] * len(binKeys))
        yyFlErrHi = array('d', [0] * len(binKeys))
        yyFlErrLo = array('d', [0] * len(binKeys))

        yyAfb = array('d', [0] * len(binKeys))
        yyAfbErrHi = array('d', [0] * len(binKeys))
        yyAfbErrLo = array('d', [0] * len(binKeys))

        for binKeyIdx, binKey in enumerate(['belowJpsi', 'betweenPeaks', 'abovePsi2s']):
            if binKey != 'betweenPeaks':
                fl = q2bins[binKey]['sm']['fl']
                afb = q2bins[binKey]['sm']['afb']
                yyFl[binKeyIdx] = fl['getVal']
                yyAfb[binKeyIdx] = afb['getVal']
                yyFlErrHi[binKeyIdx] = fl['getError']
                yyFlErrLo[binKeyIdx] = fl['getError']
                yyAfbErrHi[binKeyIdx] = afb['getError']
                yyAfbErrLo[binKeyIdx] = afb['getError']
            else:
                yyFl[binKeyIdx] = -1
                yyAfb[binKeyIdx] = -2
                yyFlErrHi[binKeyIdx] = 0
                yyFlErrLo[binKeyIdx] = 0
                yyAfbErrHi[binKeyIdx] = 0
                yyAfbErrLo[binKeyIdx] = 0

        grAfb = ROOT.TGraphAsymmErrors(len(binKeys), xx, yyAfb, xxErr, xxErr, yyAfbErrLo, yyAfbErrHi)
        grAfb.SetMarkerColor(4)
        grAfb.SetMarkerStyle(4)
        grAfb.SetMarkerSize(2)
        grAfb.SetLineColor(4)
        grAfb.SetFillColor(4)
        grAfb.SetFillStyle(3003)
        grAfbs.insert(0, grAfb)
        legendAfb.AddEntry(grAfb, "SM", "LPF")

        grFl = ROOT.TGraphAsymmErrors(len(binKeys), xx, yyFl, xxErr, xxErr, yyFlErrLo, yyFlErrHi)
        grFl.SetMarkerColor(4)
        grFl.SetMarkerStyle(4)
        grFl.SetMarkerSize(2)
        grFl.SetLineColor(4)
        grFl.SetFillColor(4)
        grFl.SetFillStyle(3003)
        grFls.insert(0, grFl)
        legendFl.AddEntry(grFl, "SM", "LPF")

    for grIdx, gr in enumerate(grAfbs):
        gr.SetTitle("")
        gr.GetXaxis().SetTitle(Q2.GetTitle())
        gr.GetXaxis().SetRangeUser(1, 19)
        gr.GetYaxis().SetTitle("A_{FB}")
        gr.GetYaxis().SetTitleOffset(0.8)
        gr.GetYaxis().SetRangeUser(-1., 1.)
        gr.SetLineWidth(2)
        drawOpt = dbSetup[grIdx]['drawOpt'] if isinstance(dbSetup[grIdx]['drawOpt'], list) else [dbSetup[grIdx]['drawOpt']]
        for optIdx, opt in enumerate(drawOpt):
            if grIdx == 0:
                gr.Draw("A" + opt if optIdx == 0 else opt)
            else:
                gr.Draw(opt + " SAME")
    jpsiBox = ROOT.TBox(8.69, -1, 10.08, 1)
    psi2sBox = ROOT.TBox(12.87, -1, 14.17, 1)
    jpsiBox.SetFillColor(17)
    psi2sBox.SetFillColor(17)
    jpsiBox.Draw()
    psi2sBox.Draw()
    legendAfb.Draw()
    line = ROOT.TLine()
    line.SetLineWidth(2)
    line.DrawLineNDC(.785, .335, .785, .365)
    line.DrawLineNDC(.817, .335, .817, .365)
    Plotter.latexDataMarks(**marks)
    self.canvasPrint(pltName + '_afb', False)

    for grIdx, gr in enumerate(grFls):
        gr.SetTitle("")
        gr.GetXaxis().SetTitle(Q2.GetTitle())
        gr.GetXaxis().SetRangeUser(1, 19)
        gr.GetYaxis().SetTitle("F_{L}")
        gr.GetYaxis().SetTitleOffset(0.8)
        gr.GetYaxis().SetRangeUser(0, 1.2)
        gr.SetLineWidth(2)
        drawOpt = dbSetup[grIdx]['drawOpt'] if isinstance(dbSetup[grIdx]['drawOpt'], list) else [dbSetup[grIdx]['drawOpt']]
        for optIdx, opt in enumerate(drawOpt):
            if grIdx == 0:
                gr.Draw("A" + opt if optIdx == 0 else opt)
            else:
                gr.Draw(opt + " SAME")
    jpsiBox.SetY1(0)
    jpsiBox.SetY2(1.2)
    psi2sBox.SetY1(0)
    psi2sBox.SetY2(1.2)
    jpsiBox.Draw()
    psi2sBox.Draw()
    legendFl.Draw()
    line.DrawLineNDC(.785, .855, .785, .885)
    line.DrawLineNDC(.817, .855, .817, .885)
    Plotter.latexDataMarks(**marks)
    self.canvasPrint(pltName + '_fl', False)
types.MethodType(plotSummaryAfbFl, None, Plotter)

def plotOnXYZ(self, pltName, dataName, createHistogramArgs, drawOpt=None, marks=None):
    # Ref: https://root.cern.ch/root/html/tutorials/roofit/rf309_ndimplot.C.html
    data = self.process.sourcemanager.get(dataName)
    if data == None:
        self.logger.logWARNING("Skip plotOnXYZ. dataset {0} not found".format(dataName))
        return
    marks = {} if marks is None else marks
    drawOpt = [] if drawOpt is None else drawOpt
    # Explicit claim of inherited method:
    #   https://root-forum.cern.ch/t/roodatasets-weighs-createhistogram-and-roondkeyspdf/16240/5
    hist = super(data.__class__, data).createHistogram(pltName, *createHistogramArgs)

    hist.SetFillColor(2)
    hist.SetMinimum(0)
    hist.SetMaximum(1.5 * hist.GetMaximum())
    for opt in drawOpt:
        if re.match("LEGO", opt.upper()):
            hist.SetTitleOffset(1.4, "X")
            hist.SetTitleOffset(1.8, "Y")
            hist.SetTitleOffset(1.5, "Z")
            hist.Draw(opt)
            Plotter.latexCMSSim(.08, .93)
            Plotter.latexCMSExtra(.08, .87, marks.get('extraArgs', {}).get('msg', None))
            Plotter.latexQ2(self.process.cfg['binKey'], .50, .93)
            self.canvasPrint(pltName + "_LEGO")
        elif re.match("COL", opt.upper()):
            hist.Draw(opt)
            Plotter.latexDataMarks(**marks)
            self.canvasPrint(pltName + "_COL")
        elif re.match("BOX", opt.upper()):
            hist.Draw(opt)
            Plotter.latexDataMarks(**marks)
            self.canvasPrint(pltName + "_BOX")
        else:
            hist.Draw(opt)
            Plotter.latexDataMarks(**marks)
            self.canvasPrint(pltName)

types.MethodType(plotOnXYZ, None, Plotter)


plotterCfg = {
    'name': "plotter",
    'switchPlots': [],
    'plots': {},
}

plotterCfg['plots']['simpleBLK'] = { # Most general case, to be customized by user
    'func': [functools.partial(plotSimpleBLK, frames='BLK')],
    'kwargs': {
        'pltName': "simpleBLK",
        'dataPlots': [["ToyGenerator.mixedToy", plotterCfg_styles['mcStyle'], "Toy"], ],
        'pdfPlots': [["f_sigM", plotterCfg_styles['sigStyle'], None, None],
                    ],
        'marks': {'marks': ['sim']}},
}
plotterCfg['plots']['simpleSpectrum'] = {
    'func': [plotSpectrumWithSimpleFit],
    'kwargs': {
        'pltName': "h_Bmass",
        'dataPlots': [["dataReader.Fit"                   , plotterCfg_styles['dataStyle'] , None]              , ] , # Standard
        # 'dataPlots': [["dataReader.Fit_noResVeto"         , plotterCfg_styles['dataStyle'] , None]              , ] ,
        # 'dataPlots': [["dataReader.Fit_antiSignal"        , plotterCfg_styles['dataStyle'] , None]              , ] ,
        # 'dataPlots': [["dataReader.Fit_antiResVeto"       , plotterCfg_styles['dataStyle'] , None]              , ] , # No tail
        # 'dataPlots': [["bkgJpsiMCReader.Fit_antiResVeto"  , plotterCfg_styles['mcStyle']   , "J/#psi K^{*+}"]   , ] ,
        # 'dataPlots': [["bkgPsi2sMCReader.Fit_antiResVeto" , plotterCfg_styles['mcStyle']   , "#psi(2S) K^{*+}"] , ] ,
        'marks': {}
    }
}

# Standard fitting procedure
plotterCfg['plots']['effi'] = {
    'func': [plotEfficiency],
    'kwargs': {
        'dataName': "effiHistReader.accXrec",
        'pdfName': "effi_sigA",
    },
}
plotterCfg['plots']['angular3D_sigM'] = {
    'func': [functools.partial(plotSimpleBLK, frames='B')],
    'kwargs': {
        'pltName': "angular3D_sigM",
        'dataPlots': [["sigMCReader.Fit", plotterCfg_styles['mcStyle'], "Simulation"], ],
        'pdfPlots': [["f_sigM", plotterCfg_styles['sigStyle'], fitCollection.setupSigMFitter['argAliasInDB'], "Total fit"],
                    ],
        'marks': {'marks': ['sim']}}
}
plotterCfg['plots']['angular3D_sig2D'] = {
    'func': [functools.partial(plotSimpleBLK, frames='LK')],
    'kwargs': {
        'pltName': "angular3D_sig2D",
        'dataPlots': [["sigMCReader.Fit", plotterCfg_styles['mcStyle'], "Simulation"], ],
        'pdfPlots': [["f_sig2D", plotterCfg_styles['sigStyle'], fitCollection.setupSig2DFitter['argAliasInDB'], None],
                    ],
        'marks': {'marks': ['sim']}}
}
plotterCfg['plots']['angular2D_summary_RECO2GEN'] = {
    'func': [plotSummaryAfbFl],
    'kwargs': {
        'pltName': "angular2D_summary_RECO2GEN",
        'dbSetup': [{'title': "RECO",
                     'argAliasInDB': {'unboundFl': 'unboundFl_RECO', 'unboundAfb': 'unboundAfb_RECO'},
                     'legendOpt': "LPE",
                     },
                    {'title': "GEN",
                     'argAliasInDB': {'unboundFl': 'unboundFl_GEN', 'unboundAfb': 'unboundAfb_GEN'},
                     'fillColor': 4,
                     'legendOpt': "LPE",
                     },
                    ],
        'marks': {'marks': ['sim']},
    },
}
plotterCfg['plots']['angular3D_bkgJpsiM'] = {
    'func': [functools.partial(plotSimpleBLK, frames='B')],
    'kwargs': {
        'pltName': "angular3D_bkgJpsiM",
        'dataPlots': [["bkgJpsiMCReader.Fit", plotterCfg_styles['mcStyle'], "Simulation"], ],
        'pdfPlots': [],
        'marks': {'marks': ['sim']}}
}
plotterCfg['plots']['angular3D_bkgPsi2sM'] = {
    'func': [functools.partial(plotSimpleBLK, frames='B')],
    'kwargs': {
        'pltName': "angular3D_bkgPsi2sM",
        'dataPlots': [["bkgPsi2sMCReader.Fit", plotterCfg_styles['mcStyle'], "Simulation"], ],
        'pdfPlots': [],
        'marks': {'marks': ['sim']}}
}
plotterCfg['plots']['angular3D_bkgCombA'] = {
    'func': [functools.partial(plotSimpleBLK, frames='LK')],
    'kwargs': {
        'pltName': "angular3D_bkgCombA",
        'dataPlots': [["dataReader.SB", plotterCfg_styles['dataStyle'], "Data"], ],
        'pdfPlots': [["f_bkgCombA", plotterCfg_styles['bkgStyle'], None, "Analytic Bkg."],
                    ],
        'marks': {}}
}
plotterCfg['plots']['angular3D_final'] = {
    'func': [plotPostfitBLK],
    'kwargs': {
        'pltName': "angular3D_final",
        'dataReader': "dataReader",
        'pdfPlots': [["f_final", plotterCfg_styles['allStyleBase'], None, "Total fit"], # Draw combined again without put a legend
                     ["f_sig3D", plotterCfg_styles['sigStyleBase'], None, "Signal"],
                     ["f_bkgComb", plotterCfg_styles['bkgStyleBase'], None, "Background"],
                    ],
    }
}
plotterCfg['plots']['angular3D_summary'] = {
    'func': [plotSummaryAfbFl],
    'kwargs': {
        'pltName': "angular3D_summary",
        'dbSetup': [{'title': "Data",
                     'statErrorKey': 'FeldmanCousins',
                     'legendOpt': "LPE",
                     'fillColor': 1,
                     },
                    {'title': "Data",
                     'statErrorKey': 'FeldmanCousins',
                     'fillColor': 1,
                     'withSystError': True,
                     },
                    ],
        'drawSM': True,
    },
}

# Syst uncertainty
plotterCfg['plots']['angular3D_bkgCombAAltA'] = {
    'func': [functools.partial(plotSimpleBLK, frames='LK')],
    'kwargs': {
        'pltName': "angular3D_bkgCombAAltA",
        'dataPlots': [["dataReader.SB", plotterCfg_styles['dataStyle'], "Data"], ],
        'pdfPlots': [["f_bkgCombAAltA", plotterCfg_styles['bkgStyle'], None, "Smooth Bkg."],
                    ],
        'marks': {}}
}
angular3D_finalAltBkgCombA_argAliasInDB = {
        'unboundAfb': 'unboundAfb_altBkgCombA', 
        'unboundFl': 'unboundFl_altBkgCombA',
        'fs': 'fs_altBkgCombA',
        'as': 'as_altBkgCombA',
        'nSig': 'nSig_altBkgCombA',
        'nBkgComb': 'nBkgComb_altBkgCombA',
        'bkgCombL_c1': 'bkgCombL_c1_altBkgCombA'}
plotterCfg['plots']['angular3D_finalAltBkgCombA'] = {
    # argAliasInDB copied from systCollection.func_altBkgCombA.setupFinalAltBkgCombAFitter['argAliasInDB']
    'func': [plotPostfitBLK],
    'kwargs': {
        'pltName': "angular3D_finalAltBkgCombA",
        'dataReader': "dataReader",
        'pdfPlots': [["f_finalAltBkgCombA", plotterCfg_styles['allStyleBase'], angular3D_finalAltBkgCombA_argAliasInDB, "Total fit"],
                     ["f_sig3D", plotterCfg_styles['sigStyleBase'], angular3D_finalAltBkgCombA_argAliasInDB, "Signal"],
                     ["f_bkgCombAltA", plotterCfg_styles['bkgStyleBase'], angular3D_finalAltBkgCombA_argAliasInDB, "Background"],
                    ],
    }
}
angular3D_finalAltBkgCombA2_argAliasInDB = {
        'unboundAfb': 'unboundAfb_altBkgCombA2', 
        'unboundFl': 'unboundFl_altBkgCombA2',
        'fs': 'fs_altBkgCombA2',
        'as': 'as_altBkgCombA2',
        'nSig': 'nSig_altBkgCombA2',
        'nBkgComb': 'nBkgComb_altBkgCombA2',
        "bkgCombM_c1": "bkgCombM_c1_altBkgCombA2",
        "bkgCombL_c1": "bkgCombL_c1_altBkgCombA2",
        "bkgCombL_c2": "bkgCombL_c2_altBkgCombA2",
        "bkgCombL_c3": "bkgCombL_c3_altBkgCombA2",
        "bkgCombL_c4": "bkgCombL_c4_altBkgCombA2",
        "bkgCombL_c5": "bkgCombL_c5_altBkgCombA2",
        "bkgCombK_c1": "bkgCombK_c1_altBkgCombA2",
        "bkgCombK_c2": "bkgCombK_c2_altBkgCombA2",
        "bkgCombK_c3": "bkgCombK_c3_altBkgCombA2",
        "bkgCombK_c4": "bkgCombK_c4_altBkgCombA2",
        "bkgCombK_c5": "bkgCombK_c5_altBkgCombA2"}
plotterCfg['plots']['angular3D_bkgCombAAltA2'] = {
    'func': [functools.partial(plotSimpleBLK, frames='LK')],
    'kwargs': {
        'pltName': "angular3D_bkgCombAAltA2",
        'dataPlots': [["dataReader.SB", plotterCfg_styles['dataStyle'], "Sideband data"], ],
        'pdfPlots': [["f_bkgCombA", plotterCfg_styles['bkgStyleAlt1'], angular3D_finalAltBkgCombA2_argAliasInDB, "Alternative Bkg."],
                     # ["f_bkgCombA", plotterCfg_styles['bkgStyle'], None, "Analytic Bkg."],
                    ],
        'marks': {}}
}
plotterCfg['plots']['angular3D_finalAltBkgCombA2'] = {
    # argAliasInDB copied from systCollection.func_altBkgCombA2.setupFinalAltBkgCombAFitter['argAliasInDB']
    'func': [plotPostfitBLK],
    'kwargs': {
        'pltName': "angular3D_finalAltBkgCombA2",
        'dataReader': "dataReader",
        'pdfPlots': [["f_final", plotterCfg_styles['allStyleBase'], angular3D_finalAltBkgCombA2_argAliasInDB, "Total fit"],
                     ["f_sig3D", plotterCfg_styles['sigStyleBase'], angular3D_finalAltBkgCombA2_argAliasInDB, "Signal"],
                     ["f_bkgComb", plotterCfg_styles['bkgStyleBase'], angular3D_finalAltBkgCombA2_argAliasInDB, "Background"],
                    ],
    }
}
angular3D_finalAltEffi3_argAliasInDB = {
        'unboundAfb': 'unboundAfb_altEffi3',
         'unboundFl': 'unboundFl_altEffi3',
         'fs': 'fs_altEffi3',
         'as': 'as_altEffi3',
         'nSig': 'nSig_altEffi3',
         'nBkgComb': 'nBkgComb_altEffi3',
         'bkgCombM_c1': 'bkgCombM_c1_altEffi3'}
for k, v in fitCollection.setupIterativeEffiFitter['argAliasInDB'].items():
    angular3D_finalAltEffi3_argAliasInDB[k] = v
plotterCfg['plots']['angular3D_finalAltEffi3'] = {
    'func': [plotPostfitBLK],
    'kwargs': {
        'pltName': "angular3D_finalAltEffi3",
        'dataReader': "dataReader",
        'pdfPlots': [
            ["f_final",   plotterCfg_styles['allStyleBase'], angular3D_finalAltEffi3_argAliasInDB, "Total fit"],
            ["f_sig3D",   plotterCfg_styles['sigStyleBase'], angular3D_finalAltEffi3_argAliasInDB, "Signal"],
            ["f_bkgComb", plotterCfg_styles['bkgStyleBase'], angular3D_finalAltEffi3_argAliasInDB, "Comb. Bkg."],
        ]
    }
}
# More tests
plotterCfg['plots']['plotOnX_Kstarmass'] = {
    'func': [plotOnXYZ],
    'kwargs': {
        'pltName': "plotOnX_Kstarmass",
        'dataName': "dataReader.Fit",
        'createHistogramArgs': (Kstarmass,
                                ROOT.RooFit.Binning(30, 0.742, 1.042),
                                ),
        'drawOpt': [""],
        'marks': {}}
}
plotterCfg['plots']['plotOnX_CosThetaK_USB'] = {
    'func': [plotOnXYZ],
    'kwargs': {
        'pltName': "plotOnX_CosThetaK_USB",
        'dataName': "dataReader.USB",
        'createHistogramArgs': (CosThetaK,
                                ROOT.RooFit.Binning(Plotter.frameK_binning),
                                ),
        'drawOpt': [""],
        'marks': {}}
}
plotterCfg['plots']['plotOnX_CosThetaL_USB'] = {
    'func': [plotOnXYZ],
    'kwargs': {
        'pltName': "plotOnX_CosThetaL_USB",
        'dataName': "dataReader.USB",
        'createHistogramArgs': (CosThetaL,
                                ROOT.RooFit.Binning(Plotter.frameL_binning),
                                ),
        'drawOpt': [""],
        'marks': {}}
}
plotterCfg['plots']['plotOnX_CosThetaK_LSB'] = {
    'func': [plotOnXYZ],
    'kwargs': {
        'pltName': "plotOnX_CosThetaK_LSB",
        'dataName': "dataReader.LSB",
        'createHistogramArgs': (CosThetaK,
                                ROOT.RooFit.Binning(Plotter.frameK_binning),
                                ),
        'drawOpt': [""],
        'marks': {}}
}
plotterCfg['plots']['plotOnX_CosThetaL_LSB'] = {
    'func': [plotOnXYZ],
    'kwargs': {
        'pltName': "plotOnX_CosThetaL_LSB",
        'dataName': "dataReader.LSB",
        'createHistogramArgs': (CosThetaL,
                                ROOT.RooFit.Binning(Plotter.frameL_binning),
                                ),
        'drawOpt': [""],
        'marks': {}}
}
plotterCfg['plots']['plotOnXY_Bmass_CosThetaK'] = {
    'func': [plotOnXYZ],
    'kwargs': {
        'pltName': "plotOnXY_Bmass_CosThetaK",
        'dataName': "sigMCReader.Fit",
        'createHistogramArgs': (Bmass,
                                ROOT.RooFit.Binning(20, 5.18, 5.38),
                                ROOT.RooFit.YVar(CosThetaK,
                                                 ROOT.RooFit.Binning(20, -1., 1.))
                                ),
        'drawOpt': ["VIOLIN", "COL TEXT", "LEGO2"],
        'marks': {'marks': ['sim']}}
}
plotterCfg['plots']['plotOnXY_Bmass_CosThetaL'] = {
    'func': [plotOnXYZ],
    'kwargs': {
        'pltName': "plotOnXY_Bmass_CosThetaL",
        'dataName': "sigMCReader.Fit",
        'createHistogramArgs': (Bmass,
                                ROOT.RooFit.Binning(20, 5.18, 5.38),
                                ROOT.RooFit.YVar(CosThetaL,
                                                 ROOT.RooFit.Binning(20, -1., 1.))
                                ),
        'drawOpt': ["VIOLIN", "COL TEXT", "LEGO2"],
        'marks': {'marks': ['sim']}}
}
plotterCfg['plots']['plotOnXY_CosThetaK_CosThetaL_bkgComb'] = {
    'func': [plotOnXYZ],
    'kwargs': {
        'pltName': "plotOnXY_CosThetaK_CosThetaL_bkgComb",
        'dataName': "dataReader.SB",
        'createHistogramArgs': (CosThetaK,
                                ROOT.RooFit.Binning(dataCollection.rAccXEffThetaKBins),
                                ROOT.RooFit.YVar(CosThetaL,
                                                 ROOT.RooFit.Binning(dataCollection.rAccXEffThetaLBins))
                                ),
        'drawOpt': ["VIOLIN", "COL TEXT", "LEGO2"],
        'marks': {}}
}
plotterCfg['plots']['iterativeEffi'] = {
    'func': [plotEfficiency],
    'kwargs': {
        'pltName': "iterativeEffi",
        'dataName': "effiHistReader.accXrec",
        'pdfName': "effi_sigA",
        'argAliasInDB': fitCollection.setupIterativeEffiFitter['argAliasInDB'],
    },
}
plotterCfg['plots']['angular3D_final_altFit0'] = {
    'func': [functools.partial(plotSimpleBLK, frames='BLK')],
    'kwargs': {
        'pltName': "angular3D_final_altFit0",
        'dataPlots': [["dataReader.Full", plotterCfg_styles['dataStyle'], "Data"], ],
        'pdfPlots': [["f_final", plotterCfg_styles['allStyle'], fitCollection.setupFinalFitter_altFit0['argAliasInDB'], "Total fit[4.68, 5.88]"],
                    ],
        'marks': {}}
}
plotterCfg['plots']['angular3D_final_altFit1'] = {
    'func': [functools.partial(plotSimpleBLK, frames='BLK')],
    'kwargs': {
        'pltName': "angular3D_final_altFit1",
        'dataPlots': [["dataReader.Full", plotterCfg_styles['dataStyle'], "Data"], ],
        'pdfPlots': [["f_final", plotterCfg_styles['allStyle'], fitCollection.setupFinalFitter_altFit1['argAliasInDB'], "Total fit[5.00, 5.64]"],
                    ],
        'marks': {}}
}
plotterCfg['plots']['angular3D_final_altFit2'] = {
    'func': [functools.partial(plotSimpleBLK, frames='BLK')],
    'kwargs': {
        'pltName': "angular3D_final_altFit2",
        'dataPlots': [["dataReader.altFit2", plotterCfg_styles['dataStyle'], "Data"],],
        'pdfPlots': [["f_final_altFit2", plotterCfg_styles['allStyleBase'] + (ROOT.RooFit.ProjectionRange("altFit2"), ROOT.RooFit.NormRange("altFit2"),), fitCollection.setupFinalFitter_altFit2['argAliasInDB'], "Total fit[4.98, 5.58]"],
                     ["f_final_altFit2", plotterCfg_styles['sigStyleBase'] + (ROOT.RooFit.ProjectionRange("altFit2"), ROOT.RooFit.NormRange("altFit2"), ROOT.RooFit.Components("f_sig3D"),), fitCollection.setupFinalFitter_altFit2['argAliasInDB'], "Signal"],
                     ["f_final_altFit2", plotterCfg_styles['bkgStyleBase'] + (ROOT.RooFit.ProjectionRange("altFit2"), ROOT.RooFit.NormRange("altFit2"), ROOT.RooFit.Components("f_bkgCombAAltA_altFit2"),), fitCollection.setupFinalFitter_altFit2['argAliasInDB'], "Smooth Bkg."],
                    ],
        'marks': {}}
}
plotterCfg['plots']['angular3D_bkgComb_altFit2'] = {
    'func': [functools.partial(plotSimpleBLK, frames='LK')],
    'kwargs': {
        'pltName': "angular3D_bkgComb_altFit2",
        'dataPlots': [["dataReader.Full", plotterCfg_styles['dataStyle'], "Data"], ],
        'pdfPlots': [["f_bkgCombAAltA_altFit2", plotterCfg_styles['bkgStyle'], None, "Smooth Bkg."],
                    ],
        'marks': {}}
}
plotterCfg['plots']['angular3D_final_altFit3'] = {
    'func': [functools.partial(plotSimpleBLK, frames='BLK')],
    'kwargs': {
        'pltName': "angular3D_final_altFit3",
        'dataPlots': [["dataReader.Fit", plotterCfg_styles['dataStyle'], "Data"],],
        'pdfPlots': [["f_final_altFit3", plotterCfg_styles['allStyle'],  fitCollection.setupFinalFitter_altFit3['argAliasInDB'], "Total fit"],
                     ["f_final_altFit3", plotterCfg_styles['sigStyle'] + (ROOT.RooFit.Components("f_sig3D"),), fitCollection.setupFinalFitter_altFit3['argAliasInDB'], "Signal"],
                     ["f_final_altFit3", plotterCfg_styles['bkgStyle'] + (ROOT.RooFit.Components("f_bkgCombAAltA_altFit3"),), fitCollection.setupFinalFitter_altFit3['argAliasInDB'], "Smooth Bkg."],
                    ],
        'marks': {}}
}
plotterCfg['plots']['test'] = { # TODO: Show two PDF with different parameter.
    'func': [functools.partial(plotSimpleBLK, frames='BLK')],
    'kwargs': {
        'pltName': "test",
        'dataPlots': [["dataReader.Full", plotterCfg_styles['dataStyle'], "Data"], ],
        'pdfPlots': [["f_final", plotterCfg_styles['allStyle'], None, "Total fit[4.76, 5.80]"],
                    ],
        'marks': {}}
}

plotter = Plotter(plotterCfg)

if __name__ == '__main__':
    defaultPlots = [
        'simpleSpectrum',
        'effi',
        'angular3D_sigM',
        'angular3D_bkgJpsiM',
        'angular3D_bkgPsi2sM',
        'angular3D_bkgCombA',
        'angular3D_bkgCombAAltA',
        'angular3D_final',
        'plotOnX_Kstarmass',
        'plotOnXY_Bmass_CosThetaK',
        'plotOnXY_Bmass_CosThetaL',
    ]

    parser = ArgumentParser(prog='plotCollection.py')
    parser.add_argument('-b', '--binKey', dest='binKey', type=str, default=p.cfg['binKey'])
    parser.add_argument('-p', '--plots', dest='switchPlots', type=str, nargs='+', default=defaultPlots, help="Switch plots from {0}.".format(" ".join(plotterCfg['plots'].keys())))
    args = parser.parse_args()

    if args.binKey in q2bins.keys():
        p.cfg['binKey'] = args.binKey
    else:
        raise KeyError("Unknown binKey. Pick from {0}".format(q2bins.keys()))

    for plt in args.switchPlots:
        if plt in plotterCfg['plots'].keys():
            if plt not in plotter.cfg['switchPlots']:
                plotter.cfg['switchPlots'].append(plt)
        else:
            raise KeyError("Unknown key {0} in plotterCfg, pick from {1}".format(plt, ' '.join(plotterCfg['plots'].keys())))

    p.setSequence([dataCollection.effiHistReader,
        dataCollection.sigMCReader,
        # dataCollection.bkgJpsiMCReader,
        # dataCollection.bkgPsi2sMCReader,
        dataCollection.dataReader,
        pdfCollection.stdWspaceReader,
        plotter])

    try:
        p.beginSeq()
        p.runSeq()
    finally:
        p.endSeq()
