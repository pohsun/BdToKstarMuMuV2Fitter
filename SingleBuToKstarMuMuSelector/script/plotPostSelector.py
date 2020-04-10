#!/usr/bin/env python

from __future__ import print_function, division

import re
from copy import copy
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
    # treeMC.Add(dataCollection.sigMCReader.cfg['ifile'][0]) # DEBUG

    selConditions = "({0})".format(")&&(".join([anaSetup.q2bins['summary']['cutString'], 
						anaSetup.bMassRegions['SR']['cutString'],
						anaSetup.cuts[-1]
						]))
    selConditions_jpsi = "({0})".format(")&&(".join([anaSetup.q2bins['jpsi']['cutString'],
						anaSetup.bMassRegions['SR']['cutString'],
						anaSetup.cuts_antiResVeto
						]))

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
    
    # It seems RDataFrame.Histo2D is weird, not all draw options is supported.
    treeMC.Draw("Bvtxcl:CosThetaK>>postSel_CosThetaK_Bvtxcl_bin0(10, -1, 1, 18, 0.1, 1)", selConditions, "goff")
    plots['postSel_CosThetaK_Bvtxcl_bin0'] = {
	    # 'hist': selDataFrame_MC.Histo2D(("postSel_CosThetaK_Bvtxcl", "", 10, -1, 1, 18, 0.1, 1), "CosThetaK", "Bvtxcl"),
	    'hist': ROOT.gDirectory.Get("postSel_CosThetaK_Bvtxcl_bin0"),
	    'xTitle': "cos#theta_{K}",
	    'yTitle': "B^{+} vtx CL",
	    'drawOpt': ["VIOLIN", "COLZ", "BOX", "SCAT", "LEGO2"],
	    'marks': ['sim'],
	}

    plots['postSel_CosThetaL_Bvtxcl_bin0'] = copy(plots['postSel_CosThetaK_Bvtxcl_bin0'])
    treeMC.Draw("Bvtxcl:CosThetaL>>postSel_CosThetaL_Bvtxcl_bin0(10, -1, 1, 18, 0.1, 1)", selConditions, "goff")
    plots['postSel_CosThetaL_Bvtxcl_bin0'].update({
	    'hist': ROOT.gDirectory.Get("postSel_CosThetaL_Bvtxcl_bin0"),
	    'xTitle': "cos#theta_{l}",
	})

    # What does this mean?
    plots['postSel_CosThetaK_Bvtxcl_data_bin2'] = copy(plots['postSel_CosThetaK_Bvtxcl_bin0'])
    treeDATA.Draw("Bvtxcl:CosThetaK>>postSel_CosThetaK_Bvtxcl_data_bin2(10, -1, 1, 18, 0.1, 1)", selConditions_jpsi, "goff")
    plots['postSel_CosThetaK_Bvtxcl_data_bin2']['hist'] = ROOT.gDirectory.Get("postSel_CosThetaK_Bvtxcl_data_bin2")
    plots['postSel_CosThetaK_Bvtxcl_data_bin2']['marks'] = None

    plots['postSel_CosThetaL_Bvtxcl_data_bin2'] = copy(plots['postSel_CosThetaK_Bvtxcl_data_bin2'])
    treeDATA.Draw("Bvtxcl:CosThetaL>>postSel_CosThetaL_Bvtxcl_data_bin2(10, -1, 1, 18, 0.1, 1)", selConditions_jpsi, "goff")
    plots['postSel_CosThetaL_Bvtxcl_data_bin2']['hist'] = ROOT.gDirectory.Get("postSel_CosThetaL_Bvtxcl_data_bin2")
    plots['postSel_CosThetaK_Bvtxcl_data_bin2']['xTitle'] = plots['postSel_CosThetaL_Bvtxcl_bin0']['xTitle']

    # plots['postSel_CosThetaK_Bvtxcl_bin0__SCAT'] = {
    #         'hist': selDataFrame_MC.Graph("CosThetaK", "Bvtxcl"),
    #         'xTitle': "cos#theta_{K}",
    #         'yTitle': "B^{+} vtx CL",
    #         'marks': ['sim'],
    #     }
    # plots['postSel_CosThetaL_Bvtxcl_bin0__SCAT'] = {
    #         'hist': selDataFrame_MC.Graph("CosThetaL", "Bvtxcl"),
    #         'xTitle': "cos#theta_{l}",
    #         'yTitle': "B^{+} vtx CL",
    #         'marks': ['sim'],
    #     }

    ### Yet another pyROOT bug https://sft.its.cern.ch/jira/browse/ROOT-10396
    # postSel_CosThetaL_Bvtxcl__SCAT = ROOT.TH2F("postSel_CosThetaL_Bvtxcl__SCAT", "", 100, -1, 1, 90, 0.1, 1)
    # postSel_CosThetaK_Bvtxcl__SCAT = ROOT.TH2F("postSel_CosThetaK_Bvtxcl__SCAT", "", 100, -1, 1, 90, 0.1, 1)
    # plots['postSel_CosThetaL_Bvtxcl_bin0__SCAT'] = {
    #         'hist': selDataFrame_MC.Fill(postSel_CosThetaL_Bvtxcl__SCAT, ["CosThetaL", "Bvtxcl"]),
    #         'xTitle': "cos#theta_{l}",
    #         'yTitle': "B^{+} vtx CL",
    #	      'marks': ['sim'],
    #     }
    # plots['postSel_CosThetaK_Bvtxcl_bin0__SCAT'] = {
    #         'hist': selDataFrame_MC.Fill(ROOT.Double, ROOT.Double)(postSel_CosThetaK_Bvtxcl__SCAT, ["CosThetaK", "Bvtxcl"]),
    #         'xTitle': "cos#theta_{K}",
    #         'yTitle': "B^{+} vtx CL",
    #	      'marks': ['sim'],
    #     }
    
    # Draw all figures
    canvas = plotCollection.Plotter.canvas
    for hName, hCfg in plots.items():
	hist = hCfg['hist']
	hist.SetFillColor(2)
	hist.SetMarkerStyle(20)
	hist.SetMarkerSize(0.1)

	if hist.InheritsFrom("TGraph"):

	    hist.Draw("AP")
	    if optIdx == 0:
		hist.SetMinimum(0)
		hist.SetMinimum(1.5 * hist.GetMaximum())
	    hist.GetXaxis().SetTitle(hCfg.get('xTitle', "Arbitrary unit"))
	    hist.GetYaxis().SetTitle(hCfg.get('yTitle', "Events"))
	    plotCollection.plotter.latexDataMarks(hCfg.get('marks', None))
	    canvas.Update()
	    canvas.Print("{0}.pdf".format(hName))
	elif hist.InheritsFrom("TH2"):
	    hist.SetFillColor(2)
	    for optIdx, opt in enumerate(hCfg.get('drawOpt', ["SCAT"])):
		opt = opt.upper()
		if re.match("LEGO2", opt):
		    hist.SetTitleOffset(1.4, "X")
		    hist.SetTitleOffset(1.8, "Y")
		    hist.SetTitleOffset(1.5, "Z")

		hist.Draw(opt)
		hist.SetMinimum(0)
		hist.SetXTitle(hCfg.get('xTitle', "Arbitrary unit"))
		hist.SetYTitle(hCfg.get('yTitle', "Events"))
		hist.SetZTitle(hCfg.get('zTitle', "Events"))
		plotCollection.plotter.latexDataMarks(hCfg.get('marks', None))
		canvas.Update()
		canvas.Print("{0}__{1}.pdf".format(hName, opt.replace(' ', '_')))
	else:
	    for optIdx, opt in enumerate(hCfg.get('drawOpt', ["E"])):
		opt = opt.upper()

		hist.Draw(opt)
		if optIdx == 0:
		    hist.SetMinimum(0)
		    hist.SetMinimum(1.5 * hist.GetMaximum())
		hist.SetXTitle(hCfg.get('xTitle', "Arbitrary unit"))
		hist.SetYTitle(hCfg.get('yTitle', "Events"))
		plotCollection.plotter.latexDataMarks(hCfg.get('marks', None))
		canvas.Update()
		canvas.Print("{0}__{1}.pdf".format(hName, opt.replace(' ', '_')))
