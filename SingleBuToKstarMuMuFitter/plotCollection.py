#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 26 Feb 2019 16:21 

import types
import shelve

import ROOT

from anaSetup import q2bins
from v2Fitter.Fitter.FitterCore import FitterCore
from v2Fitter.FlowControl.Path import Path
from varCollection import Bmass, CosThetaK, CosThetaL, Mumumass, Kstarmass

from ROOT import RooBinning

from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels

import dataCollection
import pdfCollection

class Plotter(Path):

    @classmethod
    def templateConfig(cls):
        cfg = Path.templateConfig()
        cfg.update({
            'db': "fitResults.db",
            'binKey': "test",
        })
        return cfg

    def _runPath(self):
        """Auto detect objects in sourcemanager"""
        db = shelve.open(self.cfg.get('db', "fitResults.db"))
        def initFromDB(iArg):
            argName = iArg.GetName()
            funcPair = [
                ('setVal', 'getVal'),
                ('setError', 'getError'),
                ('setAsymError', 'getErrorHi'),
                ('setAsymError', 'getErrorLo'),
                ('setConstant', 'isConstant'),
                ('setMax', 'getMax'),
                ('setMin', 'getMin')]
            if argName in db:
                for setter, getter in funcPair:
                    getattr(iArg, setter)(
                        *{
                            'getErrorHi': (db[argName]['getErrorLo'], db[argName][getter]),
                            'getErrorLo': (db[argName][getter], db[argName]['getErrorHi']),
                        }.get(getter, (db[argName][getter],))
                    )
            else:
                self.logger.logINFO("Found new variable {0}".format(argName))
        plots = [
            ("effi_sigA", "effiHistReader.accXrec"),
            ("f_sigM", "sigMCReader.Fit"),
            ("f_sig2D", "sigMCReader.Fit"),
            ("f_bkgCombA", "dataReader.SB"),
            ("f_final", "dataReader.Fit"),
        ]

        canvas = ROOT.TCanvas()
        for f, d in plots:
            if d in self.process.sourcemanager.keys() and f in self.process.sourcemanager.keys():
                data= self.process.sourcemanager.get(d)
                pdf = self.process.sourcemanager.get(f)
                args = pdf.getParameters(data)
                FitterCore.ArgLooper(args, initFromDB)
                if f == "effi_sigA":
                    # https://root.cern.ch/root/html/tutorials/roofit/rf702_efficiencyfit_2D.C.html
                    binningL = RooBinning(len(dataCollection.accXEffThetaLBins)-1, dataCollection.accXEffThetaLBins)
                    binningK = RooBinning(len(dataCollection.accXEffThetaKBins)-1, dataCollection.accXEffThetaKBins)
                    data.Draw("LEGO2")
                    h2_accXrec = data.createHistogram("h2_accXrec", CosThetaL, ROOT.RooFit.Binning(binningL), ROOT.RooFit.YVar(CosThetaK, ROOT.RooFit.Binning(binningK)))
                    h2_effi_sigA = pdf.createHistogram("h2_effi_sigA", CosThetaL, ROOT.RooFit.Binning(binningL), ROOT.RooFit.YVar(CosThetaK, ROOT.RooFit.Binning(binningK)))
                    h2_accXrec.Draw("LEGO2")
                    h2_effi_sigA.Draw("SURF SAME")
                    canvas.Update()
                    canvas.Print("h_effi_sigA.pdf")


                if f == "f_final":
                    # TODO: NLL plots for afb and fl, https://root.cern.ch/root/html/tutorials/roofit/rf606_nllerrorhandling.C.html
                    # https://root.cern.ch/root/html/tutorials/roofit/rf605_profilell.C.html
                    pass
        db.close()

plotter = Plotter({
    'name': "plotter",
})


def customize(binKey):
    plotter.cfg['db'] = "fitResults_{0}.db".format(binKey)
    plotter.cfg['binKey'] = binKey

if __name__ == '__main__':
    binKey = 'test'
    dataCollection.customize(binKey, ['SR', 'LSB', 'USB', 'test'])
    pdfCollection.customize(binKey)
    customize(binKey)
    p = Process("testFitCollection", "testProcess")
    p.logger.verbosityLevel = VerbosityLevels.DEBUG
    p.setSequence([dataCollection.effiHistReader, pdfCollection.stdWspaceReader, plotter])
    # p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sigMFitter])
    # p.setSequence([dataCollection.sigMCReader, pdfCollection.stdWspaceReader, sig2DFitter])
    # p.setSequence([dataCollection.dataReader, pdfCollection.stdWspaceReader, bkgCombAFitter])
    p.beginSeq()
    p.runSeq()
    p.endSeq()
