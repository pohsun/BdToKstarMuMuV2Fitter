#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os

import ROOT
import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection


b_range = anaSetup.bMassRegions['Fit']['range']
jpsi_range = anaSetup.q2bins['jpsi']['q2range']
psi2s_range = anaSetup.q2bins['psi2s']['q2range']

def create_histo(kwargs):
    ofname = kwargs.get('ofname', "plotDataMCValidation.root")
    iTreeFiles = kwargs.get('iTreeFiles', ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/DATA/*.root"])
    cutString = kwargs.get('cutString', anaSetup.cuts_noResVeto)
    wgtString = "2*((fabs(Bmass-5.28)<0.1)-0.5)*(fabs(Bmass-5.28)<0.2)"  # +1/-1 for SR/sideband

    tree = ROOT.TChain("tree")
    for tr in iTreeFiles:
        tree.Add(tr)

    fout = ROOT.TFile(ofname, "RECREATE")
    h_Bpt = ROOT.TH1F("h_Bpt", "", 100, 0, 100)
    h_Bphi = ROOT.TH1F("h_Bphi", "", 63, -3.15, 3.15)
    h_Bvtxcl = ROOT.TH1F("h_Bvtxcl", "", 100, 0, 1)
    h_Blxysig = ROOT.TH1F("h_Blxysig", "", 100, 0, 100)
    h_Bcosalphabs2d = ROOT.TH1F("h_Bcosalphabs2d", "", 70, 0.9993, 1)
    h_Kshortpt = ROOT.TH1F("h_Kshortpt", "", 100, 0, 10)
    h_CosThetaL = ROOT.TH1F("h_CosThetaL", "", 100, -1, 1)
    h_Trkpt = ROOT.TH1F("h_Trkpt", "", 50, 0, 5)
    h_Trkdcasigbs = ROOT.TH1F("h_Trkdcasigbs", "", 100, 0, 50)

    tree.Draw("Bpt>>h_Bpt", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("Bphi>>h_Bphi", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("Bvtxcl>>h_Bvtxcl", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("Blxysig>>h_Blxysig", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("Bcosalphabs2d>>h_Bcosalphabs2d", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("Kshortpt>>h_Kshortpt", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("CosThetaL>>h_CosThetaL", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("CosThetaK>>h_CosThetaK", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("Trkpt>>h_Trkpt", "({0})&&({1})".format(cutString, wgtString), "goff")
    tree.Draw("Trkdcasigbs>>h_Trkdcasigbs", "({0})&&({1})".format(cutString, wgtString), "goff")
    fout.Write()
    fout.Close()

def plot_histo():
    canvas = plotCollection.Plotter.canvas
    legend = plotCollection.Plotter.legend

    fin_data = ROOT.TFile("plotDataMCValidation_data.root")
    fin_mc = ROOT.TFile("plotDataMCValidation_jpsi.root")

    pConfig = {
        'h_Bpt': {
            'label': "Bpt",
            'xTitle': "B^{+} p_{T} [GeV]",
            'yTitle': None,
        },
        'h_Bphi': {
            'label': "Bphi",
            'xTitle': "B^{+} #phi",
            'yTitle': None,
        },
        'h_Bvtxcl': {
            'label': "Bvtxcl",
            'xTitle': "B^{+} vtx. CL",
            'yTitle': None,
        },
        'h_Blxysig': {
            'label': "Blxysig",
            'xTitle': "B^{+} L_{xy}/#sigma",
            'yTitle': None,
        },
        'h_Bcosalphabs2d': {
            'label': "Bcosalphabs2d",
            'xTitle': "cos#alpha_{xy}^{B^{+}}",
            'yTitle': None,
        },
        'h_Kshortpt': {
            'label': "Kshortpt",
            'xTitle': "K_{S} p_{T} [GeV]",
            'yTitle': None,
        },
        'h_CosThetaK': {
            'label': "CosThetaK",
            'xTitle': "cos#theta_{K}",
            'yTitle': None,
        },
        'h_CosThetaL': {
            'label': "CosThetaL",
            'xTitle': "cos#theta_{l}",
            'yTitle': None,
        },
        'h_Trkpt': {
            'label': "Trkpt",
            'xTitle': "#pi p_{T}",
            'yTitle': None,
        },
        'h_Trkdcasigbs': {
            'label': "Trkdcasigbs",
            'xTitle': "#pi DCA/#sigma",
            'yTitle': None,
        },
    }
    def drawPlot(pName):
        pCfg = pConfig[pName]
        h_data = fin_data.Get(pName)
        h_data.SetXTitle(pCfg['xTitle'])
        h_data.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of events")

        h_mc = fin_mc.Get(pName)
        h_mc.SetXTitle(pCfg['xTitle'])
        h_mc.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of events")
        h_mc.Scale(h_data.GetSumOfWeights() / h_mc.GetSumOfWeights())
        h_mc.SetLineColor(2)
        h_mc.SetFillColor(2)
        h_mc.SetFillStyle(3001)

        h_mc.SetMaximum(1.8 * h_data.GetMaximum())
        h_mc.SetMinimum(0)
        h_mc.Draw("HIST")
        h_data.Draw("E SAME")

        legend.Clear()
        legend.AddEntry(h_data, "Data", "lep")
        legend.AddEntry(h_mc, "J/#psi K^{*+} MC", "F")
        legend.Draw()

        plotCollection.Plotter.latexDataMarks()
        return h_data, h_mc

    for p in pConfig.keys():
        h_data, h_mc = drawPlot(p)
        canvas.Print("val_dataMC_jpsi_{0}.pdf".format(pConfig[p]['label']))

if __name__ == '__main__':
    if not os.path.exists("plotDataMCValidation_data.root"):
        create_histo({
            'ofname': "plotDataMCValidation_data.root"
        })
    if not os.path.exists("plotDataMCValidation_jpsi.root"):
        create_histo({
            'ofname': "plotDataMCValidation_jpsi.root",
            'iTreeFiles': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/JPSI/*.root"]
        })
    plot_histo()
