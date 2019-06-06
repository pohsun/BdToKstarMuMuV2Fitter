#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 sts=4 fdm=indent fdl=0 fdn=3 ft=python et:

import types
import functools
import shelve
from array import array

import ROOT

import SingleBuToKstarMuMuFitter.cpp
from v2Fitter.FlowControl.Path import Path
from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.StdFitter import unboundFlToFl, unboundAfbToAfb
from SingleBuToKstarMuMuFitter.anaSetup import q2bins, modulePath, bMassRegions

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

    def canvasPrint(self, name):
        Plotter.canvas.Update()
        Plotter.canvas.Print("{0}_{1}.pdf".format(name, q2bins[self.process.cfg['binKey']]['label']))

    latex = ROOT.TLatex()
    latexCMSMark = staticmethod(lambda x=0.19, y=0.89: Plotter.latex.DrawLatexNDC(x, y, "#font[61]{CMS}"))
    latexCMSSim = staticmethod(lambda x=0.19, y=0.89: Plotter.latex.DrawLatexNDC(x, y, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}"))
    latexCMSToy = staticmethod(lambda x=0.19, y=0.89: Plotter.latex.DrawLatexNDC(x, y, "#font[61]{CMS} #font[52]{#scale[0.8]{Post-fit Toy}}"))
    latexCMSMix = staticmethod(lambda x=0.19, y=0.89: Plotter.latex.DrawLatexNDC(x, y, "#font[61]{CMS} #font[52]{#scale[0.8]{Toy + Simu.}}"))
    latexCMSExtra = staticmethod(lambda x=0.19, y=0.85: Plotter.latex.DrawLatexNDC(x, y, "#font[52]{#scale[0.8]{Preliminary}}") if True else None)
    latexLumi = staticmethod(lambda x=0.78, y=0.96: Plotter.latex.DrawLatexNDC(x, y, "#scale[0.8]{19.98 fb^{-1} (8 TeV)}"))

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

    def initPdfPlotCfg(self, p):
        pdfPlotTemplate = ["", plotterCfg_allStyle, None]
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
        dataPlotTemplate = ["", plotterCfg_dataStyle]
        p = p + dataPlotTemplate[len(p):]
        if isinstance(p[0], str):
            self.logger.logDEBUG("Initialize dataPlot {0}".format(p[0]))
            p[0] = self.process.sourcemanager.get(p[0])
            if p[0] == None:
                self.logger.logERROR("dataPlot not found in source manager.")
                raise RuntimeError
        return p

    @staticmethod
    def plotFrame(frame, binning, dataPlots=None, pdfPlots=None, marks=None, scaleYaxis=1.5):
        """
            Use initXXXPlotCfg to ensure elements in xxxPlots fit the format
        """
        cloned_frame = frame.emptyClone("cloned_frame")
        marks = [] if marks is None else marks
        dataPlots = [] if dataPlots is None else dataPlots
        pdfPlots = [] if pdfPlots is None else pdfPlots
        for p in dataPlots:
            p[0].plotOn(cloned_frame, ROOT.RooFit.Binning(binning), *p[1])
        for p in pdfPlots:
            p[0].plotOn(cloned_frame, *p[1])
        cloned_frame.SetMaximum(scaleYaxis * cloned_frame.GetMaximum())
        cloned_frame.Draw()
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
        [wspace.pdf('model'), plotterCfg_allStyle],
        [wspace.pdf('model'), (ROOT.RooFit.Components('sigM'),) + plotterCfg_sigStyle],
        [wspace.pdf('model'), (ROOT.RooFit.Components('bkgCombM'),) + plotterCfg_bkgStyle],
    ]

    pdfPlots[0][0].fitTo(dataPlots[0][0], ROOT.RooFit.Minos(True), ROOT.RooFit.Extended(True))
    Plotter.plotFrameB(dataPlots=dataPlots, pdfPlots=pdfPlots, marks=marks)
    self.canvasPrint(pltName)

def plotSimpleBLK(self, pltName, dataPlots, pdfPlots, marks, frames='BLK'):
    for pIdx, plt in enumerate(dataPlots):
        dataPlots[pIdx] = self.initDataPlotCfg(plt)
    for pIdx, plt in enumerate(pdfPlots):
        pdfPlots[pIdx] = self.initPdfPlotCfg(plt)

    plotFuncs = {
        'B': {'func': Plotter.plotFrameB_fine, 'tag': ""},
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
    FitDBPlayer.initFromDB(self.process.dbplayer.odbfile, args)

    binningL = ROOT.RooBinning(len(dataCollection.accXEffThetaLBins) - 1, dataCollection.accXEffThetaLBins)
    binningK = ROOT.RooBinning(len(dataCollection.accXEffThetaKBins) - 1, dataCollection.accXEffThetaKBins)

    # TODO: Some optimization for 2D plot
    data_accXrec = self.process.sourcemanager.get("effiHistReader.h2_accXrec")
    h2_effi_sigA_fine = pdf.createHistogram("h2_effi_sigA_fine", CosThetaL, ROOT.RooFit.Binning(20), ROOT.RooFit.YVar(CosThetaK, ROOT.RooFit.Binning(20)))
    data_accXrec.SetMinimum(0)
    data_accXrec.SetMaximum(0.00015)
    data_accXrec.SetZTitle("Overall efficiency")
    data_accXrec.Draw("LEGO2")
    h2_effi_sigA_fine.SetLineColor(2)
    h2_effi_sigA_fine.Draw("SURF SAME")
    Plotter.latexCMSSim()
    Plotter.latexCMSExtra()
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
    try:
        inputdb = shelve.open(self.process.dbplayer.odbfile)
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
        dataPlots = [[self.process.sourcemanager.get("{0}.{1}".format(dataReader, regionName)), plotterCfg_dataStyle], ]

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

# TODO
def plotSummaryAfbFl(self, pltName, dbSetup):
    """ 'dbSetup': [["name", "/path/fitResults_{0}.db", drawSystError, drawOpt, argAliasInDB],] """
    binKeys = ['belowJpsi', 'betweenPeaks', 'abovePsi2s']

    xx = array('d', [sum(q2bins[binKey]['q2range']) / 2 for binKey in binKeys])
    xxErr = array('d', map(lambda t: (t[1]-t[0])/2, [q2bins[binKey]['q2range'] for binKey in binKeys]))

    grs = []
    for name, pat, drawSystError, drawOpt, argAliasInDB in dbSetup:
        yy = array('d')
        yyErrHi = array('d')
        yyErrLo = array('d')
        yySyst = array('d')
        for binKey in binKeys:
            try:
                  db = shelve.open(pat.format(binLabel=q2bins[binKey]['label']))
                  unboundAfb = db[argAliasInDB.get("unboundAfb", "unboundAfb")]
                  unboundFl = db[argAliasInDB.get("unboundFl", "unboundFl")]
            finally:
                  db.close()
            pass
        gr = ROOT.TGraphAsymmErrors(name, "", xx, xxErr, xxErr, yy, yyErrLo, yyErrLo)
        grs.append(gr)

    for gr in grs:
        pass
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
            'dataPlots': [["sigMCReader.Fit", plotterCfg_mcStyle], ],
            'pdfPlots': [["f_sigM", plotterCfg_sigStyle, fitCollection.setupSigMFitter['argAliasInDB']],
                        ],
            'marks': ['sim']}
    },
    'angular3D_sig2D': {
        'func': [functools.partial(plotSimpleBLK, frames='LK')],
        'kwargs': {
            'pltName': "angular3D_sig2D",
            'dataPlots': [["sigMCReader.Fit", plotterCfg_mcStyle], ],
            'pdfPlots': [["f_sig2D", plotterCfg_sigStyle, fitCollection.setupSig2DFitter['argAliasInDB']],
                        ],
            'marks': []}
    },
    'angular3D_bkgCombA': {
        'func': [functools.partial(plotSimpleBLK, frames='LK')],
        'kwargs': {
            'pltName': "angular3D_bkgCombA",
            'dataPlots': [["dataReader.SB", plotterCfg_dataStyle], ],
            'pdfPlots': [["f_bkgCombA", plotterCfg_bkgStyle],
                         #  ["f_bkgCombAltA", (ROOT.RooFit.LineColor(4), ROOT.RooFit.LineStyle(9))]
                        ],
            'marks': []}
    },
    'simpleBLK': {  # Most general case, to be customized by user
        'func': [functools.partial(plotSimpleBLK, frames='BLK')],
        'kwargs': {
            'pltName': "simpleBLK",
            'dataPlots': [["ToyGenerator.mixedToy", plotterCfg_mcStyle], ],
            'pdfPlots': [["f_sigM", plotterCfg_sigStyle],
                        ],
            'marks': ['sim']}
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
    'angular3D_summary': {
        'func': [plotSummaryAfbFl],
        'kwargs': {
            'pltName': "angular3D_final",
            'pdfPlots': [["f_final", plotterCfg_allStyle],
                         ["f_sig3D", plotterCfg_sigStyle],
                         ["f_bkgComb", plotterCfg_bkgStyle],
                        ],
            }
    }
}
#  plotterCfg['switchPlots'].append('simpleSpectrum')
#  plotterCfg['switchPlots'].append('effi')
#  plotterCfg['switchPlots'].append('angular3D_sigM')
#  plotterCfg['switchPlots'].append('angular3D_bkgCombA')
#  plotterCfg['switchPlots'].append('angular3D_final')

plotter = Plotter(plotterCfg)

if __name__ == '__main__':
    #  p.cfg['binKey'] = "abovePsi2s"
    #  plotter.cfg['switchPlots'].append('simpleSpectrum')
    plotter.cfg['switchPlots'].append('effi')
    plotter.cfg['switchPlots'].append('angular3D_sigM')
    plotter.cfg['switchPlots'].append('angular3D_bkgCombA')
    plotter.cfg['switchPlots'].append('angular3D_final')
    p.setSequence([dataCollection.effiHistReader, dataCollection.sigMCReader, dataCollection.dataReader, pdfCollection.stdWspaceReader, plotter])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
