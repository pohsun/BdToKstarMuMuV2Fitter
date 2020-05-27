#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=0 fdn=2 ft=python et:

from v2Fitter.Fitter.FitterCore import FitterCore

import SingleBuToKstarMuMuFitter.cpp
from SingleBuToKstarMuMuFitter.anaSetup import q2bins
from SingleBuToKstarMuMuFitter.StdProcess import setStyle, isDEBUG
from SingleBuToKstarMuMuFitter.varCollection import CosThetaL, CosThetaK
from SingleBuToKstarMuMuFitter.FitDBPlayer import FitDBPlayer

import re
import itertools

import ROOT
setStyle()

class EfficiencyFitter(FitterCore):
    """Implementation to standard efficiency fitting procdeure to BuToKstarMuMu angular analysis"""
    canvas = ROOT.TCanvas()
    latex = ROOT.TLatex()

    @classmethod
    def templateConfig(cls):
        cfg = FitterCore.templateConfig()
        cfg.update({
            'name': "EfficiencyFitter",
            'data': "effiHistReader.accXrec",
            'hdata': "effiHistReader.h2_accXrec",
            'dataX': "effiHistReader.h_accXrec_fine_ProjectionX",
            'dataY': "effiHistReader.h_accXrec_fine_ProjectionY",
            'pdf': "effi_sigA",
            'pdfX': "effi_cosl",
            'pdfY': "effi_cosK",
            'saveToDB': True,
            'argAliasInDB': None,
            'noDraw': False,
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
        drawPreFitPlots = True if isDEBUG else False

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

            # Draw runtime 1-D comparison
            if drawPreFitPlots:
                self.canvas.cd()
                frame = var.frame()
                hdata.plotOn(frame)
                pdf.plotOn(frame)
                frame.Draw()
                self.canvas.Update()
                self.canvas.Print("DEBUG_EfficiencyFitter_preFitSteps_{0}.pdf".format(var.GetName()))

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
        if self.cfg['saveToDB']:
            FitDBPlayer.UpdateToDB(self.process.dbplayer.odbfile, args, self.cfg.get('argAliasInDB'))

    def _runFitSteps(self):
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
        h2_accXrec = self.process.sourcemanager.get(self.cfg.get('hdata'))
        h2_accXrec.SetXTitle(CosThetaL.GetTitle())
        h2_accXrec.SetYTitle(CosThetaK.GetTitle())
        minuit = fitter.Init(nPar, h2_accXrec, f2_effi_sigA)
        h_effi_pull = ROOT.TH1F("h_effi_pull", "", 30, -3, 3)
        fitter.SetPull(h_effi_pull)
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

        # Plot comparison between fitting result to data
        if not self.cfg.get('noDraw', False):
            self.canvas.cd()
            h2_effi_2D_comp = fitter.GetRatio()
            h2_effi_2D_comp.SetXTitle(CosThetaL.GetTitle())
            h2_effi_2D_comp.SetYTitle(CosThetaK.GetTitle())
            h2_effi_2D_comp.SetZTitle("#varepsilon_{fit}/#varepsilon_{measured}")
            h2_effi_2D_comp.SetMinimum(0)
            h2_effi_2D_comp.SetMaximum(1.5)
            h2_effi_2D_comp.SetTitleOffset(1.3, "X")
            h2_effi_2D_comp.SetTitleOffset(1.5, "Y")
            h2_effi_2D_comp.SetTitleOffset(1.5, "Z")
            h2_effi_2D_comp.Draw("LEGO2")
            self.latex.DrawLatexNDC(.16, .94, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}")
            self.latex.DrawLatexNDC(.16, .84, "#chi^{{2}}/DoF={0:.2f}/{1}".format(fitter.GetChi2(), fitter.GetDoF()))
            self.canvas.Print("effi_2D_comp_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))

            # Plot numerator and denominator for the ratio plot
            compTEXTScale = 1e6
            h2_accXrec.Scale(compTEXTScale)  # Efficiency is so low, unable to compare without scale up
            h2_accXrec.Draw("COL")
            h2_accXrec.SetBarOffset(-0.1)
            h2_accXrec.Draw("TEXT SAME")
            h2_effi_2D_compText = h2_accXrec.Clone("h2_effi_2D_compText")
            h2_effi_2D_compText.Reset("ICES")
            for i, j in itertools.product(range(1, h2_effi_2D_compText.GetNbinsX()+1), range(1, h2_effi_2D_compText.GetNbinsY()+1)):
                xi = h2_effi_2D_compText.GetXaxis().GetBinLowEdge(i)
                xf = h2_effi_2D_compText.GetXaxis().GetBinUpEdge(i)
                yi = h2_effi_2D_compText.GetYaxis().GetBinLowEdge(j)
                yf = h2_effi_2D_compText.GetYaxis().GetBinUpEdge(j)
                h2_effi_2D_compText.SetBinContent(i, j, compTEXTScale* f2_effi_sigA.Integral(xi,xf,yi,yf)/(xf-xi)/(yf-yi))
            h2_effi_2D_compText.SetMarkerColor(2)
            h2_effi_2D_compText.SetBarOffset(0.1)
            h2_effi_2D_compText.Draw("TEXT SAME")
            self.latex.DrawLatexNDC(.16, .94, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}")
            self.canvas.Print("effi_2D_compTEXT_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))
            h2_accXrec.Scale(1. / compTEXTScale)

            # Plot pull between fitting result to data
            h2_effi_2D_pull = fitter.GetPull2D()
            h2_effi_2D_pull.SetXTitle(CosThetaL.GetTitle())
            h2_effi_2D_pull.SetYTitle(CosThetaK.GetTitle())
            h2_effi_2D_pull.SetZTitle("Pull")
            h2_effi_2D_pull.SetMinimum(-3.)
            h2_effi_2D_pull.SetMaximum(3.)
            h2_effi_2D_pull.SetFillColor(42)
            h2_effi_2D_pull.Draw("BOX1 TEXT")
            self.latex.DrawLatexNDC(.16, .94, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}")
            self.latex.DrawLatexNDC(.16, .84, "#chi^{{2}}/DoF={0:.2f}".format(fitter.GetChi2()/fitter.GetDoF()))
            self.canvas.Print("effi_2D_pull_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))

            h_effi_pull.Fit("gaus", "", "", -2., 2.)
            h_effi_pull.SetXTitle("Pull")
            h_effi_pull.SetYTitle("# of bins")
            h_effi_pull.Draw("")
            self.latex.DrawLatexNDC(.16, .94, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}")
            self.latex.DrawLatexNDC(.16, .84, "#chi^{{2}}/DoF={0:.2f}".format(fitter.GetChi2()/fitter.GetDoF()))
            self.canvas.Print("effi_pull_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))
            
            # Plot comparison between efficiency map w/ and w/o cross term.
            compXTermScale = 1e6
            h2_accXrec.Scale(compXTermScale)  # Efficiency is so low, unable to compare without scale up
            h2_accXrec.Draw("COL")
            h2_accXrec.SetBarOffset(-0.1)
            h2_accXrec.Draw("TEXT SAME")
            args.find('hasXTerm').setVal(0)
            h2_effi_2D_compXTerm = h2_accXrec.Clone("h2_effi_2D_compXTerm")
            h2_effi_2D_compXTerm.Reset("ICES")
            self.pdf.fillHistogram(h2_effi_2D_compXTerm, ROOT.RooArgList(CosThetaL, CosThetaK))
            h2_effi_2D_compXTerm.Scale(h2_accXrec.GetSumOfWeights()/h2_effi_2D_compXTerm.GetSumOfWeights())
            h2_effi_2D_compXTerm.SetMarkerColor(2)
            h2_effi_2D_compXTerm.SetBarOffset(0.1)
            h2_effi_2D_compXTerm.Draw("TEXT SAME")
            self.latex.DrawLatexNDC(.16, .94, "#font[61]{CMS} #font[52]{#scale[0.8]{Simulation}}")
            self.canvas.Print("effi_2D_compXTerm_{0}.pdf".format(q2bins[self.process.cfg['binKey']]['label']))
            args.find('hasXTerm').setVal(1)
            h2_accXrec.Scale(1. / compXTermScale)
        
        # Check if efficiency is positive definite
        f2_max_x, f2_max_y = ROOT.Double(0), ROOT.Double(0)
        f2_min_x, f2_min_y = ROOT.Double(0), ROOT.Double(0)
        f2_effi_sigA.GetMaximumXY(f2_max_x, f2_max_y)
        f2_effi_sigA.GetMinimumXY(f2_min_x, f2_min_y)
        self.logger.logINFO("Sanitary check: Efficiency ranges from {0:.2e} to {1:.2e}".format(f2_effi_sigA.Eval(f2_min_x, f2_min_y), f2_effi_sigA.Eval(f2_max_x, f2_max_y)))

        # Check if correction term is small
        if not self.process.sourcemanager.get("effi_xTerm") is None:
            effi_xTerm_formula = self.process.sourcemanager.get("effi_xTerm").formula().GetExpFormula().Data()
            effi_xTerm_formula = re.sub(r"x(\d{1,2})", r"[\1]", effi_xTerm_formula)
            effi_xTerm_formula = re.sub(r"CosThetaL", r"x", effi_xTerm_formula)
            effi_xTerm_formula = re.sub(r"CosThetaK", r"y", effi_xTerm_formula)
            effi_xTerm_formula = re.sub(r"hasXTerm", r"(1)", effi_xTerm_formula)

            f2_effi_xTerm = ROOT.TF2("f2_effi_xTerm", effi_xTerm_formula, -1, 1, -1, 1)
            for xIdx in range(nPar):
                minuit.GetParameter(xIdx, parVal, parErr)
                f2_effi_xTerm.SetParameter(xIdx, parVal)
                f2_effi_xTerm.SetParError(xIdx, parErr)
            f2_effi_xTerm.GetMaximumXY(f2_max_x, f2_max_y)
            f2_effi_xTerm.GetMinimumXY(f2_min_x, f2_min_y)
            self.logger.logDEBUG("Efficiency xTerm formula: {0}".format(effi_xTerm_formula))
            self.logger.logINFO("Sanitary check: xTerm ranges from {0:.2e} to {1:.2e}".format(f2_effi_xTerm.Eval(f2_min_x, f2_min_y), f2_effi_xTerm.Eval(f2_max_x, f2_max_y)))

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
