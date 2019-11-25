#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os
import itertools

import ROOT
import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
import SingleBuToKstarMuMuFitter.varCollection as varCollection
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection
import SingleBuToKstarMuMuFitter.FitDBPlayer as FitDBPlayer


#  wgtString = "2*((fabs(Bmass-5.28)<0.1)-0.5)*(fabs(Bmass-5.28)<0.2)"  # +1/-1 for SR/sideband
wgtString = "1*(fabs(Bmass-5.28)<0.06) - 0.5*(fabs(Bmass-5.11)<0.06) - 0.5*(fabs(Bmass-5.46)<0.06)"  # +1/-1 for SR/sideband
def create_histo_data(kwargs):
    iTreeFiles = kwargs.get('iTreeFiles', ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/ANv21/DATA/*.root"])
    cutString = "({0}) && ({1})".format(anaSetup.cuts_antiResVeto, anaSetup.q2bins['jpsi']['cutString'])

    tree = ROOT.TChain("tree")
    for tr in iTreeFiles:
        tree.Add(tr)

    fout = ROOT.TFile("plotEffiClosure_data.root", "RECREATE")
    hists = []
    hists.append(ROOT.TH1F("h_CosThetaL", "CosThetaL", 20, -1, 1))
    hists.append(ROOT.TH1F("h_CosThetaK", "CosThetaK", 20, -1, 1))

    for hist in hists:
        varName = hist.GetTitle()
        histName = hist.GetName()
        tree.Draw("{var}>>{hist}".format(var=varName, hist=histName), "({cut})&&({wgt})".format(cut=cutString, wgt=wgtString), "goff")
    fout.Write()
    fout.Close()

def create_histo_expc(kwargs):
    iTreeFiles = kwargs.get('iTreeFiles', ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/unfilteredJPSI_genonly/*.root"])
    iDBFile = kwargs.get('db', anaSetup.modulePath + "/testProcess/fitResults_bin2.db")

    tree = ROOT.TChain("tree")
    for tr in iTreeFiles:
        tree.Add(tr)

    fout = ROOT.TFile("plotEffiClosure_expc.root", "RECREATE")
    h2_sigA_gen_fine = ROOT.TH2F("h2_sigA_gen_fine", "genCosThetaK:genCosThetaL", 20, -1, 1, 20, -1, 1)  # Y:X
    h2_sigA_expc_fine = h2_sigA_gen_fine.Clone("h2_sigA_expc_fine")
    tree.Draw("genCosThetaK:genCosThetaL>>h2_sigA_gen_fine", "genQ2 > 8.68 && genQ2 < 10.09", wgtString)

    effiFile = ROOT.TFile(anaSetup.modulePath + "/input/wspace_bin2.root")
    effiWspace = effiFile.Get("wspace.bin2")
    effi_sigA = effiWspace.function("effi_sigA")
    FitDBPlayer.FitDBPlayer.initFromDB(iDBFile, effi_sigA.getParameters(ROOT.RooArgSet(varCollection.CosThetaK, varCollection.CosThetaL)))
    h2_effi_sigA_fine = effi_sigA.createHistogram("h2_effi_sigA_fine", varCollection.CosThetaL, ROOT.RooFit.Binning(20), ROOT.RooFit.YVar(varCollection.CosThetaK, ROOT.RooFit.Binning(20)))

    for xBin, yBin in itertools.product(range(1, h2_sigA_gen_fine.GetNbinsX() + 1), range(1, h2_sigA_gen_fine.GetNbinsY() + 1)):
        iBin = h2_sigA_expc_fine.GetBin(xBin, yBin)
        h2_sigA_expc_fine.SetBinContent(iBin, h2_sigA_gen_fine.GetBinContent(iBin) * h2_effi_sigA_fine.GetBinContent(iBin))
    h_CosThetaL = h2_sigA_expc_fine.ProjectionX("h_CosThetaL")
    h_CosThetaK = h2_sigA_expc_fine.ProjectionY("h_CosThetaK")

    fout.cd()
    h2_sigA_gen_fine.Write()
    h2_effi_sigA_fine.Write()
    h2_sigA_expc_fine.Write()
    h_CosThetaL.Write()
    h_CosThetaK.Write()
    fout.Close()

def plot_histo():
    canvas = plotCollection.Plotter.canvas
    legend = plotCollection.Plotter.legend

    fin_data = ROOT.TFile("plotEffiClosure_data.root")
    fin_expc = ROOT.TFile("plotEffiClosure_expc.root")

    pConfig = {
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
    }
    def drawPlot(pName):
        pCfg = pConfig[pName]
        h_data = fin_data.Get(pName)
        h_data.SetXTitle(pCfg['xTitle'])
        h_data.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of events")

        h_expc = fin_expc.Get(pName)
        h_expc.SetXTitle(pCfg['xTitle'])
        h_expc.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of events")
        h_expc.Scale(h_data.GetSumOfWeights() / h_expc.GetSumOfWeights())  # Scale to data yields
        h_expc.SetLineColor(2)
        h_expc.SetFillColor(2)
        h_expc.SetFillStyle(3001)

        h_expc.SetMaximum(1.8 * h_data.GetMaximum())
        h_expc.SetMinimum(0)
        h_expc.Draw("HIST")
        h_data.Draw("E SAME")

        legend.Clear()
        legend.AddEntry(h_data, "Data", "lep")
        legend.AddEntry(h_expc, "J/#psi K^{*+} MC", "F")
        legend.Draw()

        plotCollection.Plotter.latexDataMarks()
        return h_data, h_expc

    for p in pConfig.keys():
        h_data, h_mc = drawPlot(p)
        canvas.Print("val_effiClosure_jpsi_{0}.pdf".format(pConfig[p]['label']))

if __name__ == '__main__':
    if not os.path.exists("plotEffiClosure_data.root"):
        create_histo_data({})
    if not os.path.exists("plotEffiClosure_expc.root"):
        create_histo_expc({})
    plot_histo()
