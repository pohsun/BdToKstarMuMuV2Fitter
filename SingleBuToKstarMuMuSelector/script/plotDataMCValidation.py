#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=0 fdn=2 ft=python et:

import os

import ROOT
from SingleBuToKstarMuMuFitter.Plotter import Plotter
import SingleBuToKstarMuMuSelector.StdOptimizerBase as StdOptimizerBase


# Remark: additional to the reversed resRej and antiRad, lambdaVeto is performed for better check in jpsi CR.
def create_histo(kwargs):
    ofname = kwargs.get('ofname', "plotDataMCValidation.root")
    iTreeFiles = kwargs.get('iTreeFiles', ["/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2/BuToKstarMuMu-data-2012*.root"])
    wgtString = kwargs.get('wgtString', "(abs(bmass-5.28)<0.1) - (0.2/0.84)*(bmass>4.76)*(bmass<5.18) - (0.2/0.84)*(bmass>5.38)*(bmass<5.80)") # Full sideband
    # wgtString = kwargs.get('wgtString', "(abs(bmass-5.28)<0.06) - 0.5*(abs(bmass-5.11)<0.06) - 0.5*(abs(bmass-5.46)<0.06)") # Local sideband

    tree = ROOT.TChain("tree")
    for tr in iTreeFiles:
        tree.Add(tr)

    hasLambdaVeto = "1" # 1 or bit_lambdaVeto
    df = ROOT.RDataFrame(tree).Filter("nb>0", "At least one B candidate")
    aug_df = StdOptimizerBase.Define_AllCheckBits(df)\
        .Define("weight", wgtString)\
        .Define("PassAll"                     ,hasLambdaVeto + " * (1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_trkpt"         ,hasLambdaVeto + " * (1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * 1 * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_trkdcabssig"   ,hasLambdaVeto + " * (1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * 1 * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_kspt"          ,hasLambdaVeto + " * (1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * 1 * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_blsbssig"      ,hasLambdaVeto + " * (1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * 1 * bit_bcosalphabs2d * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_bcosalphabs2d" ,hasLambdaVeto + " * (1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * 1 * bit_bvtxcl * bit_kstarmass")\
        .Define("PassAllExcept_bvtxcl"        ,hasLambdaVeto + " * (1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * 1 * bit_kstarmass")\
        .Define("PassAllExcept_kstarmass"     ,hasLambdaVeto + " * (1-bit_resRej) * (1-bit_antiRad) * bit_HasGoodDimuon * bit_trkpt * bit_trkdcabssig * bit_kspt * bit_blsbssig * bit_bcosalphabs2d * bit_bvtxcl * 1")

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
        .Histo1D(("h_Blxysig", "", 50, 0, 100), "BestCand_blsbssig", "BestCand_blsbssigW")

    h_Bcosalphabs2d = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_bcosalphabs2d)")\
        .Define("BestCand_bcosalphabs2d", "Define_GetValAtArgMax(bcosalphabs2d, bvtxcl, PassAllExcept_bcosalphabs2d)")\
        .Define("BestCand_bcosalphabs2dW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_bcosalphabs2d)")\
        .Histo1D(("h_Bcosalphabs2d", "", 70, 0.9993, 1), "BestCand_bcosalphabs2d", "BestCand_bcosalphabs2dW")

    h_Trkdcabssig = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_trkdcabssig)")\
        .Define("BestCand_trkdcabssig", "Define_GetValAtArgMax(trkdcabssig, bvtxcl, PassAllExcept_trkdcabssig)")\
        .Define("BestCand_trkdcabssigW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_trkdcabssig)")\
        .Histo1D(("h_Trkdcabssig", "", 40, 0, 40), "BestCand_trkdcabssig", "BestCand_trkdcabssigW")

    h_Kshortpt = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAllExcept_kspt)")\
        .Define("BestCand_kspt", "Define_GetValAtArgMax(kspt, bvtxcl, PassAllExcept_kspt)")\
        .Define("BestCand_ksptW", "Define_GetValAtArgMax(weight, bvtxcl, PassAllExcept_kspt)")\
        .Histo1D(("h_Kshortpt", "", 40, 0, 10), "BestCand_kspt", "BestCand_ksptW")

    aug_df_PassAll = aug_df\
        .Filter("Filter_IsNonEmptyBit(PassAll)")\
        .Define("BestCand_weight", "Define_GetValAtArgMax(weight, bvtxcl, PassAll)")\

    h_Bmass = aug_df_PassAll\
        .Define("BestCand_bmass", "Define_GetValAtArgMax(bmass, bvtxcl, PassAll)")\
        .Histo1D(("h_Bmass", "", 26, 4.76, 5.80), "BestCand_bmass")
    h_Bpt = aug_df_PassAll\
        .Define("bpt", "sqrt(bpx*bpx+bpy*bpy)")\
        .Define("BestCand_bpt", "Define_GetValAtArgMax(bpt, bvtxcl, PassAll)")\
        .Histo1D(("h_Bpt", "", 50, 0, 100), "BestCand_bpt", "BestCand_weight")
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
        .Histo1D(("h_Bphi", "", 21, -3.15, 3.15), "BestCand_bphi", "BestCand_weight")
    h_CosThetaL = aug_df_PassAll\
        .Define("BestCand_cosThetaL", "Define_GetValAtArgMax(cosThetaL, bvtxcl, PassAll)")\
        .Histo1D(("h_CosThetaL", "", 20, -1, 1), "BestCand_cosThetaL", "BestCand_weight")
    h_CosThetaK = aug_df_PassAll\
        .Define("BestCand_cosThetaK", "Define_GetValAtArgMax(cosThetaK, bvtxcl, PassAll)")\
        .Histo1D(("h_CosThetaK", "", 20, -1, 1), "BestCand_cosThetaK", "BestCand_weight")

    hists = [h_Bmass, h_Trkpt, h_Bvtxcl, h_Blxysig, h_Bcosalphabs2d, h_Trkdcabssig, h_Kshortpt, h_Bpt, h_Bphi, h_CosThetaL, h_CosThetaK]
    fout = ROOT.TFile(ofname, "RECREATE")
    for h in hists:
        h.Write()
    fout.Write()
    fout.Close()

def plot_histo():
    canvas = Plotter.canvas

    fin_data = ROOT.TFile("plotDataMCValidation_data.root")
    fin_mc = ROOT.TFile("plotDataMCValidation_jpsi.root")

    pConfig = {
        # 'h_Bmass': {
        #     'label': "Bmass",
        #     'xTitle': "m_{B^{+}} [GeV]",
        #     'yTitle': None,
        # },
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
            'cutPoints': [0.1],
        },
        'h_Blxysig': {
            'label': "Blxysig",
            'xTitle': "B^{+} L_{xy}/#sigma",
            'yTitle': None,
            'cutPoints': [12.],
        },
        'h_Bcosalphabs2d': {
            'label': "Bcosalphabs2d",
            'xTitle': "cos#alpha_{xy}^{B^{+}}",
            'yTitle': None,
            'isLogY': True,
            'cutPoints': [0.9994],
        },
        'h_Kshortpt': {
            'label': "Kshortpt",
            'xTitle': "K_{S} p_{T} [GeV]",
            'yTitle': None,
            'cutPoints': [1.],
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
            'cutPoints': [0.4],
        },
        'h_Trkdcabssig': {
            'label': "Trkdcasigbs",
            'xTitle': "#pi DCA/#sigma",
            'yTitle': None,
            'cutPoints': [0.2],
        },
    }
    def drawPlot(pName):
        pCfg = pConfig[pName]
        h_data = fin_data.Get(pName)
        h_data.UseCurrentStyle()
        h_data.SetXTitle(pCfg['xTitle'])
        h_data.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of events")

        h_mc = fin_mc.Get(pName)
        h_mc.UseCurrentStyle()
        h_mc.SetXTitle(pCfg['xTitle'])
        h_mc.SetYTitle(pCfg['yTitle'] if pCfg['yTitle'] else "Number of events")
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

        legend = ROOT.gPad.BuildLegend(.60, .70, .95, .89)
        legend.Clear()
        legend.SetFillColor(0)
        legend.SetFillStyle(0)
        legend.SetBorderSize(0)
        legend.AddEntry(h_data, "Data", "lep")
        legend.AddEntry(h_mc, "J/#psi K^{*+} MC", "F")
        legend.Draw()

        line = ROOT.TLine()
        line.SetLineWidth(2)
        line.SetLineStyle(10)
        if pCfg.get('cutPoints', False):
            for pt in pCfg.get('cutPoints'):
                line.DrawLine(pt, h_mc.GetMinimum(), pt, h_mc.GetMaximum())
        
        Plotter.latexDataMarks()
        return h_data, h_mc

    def drawRatioPlot(pName, h_data, h_mc):
        pCfg = pConfig[pName]

        h_ratio = ROOT.TRatioPlot(h_data, h_mc)
        h_ratio.SetSeparationMargin(0.04)
        h_ratio.SetH1DrawOpt("E")
        h_ratio.SetH2DrawOpt("HIST")
        h_ratio.Draw()
        if pCfg.get('isLogY', False):
            h_ratio.GetUpperPad().SetLogy(1)
        h_ratio.GetUpperRefYaxis().SetRangeUser(h_mc.GetMinimum(), h_mc.GetMaximum())
        h_ratio.GetUpperRefYaxis().SetMaxDigits(3)
        h_ratio.GetUpperRefYaxis().SetTitleSize(0.06)
        h_ratio.GetUpperRefYaxis().SetTitleOffset(1.33)
        h_ratio.GetLowerRefYaxis().SetRangeUser(0.5, 1.5)
        h_ratio.GetLowerRefYaxis().SetTitle("Data/MC")
        h_ratio.GetLowerRefYaxis().SetTitleSize(0.06)
        h_ratio.GetLowerRefYaxis().SetTitleOffset(1.33)
        h_ratio.GetLowYaxis().SetNdivisions(502)
        h_ratio.SetSplitFraction(0.4)
        h_ratio.SetUpTopMargin(ROOT.gStyle.GetPadTopMargin()/(1-0.4)) # corrected by split fraction
        h_ratio.SetLowBottomMargin(ROOT.gStyle.GetPadBottomMargin()/0.4)
        h_ratio.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin())
        h_ratio.SetRightMargin(ROOT.gStyle.GetPadRightMargin())
        h_ratio.GetLowerPad().Update()

        upperPad = h_ratio.GetUpperPad()
        upperPad.cd()
        h_data.Draw("E SAME")
        upperPad.Update()
        
        legend = upperPad.BuildLegend(.60, .60, .95, .89)
        legend.Clear()
        legend.SetFillColor(0)
        legend.SetFillStyle(0)
        legend.SetBorderSize(0)
        legend.AddEntry(h_data, "Data", "lep")
        legend.AddEntry(h_mc, "J/#psi K^{*+} MC", "F")
        legend.Draw()

        line = ROOT.TLine()
        line.SetLineWidth(2)
        line.SetLineStyle(10)
        if pCfg.get('cutPoints', False):
            for pt in pCfg.get('cutPoints'):
                line.DrawLine(pt, h_mc.GetMinimum(), pt, h_mc.GetMaximum())

        canvas.cd()
        Plotter.latexLumi()
        Plotter.latexCMSMark()
        Plotter.latexCMSExtra()
        canvas.Update()
        return h_ratio

    for p in pConfig.keys():
        h_data, h_mc = drawPlot(p)
        canvas.Print("val_dataMC_jpsi_{0}_noRatio.pdf".format(pConfig[p]['label']))
        h_ratio = drawRatioPlot(p, h_data, h_mc)
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
