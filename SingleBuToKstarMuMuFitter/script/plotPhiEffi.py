#!/usr/bin/env python

import os
import re
import ROOT

from SingleBuToKstarMuMuFitter.anaSetup import modulePath, q2bins, bMassRegions, cuts
from SingleBuToKstarMuMuFitter.dataCollection import sigMCReader
from SingleBuToKstarMuMuFitter.plotCollection import Plotter

foutName = "plotPhiEffi.root"
targetBins = ['belowJpsi', 'betweenPeaks', 'abovePsi2s', 'summary']

def create_histo(cfg=None):
    forceRebuild = False

    setupEfficiencyBuildProcedure = {
        'ifiles': sigMCReader.cfg['ifile'],
        'baseString': "1>0",
        'cutString': "Bmass > 0.5 && ({0})".format(cuts[-1]),
    }

    if not os.path.exists(foutName) or forceRebuild:
        hists = []

        treein = ROOT.TChain("tree")
        for f in setupEfficiencyBuildProcedure['ifiles']:
            treein.Add(f)

        df = ROOT.RDataFrame(treein)\
                .Filter(setupEfficiencyBuildProcedure['baseString'])

        for binKey in targetBins:
            hists.append(df.Filter(re.sub("Mumumass", "sqrt(genQ2)", q2bins[binKey]['cutString']))\
                .Histo1D(("h_genPhi_{0}".format(binKey), "", 32, 0, 3.2), "genPhi"))

            hists.append(df.Filter(q2bins[binKey]['cutString'])\
                .Filter(setupEfficiencyBuildProcedure['cutString'])\
                .Filter(bMassRegions['SR']['cutString'])\
                .Histo1D(("h_Phi_{0}".format(binKey), "", 32, 0, 3.2), "Phi"))

        fout = ROOT.TFile(foutName, "UPDATE")
        for h in hists:
            h.Write()
        fout.Close()
    pass

def plot_histo():
    canvas = Plotter.canvas
    canvas.cd()

    if not os.path.exists(foutName):
        create_histo()

    fin = ROOT.TFile(foutName)
    for binKey in targetBins:
        h_rec = ROOT.TEfficiency(fin.Get("h_Phi_{0}".format(binKey)), fin.Get("h_genPhi_{0}".format(binKey)))
        gr = h_rec.CreateGraph()
        gr.SetMinimum(0)
        gr.SetMaximum(1e-2)
        gr.GetXaxis().SetTitle("#phi")
        gr.GetYaxis().SetTitle("Efficiency")
        gr.Draw("AP")
        canvas.Update()

        Plotter.latexDataMarks(marks=['sim'])
        Plotter.latexQ2(binKey)
        canvas.Print("h_rec_Phi_{0}.pdf".format(q2bins[binKey]['label']))
    fin.Close()
    pass

if __name__ == "__main__":
    plot_histo()
