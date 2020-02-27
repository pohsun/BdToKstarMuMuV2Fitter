#!/usr/bin/env python

from __future__ import print_function, division
import ROOT

import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection

if __name__ == '__main__':
    tree = ROOT.TChain("tree")
    for t in dataCollection.sigMCReaderCfg['ifile']:
        tree.Add(t)
    nTotal = tree.Draw("isTrueB",
                       "({0}) && ({1})".format(anaSetup.cuts[-1], anaSetup.bMassRegions['SR']['cutString']),
                       "goff")
    nSelected = tree.Draw("isTrueB",
                          "(isTrueB > 0) && ({0}) && ({1})".format(anaSetup.cuts[-1], anaSetup.bMassRegions['SR']['cutString']),
                          "goff")
    print("GenMatching efficiency = {0:.3f}%".format(100. * nSelected / nTotal))
