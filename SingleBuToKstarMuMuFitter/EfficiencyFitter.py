#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

from v2Fitter.Fitter.FitterCore import FitterCore

import SingleBuToKstarMuMuFitter.cpp
from SingleBuToKstarMuMuFitter.anaSetup import q2bins
from SingleBuToKstarMuMuFitter.StdProcess import setStyle
from SingleBuToKstarMuMuFitter.varCollection import CosThetaL, CosThetaK
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer

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
        h_effi_2D_pull = ROOT.TH1F("h_effi_2D_pull", "", 30, -3, 3)
        fitter.SetPull(h_effi_2D_pull)
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
        h2_effi_2D_comp = fitter.GetRatio()
        h2_effi_2D_comp.SetMinimum(0)
        h2_effi_2D_comp.SetMaximum(1.5)
        h2_effi_2D_comp.SetTitleOffset(1.6, "X")
        h2_effi_2D_comp.SetTitleOffset(1.8, "Y")
        h2_effi_2D_comp.SetTitleOffset(1.5, "Z")
        h2_effi_2D_comp.SetZTitle("#varepsilon_{fit}/#varepsilon_{measured}")
        h2_effi_2D_comp.Draw("LEGO2")
        latex.DrawLatexNDC(.08, .93, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}")
        latex.DrawLatexNDC(.08, .88, "#chi^{{2}}/DoF={0:.2f}/{1}".format(fitter.GetChi2(), fitter.GetDoF()))
        canvas.Print("effi_2D_comp_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))

        # Plot pull between fitting result to data
        h_effi_2D_pull.SetXTitle("Pull")
        h_effi_2D_pull.SetYTitle("# of bins")
        h_effi_2D_pull.Draw()
        latex.DrawLatexNDC(.19, .89, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}")
        latex.DrawLatexNDC(.19, .84, "#chi^{{2}}/DoF={0:.2f}".format(fitter.GetChi2()/fitter.GetDoF()))
        canvas.Print("effi_2D_pull_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))


    @staticmethod
    def isPosiDef(formula2D):
        f2_min_x, f2_min_y = ROOT.Double(0), ROOT.Double(0)
        formula2D.GetMinimumXY(f2_min_x, f2_min_y)
        f2_min = formula2D.Eval(f2_min_x, f2_min_y)
        if f2_min > 0:
            return True
        else:
            print("WARNING\t: Sanitary check failed: Minimum of efficiency map is {0:.2e} at {1}, {2}".format(f2_min, f2_min_x, f2_min_y))
        return False
