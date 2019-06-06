#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os
import math
import itertools
import ROOT
import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
from SingleBuToKstarMuMuFitter.StdProcess import setStyle
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection
import SingleBuToKstarMuMuFitter.varCollection as varCollection


b_range = anaSetup.bMassRegions['Fit']['range']
jpsi_range = anaSetup.q2bins['jpsi']['q2range']
psi2s_range = anaSetup.q2bins['psi2s']['q2range']

def create_histo():
    tree = ROOT.TChain("tree")
    #  tree.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/DATA/*.root")
    tree.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/SIG/*.root")

    fout = ROOT.TFile("h2_MumumassVsBmass.root", "RECREATE")
    h2_MumumassVsBmass_presel = ROOT.TH2F("h2_MumumassVsBmass_presel", "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1])
    h2_MumumassVsBmass_resRej = ROOT.TH2F("h2_MumumassVsBmass_resRej", "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1])
    h2_MumumassVsBmass_antiRad = ROOT.TH2F("h2_MumumassVsBmass_antiRad", "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1])
    h2_MumumassVsBmass_resVeto = ROOT.TH2F("h2_MumumassVsBmass_resVeto", "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1])

    tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_presel", "({0})*({1})".format(anaSetup.cut_passTrigger,
                                                                                  anaSetup.cut_kstarMassWindow))
    tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_resRej", "({0})*({1})*({2})".format(anaSetup.cut_passTrigger,
                                                                                        anaSetup.cut_kstarMassWindow,
                                                                                        anaSetup.cut_resonanceRej))
    tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_antiRad", "({0})*({1})*({2})".format(anaSetup.cut_passTrigger,
                                                                                         anaSetup.cut_kstarMassWindow,
                                                                                         anaSetup.cut_antiRadiation))
    tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_resVeto", "({0})*({1})*({2})*({3})".format(anaSetup.cut_passTrigger,
                                                                                               anaSetup.cut_kstarMassWindow,
                                                                                               anaSetup.cut_resonanceRej,
                                                                                               anaSetup.cut_antiRadiation))
    fout.Write()
    fout.Close()


def plot_histo(fname="h2_MumumassVsBmass.root"):
    setStyle()
    canvas = ROOT.TCanvas()

    fin = ROOT.TFile(fname)

    def _plot(hname):
        h = fin.Get(hname)
        h.SetMarkerSize(0.2)
        h.SetXTitle(varCollection.Mumumass.getTitle().Data())
        h.SetYTitle(varCollection.Bmass.getTitle().Data())
        h.Draw()

        highlight_jpsi = ROOT.TBox(math.sqrt(jpsi_range[0]), b_range[0], math.sqrt(jpsi_range[1]), b_range[1])
        highlight_jpsi.SetFillColorAlpha(ROOT.kRed, 0.3)
        highlight_jpsi.Draw()
        highlight_psi2s = ROOT.TBox(math.sqrt(psi2s_range[0]), b_range[0], math.sqrt(psi2s_range[1]), b_range[1])
        highlight_psi2s.SetFillColorAlpha(ROOT.kRed, 0.3)
        highlight_psi2s.Draw()
        highlight_SR = ROOT.TBox(1, anaSetup.bMassRegions['SR']['range'][0], 5, anaSetup.bMassRegions['SR']['range'][1])
        highlight_SR.SetFillColorAlpha(ROOT.kRed, 0.3)
        highlight_SR.Draw()

        nEvtInSR = 0
        nEvtInPeaks = 0
        for xbin, ybin in itertools.product([l + 1 for l in range(h.GetNbinsX())], [l + 1 for l in range(h.GetNbinsY())]):
            xCenter = h.GetXaxis().GetBinCenter(xbin)
            yCenter = h.GetYaxis().GetBinCenter(ybin)
            if anaSetup.bMassRegions['SR']['range'][1] > yCenter > anaSetup.bMassRegions['SR']['range'][0]\
                    and 19 > xCenter**2 > 1:
                if anaSetup.q2bins['psi2s']['q2range'][1] > xCenter**2 > anaSetup.q2bins['psi2s']['q2range'][0]\
                        or anaSetup.q2bins['jpsi']['q2range'][1] > xCenter**2 > anaSetup.q2bins['jpsi']['q2range'][0]:
                    nEvtInPeaks = nEvtInPeaks + h.GetBinContent(xbin, ybin)
                else:
                    nEvtInSR = nEvtInSR + h.GetBinContent(xbin, ybin)


        latex = ROOT.TLatex()
        latex.DrawLatexNDC(.15, .85, "Yields_{{Non-peaking}}={0}".format(nEvtInSR))
        latex.DrawLatexNDC(.15, .78, "Yields_{{peaking}}={0:.2e}".format(nEvtInPeaks))

        plotCollection.Plotter.latexCMSMark()
        plotCollection.Plotter.latexLumi()
        canvas.Update()
        canvas.Print("{0}.pdf".format(hname))

        h_projX = h.ProjectionX(hname.replace("h2", "h").replace("MumumassVsBmass", "Mumumass"))
        if h_projX.GetSumOfWeights() < 10000:
            h_projX.Rebin(5)
        h_projX.Draw("HIST")
        plotCollection.Plotter.latexCMSMark()
        plotCollection.Plotter.latexLumi()
        canvas.Update()
        canvas.Print("{0}.pdf".format(h_projX.GetName()))

        h_projY = h.ProjectionY(hname.replace("h2", "h").replace("MumumassVsBmass", "Bmass"))
        h_projY.Draw("HIST")
        plotCollection.Plotter.latexCMSMark()
        plotCollection.Plotter.latexLumi()
        canvas.Update()
        canvas.Print("{0}.pdf".format(h_projY.GetName()))

    for hname in ["h2_MumumassVsBmass_presel", "h2_MumumassVsBmass_resRej", "h2_MumumassVsBmass_antiRad", "h2_MumumassVsBmass_resVeto"]:
        _plot(hname)

if __name__ == '__main__':
    if not os.path.exists("h2_MumumassVsBmass.root"):
        create_histo()
    plot_histo()
