#!/usr/bin/env python

from __future__ import print_function, division

import re
import ROOT
ROOT.ROOT.EnableImplicitMT()

import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection

if __name__ == '__main__':
    tree = ROOT.TChain("tree")
    for t in dataCollection.dataReader.cfg['ifile']:
        tree.Add(t)

    sngDataFrame = ROOT.RDataFrame(tree)
    selDataFrame = sngDataFrame.Filter(anaSetup.q2bins['summary']['cutString']).Filter(anaSetup.cuts[-1])
    selDataFrame_bin1 = selDataFrame.Filter(anaSetup.q2bins['belowJpsi']['cutString'])
    selDataFrame_bin3 = selDataFrame.Filter(anaSetup.q2bins['betweenPeaks']['cutString'])
    selDataFrame_bin5 = selDataFrame.Filter(anaSetup.q2bins['abovePsi2s']['cutString'])

    # Book all figures
    plots = {}
    plots['postSel_LambdaMass'] = {
	    'hist': sngDataFrame.Histo1D(("postSel_LambdaMass", "", 50, 1.1, 1.15), "Lambdamass"),
	    'xTitle': "m_{p#pi} [GeV]",
	}
    plots['postSel_CosThetaL_Bvtxcl'] = {
	    'hist': sngDataFrame.Histo2D(("postSel_CosThetaL_Bvtxcl", "", 10, -1, 1, 20, 0, 1), "CosThetaL", "Bvtxcl"),
	    'xTitle': "cos#theta_{l}",
	    'yTitle': "B^{+} L_{xy}/#sigma",
	    'drawOpt': "VIOLIN",
	}
    plots['postSel_CosThetaK_Bvtxcl'] = {
	    'hist': sngDataFrame.Histo2D(("postSel_CosThetaK_Bvtxcl", "", 10, -1, 1, 20, 0, 1), "CosThetaK", "Bvtxcl"),
	    'xTitle': "cos#theta_{K}",
	    'yTitle': "B^{+} L_{xy}/#sigma",
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
	    if re.match("LEGO", hCfg.get('drawOpt', "")):
		hist.SetTitleOffset(1.4, "X")
		hist.SetTitleOffset(1.8, "Y")
		hist.SetTitleOffset(1.5, "Z")
	    hist.Draw(hCfg.get('drawOpt', "E"))

	else:
	    hist.Draw(hCfg.get('drawOpt', "E"))

	plotCollection.plotter.latexDataMarks()
	plotCollection.Plotter.latexLumi()
	canvas.Update()
	canvas.Print("{0}.pdf".format(hName))
