#!/usr/bin/env python

from __future__ import print_function, division

import re
import ROOT
ROOT.ROOT.EnableImplicitMT()

import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection

if __name__ == '__main__':
    treeDATA = ROOT.TChain("tree")
    for t in dataCollection.dataReader.cfg['ifile']:
        treeDATA.Add(t)

    treeMC = ROOT.TChain("tree")
    for t in dataCollection.sigMCReader.cfg['ifile']:
        treeMC.Add(t)

    sngDataFrame_DATA = ROOT.RDataFrame(treeDATA)
    selDataFrame_DATA = sngDataFrame_DATA.Filter(anaSetup.q2bins['summary']['cutString']).Filter(anaSetup.cuts[-1])

    sngDataFrame_MC = ROOT.RDataFrame(treeMC)
    selDataFrame_MC = sngDataFrame_MC.Filter(anaSetup.q2bins['summary']['cutString']).Filter(anaSetup.cuts[-1])

    # Book all figures
    plots = {}
    plots['postSel_LambdaMass'] = {
	    'hist': sngDataFrame_DATA.Histo1D(("postSel_LambdaMass", "", 50, 1.1, 1.15), "Lambdamass"),
	    'xTitle': "m_{p#pi} [GeV]",
	}
    plots['postSel_CosThetaL_Bvtxcl_bin0'] = {
	    'hist': selDataFrame_MC.Histo2D(("postSel_CosThetaL_Bvtxcl", "", 20, -1, 1, 18, 0.1, 1), "CosThetaL", "Bvtxcl"),
	    'xTitle': "cos#theta_{l}",
	    'yTitle': "B^{+} vtx CL",
	    'drawOpt': "VIOLIN",
	}
    plots['postSel_CosThetaK_Bvtxcl_bin0'] = {
	    'hist': selDataFrame_MC.Histo2D(("postSel_CosThetaK_Bvtxcl", "", 20, -1, 1, 18, 0.1, 1), "CosThetaK", "Bvtxcl"),
	    'xTitle': "cos#theta_{K}",
	    'yTitle': "B^{+} vtx CL",
	    'drawOpt': "VIOLIN",
	}
    
    # Draw all figures
    canvas = plotCollection.Plotter.canvas
    for hName, hCfg in plots.items():
	hist = hCfg['hist']
	hist.SetMinimum(0)
	hist.SetMinimum(1.5 * hist.GetMaximum())
	hist.SetXTitle(hCfg.get('xTitle', "Arbitrary unit"))
	hist.SetYTitle(hCfg.get('yTitle', "Events"))

	if hist.InheritsFrom("TH2"):
	    hist.SetZTitle(hCfg.get('zTitle', "Events"))
	    drawOpt = hCfg.get('drawOpt', "")

	    hist.SetFillColor(2)
	    hist.SetMarkerStyle(20)
	    hist.SetMarkerSize(0.2)
	    if re.match("LEGO", hCfg.get('drawOpt', "")):
		hist.SetTitleOffset(1.4, "X")
		hist.SetTitleOffset(1.8, "Y")
		hist.SetTitleOffset(1.5, "Z")
	    hist.Draw(hCfg.get('drawOpt', "SCAT"))
	else:
	    hist.Draw(hCfg.get('drawOpt', "E"))

	plotCollection.plotter.latexDataMarks()
	plotCollection.Plotter.latexLumi()
	canvas.Update()
	canvas.Print("{0}.pdf".format(hName))
