#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

from v2Fitter.Fitter.FitterCore import FitterCore
from FitDBPlayer import FitDBPlayer
from anaSetup import q2bins
from varCollection import CosThetaL, CosThetaK
from plotCollection import setStyle

import os
import re
import shutil
import shelve
import functools
import itertools
from array import array

import ROOT

class EfficiencyFitter(FitterCore):
    """Implementation to standard efficiency fitting procdeure to BuToKstarMuMu angular analysis"""

    @classmethod
    def templateConfig(cls):
        cfg = FitterCore.templateConfig()
        cfg.update({
            'name': "EfficiencyFitter",
            'data': "effiHistReader.accXrec",
            'dataX': "effiHistReader.h_accXrec_fine_ProjectionX",
            'dataY': "effiHistReader.h_accXrec_fine_ProjectionY",
            'pdf' : "effi_sigA",
            'pdfX' : "effi_cosl",
            'pdfY' : "effi_cosK",
            'db'  : "fitResults.db",
            'updateArgs': True,
        })
        del cfg['createNLLOpt']
        return cfg

    def _bookMinimizer(self):
        """Pass complicate fitting control."""
        pass

    def _preFitSteps(self):
        """Prefit uncorrelated term"""
        args = self.pdf.getParameters(self.data)
        FitDBPlayer.initFromDB(self.cfg.get('db', FitDBPlayer.outputfilename), args)
        self.ToggleConstVar(args, isConst=True)

        # Disable xTerm correction and fit to 1-D
        args.find('hasXTerm').setVal(0)
        self.ToggleConstVar(args, isConst=False, targetArgs=[r"^k\d+$"])
        self.ToggleConstVar(args, isConst=False, targetArgs=[r"^l\d+$"])
        
        h_accXrec_fine_ProjectionX = self.process.sourcemanager.get(self.cfg['dataX'])
        h_accXrec_fine_ProjectionY = self.process.sourcemanager.get(self.cfg['dataY'])
        effi_cosl = self.process.sourcemanager.get(self.cfg['pdfX'])
        effi_cosK = self.process.sourcemanager.get(self.cfg['pdfY'])
        for proj, pdf, var in [(h_accXrec_fine_ProjectionX, effi_cosl, CosThetaL), (h_accXrec_fine_ProjectionY, effi_cosK, CosThetaK)]:
            hdata = ROOT.RooDataHist("hdata", "", ROOT.RooArgList(var), ROOT.RooFit.Import(proj))
            pdf.chi2FitTo(hdata, ROOT.RooLinkedList())

        self.ToggleConstVar(args, isConst=True, targetArgs=[r"^l\d+$"])
        self.ToggleConstVar(args, isConst=True, targetArgs=[r"^k\d+$"])
        args.find('effi_norm').setConstant(False)
        self.pdf.chi2FitTo(self.data, ROOT.RooFit.Minos(True))

        # Fix uncorrelated term and for later update with xTerms in main fit step
        args.find('hasXTerm').setVal(1)
        self.ToggleConstVar(args, isConst=False, targetArgs=[r"^x\d+$"])
        args.find('effi_norm').setConstant(True)

    def _postFitSteps(self):
        """Post-processing"""
        args = self.pdf.getParameters(self.data)
        self.ToggleConstVar(args, True)
        if self.cfg['updateArgs']:
            ofilename = "{0}_{1}.db".format(os.path.splitext(FitDBPlayer.outputfilename)[0], q2bins[self.process.cfg['binKey']]['label'])
            if not os.path.exists(ofilename) and self.process.cfg.has_key("db"):
                shutil.copy(self.process.cfg["db"], ofilename)
            FitDBPlayer.UpdateToDB(ofilename, args)

    def _runFitSteps(self):
        h2_accXrec = self.process.sourcemanager.get("effiHistReader.h2_accXrec")

        effi_sigA_formula = self.pdf.formula().GetExpFormula().Data()
        args = self.pdf.getParameters(self.data)
        args_it = args.createIterator()
        arg = args_it.Next()
        nPar = 0
        while arg:
            if any(re.match(pat, arg.GetName()) for pat in ["effi_norm", "hasXTerm", "^l\d+$", "^k\d+$"]):
                effi_sigA_formula = re.sub(arg.GetName(), "({0})".format(arg.getVal()), effi_sigA_formula)
            elif re.match("^x\d+$", arg.GetName()):
                nPar = nPar+1
            arg = args_it.Next()
        effi_sigA_formula = re.sub(r"x(\d{1,2})", r"[\1]", effi_sigA_formula)
        effi_sigA_formula = re.sub(r"CosThetaL", r"x", effi_sigA_formula)
        effi_sigA_formula = re.sub(r"CosThetaK", r"y", effi_sigA_formula)
        f2_effi_sigA = ROOT.TF2("f2_effi_sigA", effi_sigA_formula, -1, 1, -1, 1)

        if os.path.exists(os.path.abspath(os.path.dirname(__file__))+"/cpp/EfficiencyFitter_cc.so"):
            ROOT.gROOT.ProcessLine(".L "+os.path.abspath(os.path.dirname(__file__))+"/cpp/EfficiencyFitter_cc.so")
        else:
            ROOT.gROOT.ProcessLine(".L "+os.path.abspath(os.path.dirname(__file__))+"/cpp/EfficiencyFitter.cc+")
        fitter = ROOT.EfficiencyFitter()
        minuit = fitter.Init(nPar, h2_accXrec, f2_effi_sigA)
        for xIdx in range(nPar):
            minuit.DefineParameter(xIdx, "x{0}".format(xIdx), 0.,  1E-4,    -1E+1, 1E+1)
        minuit.Command("MINI")
        minuit.Command("MINI")
        minuit.Command("MINOS")

        parVal = ROOT.Double(0)
        parErr = ROOT.Double(0)
        for xIdx in range(nPar):
            minuit.GetParameter(xIdx, parVal, parErr)
            arg = args.find("x{0}".format(xIdx))
            arg.setVal(parVal)
            arg.setError(parErr)

        setStyle()
        canvas = ROOT.TCanvas()
        latex = ROOT.TLatex()
        h2_effi_sigA_comp = h2_accXrec.Clone("h2_effi_sigA_comp")
        h2_effi_sigA_comp.Reset("ICESM")
        for lBin, KBin in itertools.product(list(range(1, h2_effi_sigA_comp.GetNbinsX()+1)), list(range(1, h2_effi_sigA_comp.GetNbinsY()+1))):
            h2_effi_sigA_comp.SetBinContent(lBin, KBin, f2_effi_sigA.Eval(h2_accXrec.GetXaxis().GetBinCenter(lBin), h2_accXrec.GetYaxis().GetBinCenter(KBin))/h2_accXrec.GetBinContent(lBin, KBin))
        h2_effi_sigA_comp.SetMinimum(0)
        h2_effi_sigA_comp.SetMaximum(1.5)
        h2_effi_sigA_comp.SetZTitle("#varepsilon_{fit}/#varepsilon_{measured}")
        h2_effi_sigA_comp.Draw("LEGO2")
        latex.DrawLatexNDC(.05, .9, "CMS Simulation")
        latex.DrawLatexNDC(.85, .9, "#chi^{{2}}={0:.2f}".format(fitter.GetChi2()))
        canvas.Print("h2_effi_sigA_comp_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))


