#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

from v2Fitter.Fitter.FitterCore import FitterCore

import SingleBuToKstarMuMuFitter.cpp
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer
from SingleBuToKstarMuMuFitter.anaSetup import q2bins
from SingleBuToKstarMuMuFitter.varCollection import CosThetaL, CosThetaK
from SingleBuToKstarMuMuFitter.plotCollection import setStyle

import re
import itertools

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
            'pdf': "effi_sigA",
            'pdfX': "effi_cosl",
            'pdfY': "effi_cosK",
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
        FitDBPlayer.initFromDB(self.process.dbplayer.odbfile, args)
        self.ToggleConstVar(args, isConst=True)

        # Disable xTerm correction and fit to 1-D
        args.find('hasXTerm').setVal(0)

        h_accXrec_fine_ProjectionX = self.process.sourcemanager.get(self.cfg['dataX'])
        h_accXrec_fine_ProjectionY = self.process.sourcemanager.get(self.cfg['dataY'])
        effi_cosl = self.process.sourcemanager.get(self.cfg['pdfX'])
        effi_cosK = self.process.sourcemanager.get(self.cfg['pdfY'])
        for proj, pdf, var, argPats in [(h_accXrec_fine_ProjectionX, effi_cosl, CosThetaL, [r"^l\d+$"]), (h_accXrec_fine_ProjectionY, effi_cosK, CosThetaK, [r"^k\d+$"])]:
            hdata = ROOT.RooDataHist("hdata", "", ROOT.RooArgList(var), ROOT.RooFit.Import(proj))
            self.ToggleConstVar(args, isConst=False, targetArgs=argPats)
            pdf.chi2FitTo(hdata, ROOT.RooLinkedList())
            self.ToggleConstVar(args, isConst=True, targetArgs=argPats)

        args.find('effi_norm').setConstant(False)
        self.pdf.chi2FitTo(self.data, ROOT.RooFit.Minos(True))
        args.find('effi_norm').setVal(args.find('effi_norm').getVal() / 4.)
        args.find('effi_norm').setConstant(True)

        # Fix uncorrelated term and for later update with xTerms in main fit step
        args.find('hasXTerm').setVal(1)
        self.ToggleConstVar(args, isConst=False, targetArgs=[r"^x\d+$"])

    def _postFitSteps(self):
        """Post-processing"""
        args = self.pdf.getParameters(self.data)
        self.ToggleConstVar(args, True)
        FitDBPlayer.UpdateToDB(self.process.dbplayer.odbfile, args)

    def _runFitSteps(self):
        h2_accXrec = self.process.sourcemanager.get("effiHistReader.h2_accXrec")

        effi_sigA_formula = self.pdf.formula().GetExpFormula().Data()
        args = self.pdf.getParameters(self.data)
        args_it = args.createIterator()
        arg = args_it.Next()
        nPar = 0
        while arg:
            if any(re.match(pat, arg.GetName()) for pat in ["effi_norm", "hasXTerm", r"^l\d+$", r"^k\d+$"]):
                effi_sigA_formula = re.sub(arg.GetName(), "({0})".format(arg.getVal()), effi_sigA_formula)
            elif re.match(r"^x\d+$", arg.GetName()):
                nPar = nPar + 1
            arg = args_it.Next()
        effi_sigA_formula = re.sub(r"x(\d{1,2})", r"[\1]", effi_sigA_formula)
        effi_sigA_formula = re.sub(r"CosThetaL", r"x", effi_sigA_formula)
        effi_sigA_formula = re.sub(r"CosThetaK", r"y", effi_sigA_formula)
        f2_effi_sigA = ROOT.TF2("f2_effi_sigA", effi_sigA_formula, -1, 1, -1, 1)

        fitter = ROOT.EfficiencyFitter()
        minuit = fitter.Init(nPar, h2_accXrec, f2_effi_sigA)
        for xIdx in range(nPar):
            minuit.DefineParameter(xIdx, "x{0}".format(xIdx), 0., 1E-4, -1E+1, 1E+1)
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

        # Check if efficiency is positive definite
        f2_max_x, f2_max_y = ROOT.Double(0), ROOT.Double(0)
        f2_min_x, f2_min_y = ROOT.Double(0), ROOT.Double(0)
        f2_effi_sigA.GetMaximumXY(f2_max_x, f2_max_y)
        f2_effi_sigA.GetMinimumXY(f2_min_x, f2_min_y)
        self.logger.logINFO("Sanitary check: Efficiency ranges from {0:.2e} to {1:.2e}".format(f2_effi_sigA.Eval(f2_min_x, f2_min_y), f2_effi_sigA.Eval(f2_max_x, f2_max_y)))

        # Plot comparison between fitting result to data
        setStyle()
        canvas = ROOT.TCanvas()
        latex = ROOT.TLatex()
        h2_effi_sigA_comp = h2_accXrec.Clone("h2_effi_sigA_comp")
        h2_effi_sigA_comp.Reset("ICESM")
        for lBin, KBin in itertools.product(list(range(1, h2_effi_sigA_comp.GetNbinsX() + 1)), list(range(1, h2_effi_sigA_comp.GetNbinsY() + 1))):
            h2_effi_sigA_comp.SetBinContent(lBin, KBin, f2_effi_sigA.Eval(h2_accXrec.GetXaxis().GetBinCenter(lBin), h2_accXrec.GetYaxis().GetBinCenter(KBin)) / h2_accXrec.GetBinContent(lBin, KBin))
        h2_effi_sigA_comp.SetMinimum(0)
        h2_effi_sigA_comp.SetMaximum(1.5)
        h2_effi_sigA_comp.SetZTitle("#varepsilon_{fit}/#varepsilon_{measured}")
        h2_effi_sigA_comp.Draw("LEGO2")
        latex.DrawLatexNDC(.05, .9, "CMS Simulation")
        latex.DrawLatexNDC(.85, .9, "#chi^{{2}}={0:.2f}".format(fitter.GetChi2()))
        canvas.Print("h2_effi_sigA_comp_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))
