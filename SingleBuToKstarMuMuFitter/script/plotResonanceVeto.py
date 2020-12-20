#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os
import math
import itertools
import ROOT
import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
from SingleBuToKstarMuMuFitter.StdProcess import setStyle
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection
import SingleBuToKstarMuMuFitter.varCollection as varCollection


b_range = anaSetup.bMassRegions['Fit']['range']
jpsi_range = anaSetup.q2bins['jpsi']['q2range']
psi2s_range = anaSetup.q2bins['psi2s']['q2range']

def create_histo():
    tree = ROOT.TChain("tree")
    for f in dataCollection.dataReaderCfg['ifile']:
        tree.Add(f)

    #  treeFriend = ROOT.TChain("tree")
    #  treeFriend.Add("./plotMatchCandPreSelector.root")
    #  treeFriend.BuildIndex("Bmass", "Mumumass")
    #  tree.AddFriend(treeFriend)

    fout = ROOT.TFile("h2_MumumassVsBmass.root", "RECREATE")
    h2_MumumassVsBmass_presel  = [] 
    h2_MumumassVsBmass_resRej  = []
    h_varAntiRad_jpsi_resRej = []
    h_varAntiRad_psi2s_resRej = []
    h2_MumumassVsBmass_antiRad = []
    h2_MumumassVsBmass_resVeto = []


    for q2r in ['full', 'summary', 'peaks']:
        q2rCut = anaSetup.q2bins[q2r]['cutString']

        h2_MumumassVsBmass_presel.append(ROOT.TH2F("h2_MumumassVsBmass_{0}_presel".format(q2r), "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1]))
        h2_MumumassVsBmass_resRej.append(ROOT.TH2F("h2_MumumassVsBmass_{0}_resRej".format(q2r), "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1]))
        h2_MumumassVsBmass_antiRad.append(ROOT.TH2F("h2_MumumassVsBmass_{0}_antiRad".format(q2r), "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1]))
        h2_MumumassVsBmass_resVeto.append(ROOT.TH2F("h2_MumumassVsBmass_{0}_resVeto".format(q2r), "", 200, 1, 5, int((b_range[1] - b_range[0]) / 0.02), b_range[0], b_range[1]))
        h_varAntiRad_jpsi_resRej.append(ROOT.TH1F("h_varAntiRad_{0}_resRej".format(q2r), "", 100, -2 + 2.182, 2 + 2.182))

        tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_{0}_presel".format(q2r), "({0})*({1})*({2})".format(q2rCut,
                                                                                      anaSetup.cut_passTrigger,
                                                                                      #  anaSetup.cut_kshortWindow,
                                                                                      anaSetup.cut_kstarMassWindow))
        tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_{0}_resRej".format(q2r), "({0})*({1})*({2})*({3})".format(q2rCut,
                                                                                            anaSetup.cut_passTrigger,
                                                                                            #  anaSetup.cut_kshortWindow,
                                                                                            anaSetup.cut_kstarMassWindow,
                                                                                            anaSetup.cut_resonanceRej))
        tree.Draw("Bmass-Mumumass >> h_varAntiRad_{0}_resRej".format(q2r), "({0})*({1})*({2})*({3})*({4})".format(q2rCut,
                                                                                                   anaSetup.cut_passTrigger,
                                                                                                   "Bmass > 5.0 && Bmass < 5.3",
                                                                                                   #  anaSetup.cut_kshortWindow,
                                                                                                   anaSetup.cut_kstarMassWindow,
                                                                                                   anaSetup.cut_resonanceRej))
        tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_{0}_antiRad".format(q2r), "({0})*({1})*({2})*({3})".format(q2rCut,
                                                                                             anaSetup.cut_passTrigger,
                                                                                             #  anaSetup.cut_kshortWindow,
                                                                                             anaSetup.cut_kstarMassWindow,
                                                                                             anaSetup.cut_antiRadiation))
        tree.Draw("Bmass:Mumumass >> h2_MumumassVsBmass_{0}_resVeto".format(q2r), "({0})*({1})*({2})*({3})*({4})".format(q2rCut,
                                                                                                   anaSetup.cut_passTrigger,
                                                                                                   #  anaSetup.cut_kshortWindow,
                                                                                                   anaSetup.cut_kstarMassWindow,
                                                                                                   anaSetup.cut_resonanceRej,
                                                                                                   anaSetup.cut_antiRadiation))
    fout.Write()
    fout.Close()

def plot_histo(fname="h2_MumumassVsBmass.root"):
    setStyle()
    canvas = ROOT.TCanvas()

    fin = ROOT.TFile(fname)

    def plotH2(hname, q2r):
        h = fin.Get(hname)
        h.UseCurrentStyle()
        h.SetMarkerSize(0.2)
        h.SetXTitle(varCollection.Mumumass.GetTitle())
        h.SetYTitle(varCollection.Bmass.GetTitle())
        h.Draw()

        transparencyPeak = 0.3 if q2r in ['full', 'peaks'] else 0.  # Binning is irrelavent
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
        #  latex.DrawLatexNDC(.20, .80, "Yields_{{Non-peaking}}={0:.0f}".format(nEvtInSR))
        #  latex.DrawLatexNDC(.20, .74, "Yields_{{peaking}}={0:.1e}".format(nEvtInPeaks))

        plotCollection.Plotter.latexDataMarks(extraArgs={'y': 0.86})
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
        plotCollection.Plotter.latexDataMarks(extraArgs={'y': 0.86})
        canvas.Update()
        canvas.Print("{0}_psi2s.pdf".format(h_projX.GetName()))

        h_projY = h.ProjectionY(hname.replace("h2", "h").replace("MumumassVsBmass", "Bmass"))
        h_projY.SetYTitle("Number of events")
        h_projY.Draw("E")
        plotCollection.Plotter.latexDataMarks(extraArgs={'y': 0.86})
        canvas.Update()
        canvas.Print("{0}.pdf".format(h_projY.GetName()))

    def plotH1(hname, q2r):
        h = fin.Get(hname)
        h.UseCurrentStyle()
        h.SetMarkerSize(0.2)
        h.SetXTitle("m_{B} - m_{ll} [GeV]")
        h.SetMaximum(1.3 * h.GetMaximum())
        h.SetYTitle("Events / 0.04 GeV")
        h.Draw()

        transparencyPeak = 0.3
        highlight_jpsi = ROOT.TBox(2.182-0.09, 0, 2.182+0.09, h.GetMaximum())
        highlight_jpsi.SetFillColorAlpha(ROOT.kRed, transparencyPeak)
        highlight_jpsi.Draw()
        highlight_psi2s = ROOT.TBox(1.593-0.03, 0, 1.593+0.03, h.GetMaximum())
        highlight_psi2s.SetFillColorAlpha(ROOT.kRed, transparencyPeak)
        highlight_psi2s.Draw()

        plotCollection.Plotter.latexDataMarks(extraArgs={'y': 0.86})
        canvas.Update()
        canvas.Print("{0}.pdf".format(hname))

    for hname in ["h2_MumumassVsBmass_{0}_presel", "h2_MumumassVsBmass_{0}_resRej", "h2_MumumassVsBmass_{0}_antiRad", "h2_MumumassVsBmass_{0}_resVeto"]:
        for q2r in ['full', 'peaks', 'summary']:
            plotH2(hname.format(q2r), q2r)

    for q2r in ['full', 'peaks', 'summary']:
        plotH1("h_varAntiRad_{0}_resRej".format(q2r), q2r)

if __name__ == '__main__':
    if not os.path.exists("h2_MumumassVsBmass.root"):
        create_histo()
    plot_histo()
