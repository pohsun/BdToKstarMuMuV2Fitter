#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os

import ROOT
from SingleBuToKstarMuMuFitter.Plotter import Plotter
import SingleBuToKstarMuMuSelector.StdOptimizerBase as StdOptimizerBase

def create_histo(kwargs):
    ofname = kwargs.get('ofname', "plotFOMScan.root")
    iTreeFiles = kwargs.get('iTreeFiles', ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2/BuToKstarMuMu-data-2012*.root"])
    wgtString = kwargs.get('wgtString', "1")

    tree = ROOT.TChain("tree")
    for tr in iTreeFiles:
        tree.Add(tr)

    df = ROOT.RDataFrame(tree).Filter("nb>0", "At least one B candidate")
    aug_df = StdOptimizerBase.Define_AllCheckBits(df)\
        .Define("weight", wgtString)\
        .Define("PassAll"                     , "bit_resRej * bit_antiRad * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_trkpt"         , "bit_resRej * bit_antiRad * bit_HasGoodDimuon * 1         * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_trkdcabssig"   , "bit_resRej * bit_antiRad * bit_HasGoodDimuon * bit_trkpt * 1               * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_kspt"          , "bit_resRej * bit_antiRad * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * 1        * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_blsbssig"      , "bit_resRej * bit_antiRad * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * 1            * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_bcosalphabs2d" , "bit_resRej * bit_antiRad * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * 1                 * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_bvtxcl"        , "bit_resRej * bit_antiRad * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * 1          * bit_kstarmass")\
        .Define("PassAllExcept_kstarmass"     , "bit_resRej * bit_antiRad * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * 1")

    h_Trkpt = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_trkpt)")\
        .Define("BestCand_trkpt", "Define_GetValAtArgMax(trkpt, bvtxcl, PassAllExcept_trkpt)")\
        .Define("BestCand_trkptM", "Define_GetValAtArgMax(bmass, bvtxcl, PassAllExcept_trkpt)")\
        .Define("BestCand_trkptW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_trkpt)")\
        .Histo2D(("h_Trkpt", "", 50, 0, 5, 104, 4.76, 5.80), "BestCand_trkpt", "BestCand_trkptM", "BestCand_trkptW")

    h_Bvtxcl = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_bvtxcl)")\
        .Define("BestCand_bvtxcl", "Define_GetValAtArgMax(bvtxcl, bvtxcl, PassAllExcept_bvtxcl)")\
        .Define("BestCand_bvtxclM", "Define_GetValAtArgMax(bmass, bvtxcl, PassAllExcept_bvtxcl)")\
        .Define("BestCand_bvtxclW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_bvtxcl)")\
        .Histo2D(("h_Bvtxcl", "", 100, 0, 1, 104, 4.76, 5.80), "BestCand_bvtxcl", "BestCand_bvtxclM", "BestCand_bvtxclW")

    h_Blxysig = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_blsbssig)")\
        .Define("BestCand_blsbssig", "Define_GetValAtArgMax(blsbssig, bvtxcl, PassAllExcept_blsbssig)")\
        .Define("BestCand_blsbssigM", "Define_GetValAtArgMax(bmass, bvtxcl, PassAllExcept_blsbssig)")\
        .Define("BestCand_blsbssigW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_blsbssig)")\
        .Histo2D(("h_Blxysig", "", 100, 0, 100, 104, 4.76, 5.80), "BestCand_blsbssig", "BestCand_blsbssigM", "BestCand_blsbssigW")

    h_Bcosalphabs2d = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_bcosalphabs2d)")\
        .Define("BestCand_bcosalphabs2d", "Define_GetValAtArgMax(bcosalphabs2d, bvtxcl, PassAllExcept_bcosalphabs2d)")\
        .Define("BestCand_bcosalphabs2dM", "Define_GetValAtArgMax(bmass, bvtxcl, PassAllExcept_bcosalphabs2d)")\
        .Define("BestCand_bcosalphabs2dW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_bcosalphabs2d)")\
        .Histo2D(("h_Bcosalphabs2d", "", 70, 0.9993, 1, 104, 4.76, 5.80), "BestCand_bcosalphabs2d", "BestCand_bcosalphabs2dM", "BestCand_bcosalphabs2dW")

    h_Trkdcabssig = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_trkdcabssig)")\
        .Define("BestCand_trkdcabssig", "Define_GetValAtArgMax(trkdcabssig, bvtxcl, PassAllExcept_trkdcabssig)")\
        .Define("BestCand_trkdcabssigM", "Define_GetValAtArgMax(bmass, bvtxcl, PassAllExcept_trkdcabssig)")\
        .Define("BestCand_trkdcabssigW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_trkdcabssig)")\
        .Histo2D(("h_Trkdcabssig", "", 100, 0, 50, 104, 4.76, 5.80), "BestCand_trkdcabssig", "BestCand_trkdcabssigM", "BestCand_trkdcabssigW")

    h_Kshortpt = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_kspt)")\
        .Define("BestCand_kspt", "Define_GetValAtArgMax(kspt, bvtxcl, PassAllExcept_kspt)")\
        .Define("BestCand_ksptM", "Define_GetValAtArgMax(bmass, bvtxcl, PassAllExcept_kspt)")\
        .Define("BestCand_ksptW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_kspt)")\
        .Histo2D(("h_Kshortpt", "", 100, 0, 10, 104, 4.76, 5.80), "BestCand_kspt", "BestCand_ksptM", "BestCand_ksptW")
    
    hists = [h_Trkpt, h_Bvtxcl, h_Blxysig, h_Bcosalphabs2d, h_Trkdcabssig, h_Kshortpt]
    fout = ROOT.TFile(ofname, "RECREATE")
    for h in hists:
        h.Write()
    fout.Write()
    fout.Close()

def plot_histo():
    canvas = Plotter.canvas
    legend = Plotter.legend

    fin_data = ROOT.TFile("plotFOMScan_data.root")
    fin_mc = ROOT.TFile("plotFOMScan_sigMC.root")

    pConfig = {
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
            'isLogY': True,
        },
        'h_Kshortpt': {
            'label': "Kshortpt",
            'xTitle': "K_{S} p_{T} [GeV]",
            'yTitle': None,
        },
        'h_Trkpt': {
            'label': "Trkpt",
            'xTitle': "#pi p_{T}",
            'yTitle': None,
        },
        'h_Trkdcabssig': {
            'label': "Trkdcasigbs",
            'xTitle': "#pi DCA/#sigma",
            'yTitle': None,
        },
    }
    def drawPlot(pName):
        pCfg = pConfig[pName]
        h_data = fin_data.Get(pName)
        h_data.SetXTitle(pCfg['xTitle'])
        h_data.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of candidates")

        h_mc = fin_mc.Get(pName)
        h_mc.SetXTitle(pCfg['xTitle'])
        h_mc.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of candidates")
        h_mc.Scale(h_data.GetSumOfWeights() / h_mc.GetSumOfWeights())
        h_mc.SetLineColor(2)
        h_mc.SetFillColor(2)
        h_mc.SetFillStyle(3003)

        if pCfg.get('isLogY', False):
            canvas.SetLogy(1)
            h_mc.SetMaximum(70 * h_data.GetMaximum())
            h_mc.SetMinimum(1)
        else:
            canvas.SetLogy(0)
            h_mc.SetMaximum(1.8 * h_data.GetMaximum())
            h_mc.SetMinimum(0)
        h_mc.Draw("HIST")
        h_data.Draw("E SAME")

        legend.Clear()
        legend.AddEntry(h_data, "Data", "lep")
        legend.AddEntry(h_mc, "J/#psi K^{*+} MC", "F")
        legend.Draw()

        Plotter.latexDataMarks()
        return h_data, h_mc

    for p in pConfig.keys():
        h_data, h_mc = drawPlot(p)
        canvas.Print("fom_{0}.pdf".format(pConfig[p]['label']))

if __name__ == '__main__':
    if not os.path.exists("plotFOMScan_data.root"):
        # Remark: Takes ~2 minutes for data processing
        create_histo({
            'ofname': "plotFOMScan_data.root",
            'wgtString': "abs(BestCand_bmass-5.28) < 0.1",
        })
    if not os.path.exists("plotFOMScan_sigMC.root"):
        # Remark: Takes ~5 minutes for data processing
        create_histo({
            'ofname': "plotFOMScan_sigMC.root",
            'iTreeFiles': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2/BuToKstarJPsi_8TeV_*.root"],
            'wgtString': "(abs(BestCand_bmass-5.28) < 0.1)",
        })
    plot_histo()
