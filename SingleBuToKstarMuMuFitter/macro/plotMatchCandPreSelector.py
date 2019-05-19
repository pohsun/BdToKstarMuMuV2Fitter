#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import ROOT

if __name__ == '__main__':
    ch = ROOT.TChain("tree")
    ch.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/DATA/sel_2012A_SCN_merged_v18JUL_data_cut3-LHCb_s0.root")
    ch.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/DATA/sel_2012B_SCN_merged_v18JUL_data_cut3-LHCb_s0.root")
    ch.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/DATA/sel_2012C_SCN_merged_v18JUL_data_cut3-LHCb_s0.root")
    ch.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/sel/v3p5/DATA/sel_2012D_SCN_merged_v18JUL_data_cut3-LHCb_s0.root")
    ch.Process("plotMatchCandPreSelector.C+", "")
