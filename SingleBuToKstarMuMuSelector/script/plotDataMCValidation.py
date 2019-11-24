#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os

import ROOT
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection
import SingleBuToKstarMuMuSelector.StdOptimizerBase as StdOptimizerBase

def create_histo(kwargs):
    ofname = kwargs.get('ofname', "plotDataMCValidation.root")
    iTreeFiles = kwargs.get('iTreeFiles', ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2/BuToKstarMuMu-data-2012*.root"])
    wgtString = kwargs.get('wgtString', "(abs(bmass-5.28)<0.06) - 0.5*(abs(bmass-5.11)<0.06) - 0.5*(abs(bmass-5.46)<0.06)")

    tree = ROOT.TChain("tree")
    for tr in iTreeFiles:
        tree.Add(tr)

    df = ROOT.RDataFrame(tree).Filter("nb>0", "At least one B candidate")
    aug_df = StdOptimizerBase.Define_AllCheckBits(df)\
        .Define("weight", wgtString)\
        .Define("PassAll", "(1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_trkpt", "(1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * 1 * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_trkdcabssig", "(1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * 1 * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_kspt", "(1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * 1 * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_blsbssig", "(1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * 1 * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_bcosalphabs2d", "(1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * 1 * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_bvtxcl", "(1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * 1 * bit_kstarmass")\
        .Define("PassAllExcept_kstarmass", "(1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * 1")

    h_Trkpt = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_trkpt)")\
        .Define("BestCand_trkpt", "Define_GetValAtArgMax(trkpt, bvtxcl, PassAllExcept_trkpt)")\
        .Define("BestCand_trkptW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_trkpt)")\
        .Histo1D(("h_Trkpt", "", 50, 0, 5), "BestCand_trkpt", "BestCand_trkptW")

    h_Bvtxcl = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_bvtxcl)")\
        .Define("BestCand_bvtxcl", "Define_GetValAtArgMax(bvtxcl, bvtxcl, PassAllExcept_bvtxcl)")\
        .Define("BestCand_bvtxclW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_bvtxcl)")\
        .Histo1D(("h_Bvtxcl", "", 100, 0, 1), "BestCand_bvtxcl", "BestCand_bvtxclW")

    h_Blxysig = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_blsbssig)")\
        .Define("BestCand_blsbssig", "Define_GetValAtArgMax(blsbssig, bvtxcl, PassAllExcept_blsbssig)")\
        .Define("BestCand_blsbssigW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_blsbssig)")\
        .Histo1D(("h_Blxysig", "", 100, 0, 100), "BestCand_blsbssig", "BestCand_blsbssigW")

    h_Bcosalphabs2d = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_bcosalphabs2d)")\
        .Define("BestCand_bcosalphabs2d", "Define_GetValAtArgMax(bcosalphabs2d, bvtxcl, PassAllExcept_bcosalphabs2d)")\
        .Define("BestCand_bcosalphabs2dW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_bcosalphabs2d)")\
        .Histo1D(("h_Bcosalphabs2d", "", 70, 0.9993, 1), "BestCand_bcosalphabs2d", "BestCand_bcosalphabs2dW")

    h_Trkdcabssig = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_trkdcabssig)")\
        .Define("BestCand_trkdcabssig", "Define_GetValAtArgMax(trkdcabssig, bvtxcl, PassAllExcept_trkdcabssig)")\
        .Define("BestCand_trkdcabssigW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_trkdcabssig)")\
        .Histo1D(("h_Trkdcabssig", "", 100, 0, 50), "BestCand_trkdcabssig", "BestCand_trkdcabssigW")

    h_Kshortpt = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_kspt)")\
        .Define("BestCand_kspt", "Define_GetValAtArgMax(kspt, bvtxcl, PassAllExcept_kspt)")\
        .Define("BestCand_ksptW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_kspt)")\
        .Histo1D(("h_Kshortpt", "", 100, 0, 10), "BestCand_kspt", "BestCand_ksptW")

    aug_df_PassAll = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAll)")\
        .Define("BestCand_weight", "Define_GetValAtArgMax(weight, bvtxcl, PassAll)")\

    h_Bmass = aug_df_PassAll\
        .Define("BestCand_bmass", "Define_GetValAtArgMax(bmass, bvtxcl, PassAll)")\
        .Histo1D(("h_Bmass", "", 52, 4.76, 5.80), "BestCand_bmass")
    h_Bpt = aug_df_PassAll\
        .Define("bpt", "sqrt(bpx*bpx+bpy*bpy)")\
        .Define("BestCand_bpt", "Define_GetValAtArgMax(bpt, bvtxcl, PassAll)")\
        .Histo1D(("h_Bpt", "", 100, 0, 100), "BestCand_bpt", "BestCand_weight")
    cimp_getPhi = """
#include "math.h"
ROOT::VecOps::RVec<double> getPhi(const ROOT::VecOps::RVec<double> &py, const ROOT::VecOps::RVec<double> &px)
{
    ROOT::VecOps::RVec<double> output;
    for(int i=0; i<py.size(); i++){
        output.emplace_back(atan2(py.at(i), px.at(i)));
    }
   return output;
}
"""
    if not hasattr(ROOT, "getPhi"):
        ROOT.gInterpreter.Declare(cimp_getPhi)
    h_Bphi = aug_df_PassAll\
        .Define("bphi", "getPhi(bpy, bpx)")\
        .Define("BestCand_bphi", "Define_GetValAtArgMax(bphi, bvtxcl, PassAll)")\
        .Histo1D(("h_Bphi", "", 63, -3.15, 3.15), "BestCand_bphi", "BestCand_weight")
    h_CosThetaL = aug_df_PassAll\
        .Define("BestCand_cosThetaL", "Define_GetValAtArgMax(cosThetaL, bvtxcl, PassAll)")\
        .Histo1D(("h_CosThetaL", "", 100, -1, 1), "BestCand_cosThetaL", "BestCand_weight")
    h_CosThetaK = aug_df_PassAll\
        .Define("BestCand_cosThetaK", "Define_GetValAtArgMax(cosThetaK, bvtxcl, PassAll)")\
        .Histo1D(("h_CosThetaK", "", 100, -1, 1), "BestCand_cosThetaK", "BestCand_weight")

    hists = [h_Bmass, h_Trkpt, h_Bvtxcl, h_Blxysig, h_Bcosalphabs2d, h_Trkdcabssig, h_Kshortpt, h_Bpt, h_Bphi, h_CosThetaL, h_CosThetaK]
    fout = ROOT.TFile(ofname, "RECREATE")
    for h in hists:
        h.Write()
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
            'isLogY': True,
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
        h_data.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of events")

        h_mc = fin_mc.Get(pName)
        h_mc.SetXTitle(pCfg['xTitle'])
        h_mc.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of events")
        h_mc.Scale(h_data.GetSumOfWeights() / h_mc.GetSumOfWeights())
        h_mc.SetLineColor(2)
        h_mc.SetFillColor(2)
        h_mc.SetFillStyle(3001)

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

        plotCollection.Plotter.latexDataMarks()
        return h_data, h_mc

    for p in pConfig.keys():
        h_data, h_mc = drawPlot(p)
        canvas.Print("val_dataMC_jpsi_{0}.pdf".format(pConfig[p]['label']))

if __name__ == '__main__':
    if not os.path.exists("plotDataMCValidation_data.root"):
        # Remark: Takes ~2 minutes for data processing
        create_histo({
            'ofname': "plotDataMCValidation_data.root"
        })
    if not os.path.exists("plotDataMCValidation_jpsi.root"):
        # Remark: Takes ~5 minutes for data processing
        create_histo({
            'ofname': "plotDataMCValidation_jpsi.root",
            'iTreeFiles': ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2/BuToKstarJPsi_8TeV_*.root"]
        })
    plot_histo()
