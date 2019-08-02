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
    tree.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/DATA/*.root")

    #  treeFriend = ROOT.TChain("tree")
    #  treeFriend.Add("./plotMatchCandPreSelector.root")
    #  treeFriend.BuildIndex("Bmass", "Mumumass")
    #  tree.AddFriend(treeFriend)

    fout = ROOT.TFile("h2_MumumassVsBmass.root", "RECREATE")
    h2_MumumassVsBmass_presel = ROOT.TH2F("h2_MumumassVsBmass_presel", "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1])
    h2_MumumassVsBmass_resRej = ROOT.TH2F("h2_MumumassVsBmass_resRej", "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1])
    h2_MumumassVsBmass_antiRad = ROOT.TH2F("h2_MumumassVsBmass_antiRad", "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1])
    h2_MumumassVsBmass_resVeto = ROOT.TH2F("h2_MumumassVsBmass_resVeto", "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1])

    tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_presel", "({0})*({1})".format(anaSetup.cut_passTrigger,
                                                                                  anaSetup.cut_kshortWindow,
                                                                                  anaSetup.cut_kstarMassWindow))
    tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_resRej", "({0})*({1})*({2})".format(anaSetup.cut_passTrigger,
                                                                                        anaSetup.cut_kshortWindow,
                                                                                        anaSetup.cut_kstarMassWindow,
                                                                                        anaSetup.cut_resonanceRej))
    tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_antiRad", "({0})*({1})*({2})".format(anaSetup.cut_passTrigger,
                                                                                         anaSetup.cut_kshortWindow,
                                                                                         anaSetup.cut_kstarMassWindow,
                                                                                         anaSetup.cut_antiRadiation))
    tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_resVeto", "({0})*({1})*({2})*({3})".format(anaSetup.cut_passTrigger,
                                                                                               anaSetup.cut_kshortWindow,
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

        transparencyPeak = 1.0
        transparencySR = 0.3
        highlight_jpsi = ROOT.TBox(math.sqrt(jpsi_range[0]), b_range[0], math.sqrt(jpsi_range[1]), b_range[1])
        highlight_jpsi.SetFillColorAlpha(ROOT.kRed, transparencyPeak)
        highlight_jpsi.Draw()
        highlight_psi2s = ROOT.TBox(math.sqrt(psi2s_range[0]), b_range[0], math.sqrt(psi2s_range[1]), b_range[1])
        highlight_psi2s.SetFillColorAlpha(ROOT.kRed, transparencyPeak)
        highlight_psi2s.Draw()
        highlight_SR = ROOT.TBox(1, anaSetup.bMassRegions['SR']['range'][0], 5, anaSetup.bMassRegions['SR']['range'][1])
        highlight_SR.SetFillColorAlpha(ROOT.kRed, transparencySR)
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
        latex.DrawLatexNDC(.20, .80, "Yields_{{Non-peaking}}={0:.0f}".format(nEvtInSR))
        latex.DrawLatexNDC(.20, .74, "Yields_{{peaking}}={0:.1e}".format(nEvtInPeaks))

        plotCollection.Plotter.latexCMSMark()
        plotCollection.Plotter.latexCMSExtra()
        plotCollection.Plotter.latexLumi()
        canvas.Update()
        canvas.Print("{0}.pdf".format(hname))

        h_projX = h.ProjectionX(hname.replace("h2", "h").replace("MumumassVsBmass", "Mumumass"), 22, 32)  # [5.18, 5.38] out of [4.76, 5.80]
        h_projX.SetYTitle("Number of events")
        if h_projX.GetSumOfWeights() > 10000:
            h_projX.Rebin(5)

        h_projX.GetXaxis().SetRangeUser(2.5, 3.5)
        h_projX.Draw("E")
        plotCollection.Plotter.latexCMSMark()
        plotCollection.Plotter.latexCMSExtra()
        plotCollection.Plotter.latexLumi()
        canvas.Update()
        canvas.Print("{0}_jpsi.pdf".format(h_projX.GetName()))
        h_projX.GetXaxis().SetRangeUser(3.3, 4.1)
        h_projX.Draw("E")
        plotCollection.Plotter.latexCMSMark()
        plotCollection.Plotter.latexCMSExtra()
        plotCollection.Plotter.latexLumi()
        canvas.Update()
        canvas.Print("{0}_psi2s.pdf".format(h_projX.GetName()))

        h_projY = h.ProjectionY(hname.replace("h2", "h").replace("MumumassVsBmass", "Bmass"))
        h_projY.SetYTitle("Number of events")
        h_projY.Draw("E")
        plotCollection.Plotter.latexCMSMark()
        plotCollection.Plotter.latexCMSExtra()
        plotCollection.Plotter.latexLumi()
        canvas.Update()
        canvas.Print("{0}.pdf".format(h_projY.GetName()))

    for hname in ["h2_MumumassVsBmass_presel", "h2_MumumassVsBmass_resRej", "h2_MumumassVsBmass_antiRad", "h2_MumumassVsBmass_resVeto"]:
        _plot(hname)

if __name__ == '__main__':
    if not os.path.exists("h2_MumumassVsBmass.root"):
        create_histo()
    plot_histo()
