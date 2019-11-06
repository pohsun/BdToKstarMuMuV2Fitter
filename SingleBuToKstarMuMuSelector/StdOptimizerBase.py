#!/usr/bin/env python

from __future__ import print_function, division

import ROOT
import SingleBuToKstarMuMuSelector.cpp

# Preselection cut strings
def Define_AllCheckBits(df):
    aug_df = df.Define("bit_HasGoodDimuon", "DefineBit_HasGoodDimuon(mumisgoodmuon, mupisgoodmuon, mumntrklayers, mupntrklayers, mumnpixlayers, mupnpixlayers, mumnormchi2, mupnormchi2, mumdxyvtx, mupdxyvtx, mumdzvtx, mupdzvtx)")\
        .Define("bit_trkpt"        , "DefineBit_trkpt(trkpt)")\
        .Define("bit_trkdcabssig"  , "DefineBit_trkdcabssig(trkdcabs, trkdcabserr)")\
        .Define("bit_kspt"         , "DefineBit_kspt(kspx, kspy)")\
        .Define("bit_kstarmass"    , "DefineBit_kstarmass(kstarmass)")\
        .Define("bit_bvtxcl"       , "DefineBit_bvtxcl(bvtxcl)")\
        .Define("bit_blsbssig"     , "DefineBit_blsbssig(blsbs, blsbserr)")\
        .Define("bit_bcosalphabs2d", "DefineBit_bcosalphabs2d(bcosalphabs2d)")\
        .Define("bit_bmass"        , "DefineBit_bmass(bmass)")\
        .Define("bit_resRej", "((mumumass>(3.096916+3.5*mumumasserr))+(mumumass<(3.096916-5.5*mumumasserr)))*((mumumass>(3.686109+3.5*mumumasserr))+(mumumass<(3.686109-3.5*mumumasserr)))>0")\
        .Define("bit_antiRad", "(abs(bmass-mumumass-2.182)>0.09)*(abs(bmass-mumumass-1.593)>0.03)>0")\
        .Define("kspt", "sqrt(kspx*kspx + kspy*kspy)")\
        .Define("blsbssig", "blsbs/blsbserr")\
        .Define("trkdcabssig", "trkdcabs/trkdcabserr")\
        .Define("cosThetaL", "Define_cosThetaL(bpx, bpy, bpz, bmass, bchg, mumpx, mumpy, mumpz, muppx, muppy, muppz)")\
        .Define("cosThetaK", "Define_cosThetaK(bpx, bpy, bpz, bmass, kstarmass, kspx, kspy, kspz, trkpx, trkpy, trkpz)")
    return aug_df

presel_cuts = [
]

if __name__ == '__main__':
    tree = ROOT.TChain("tree")
    tree.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2/BuToKstarMuMu-data-2012*-v3p2-merged.root")

    df = ROOT.RDataFrame(tree).Filter("nb>5")
    aug_df = Define_AllCheckBits(df)
    histo_HasGoodDimuon0 = aug_df.Histo1D(("bit_HasGoodDimuon", "", 2, 0, 2), "bit_HasGoodDimuon")

    canvas = ROOT.TCanvas()
    histo_HasGoodDimuon0.Draw()
    print(aug_df.GetColumnNames())
    print(aug_df.GetDefinedColumnNames())
    canvas.Print("test_StdOptimizerBase.pdf")
