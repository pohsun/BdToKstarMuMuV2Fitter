#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 ft=python et:

import os

import ROOT
import SingleBuToKstarMuMuFitter.plotCollection as plotCollection

def create_histo():
    tree = ROOT.TChain("tree")
    tree.Add("/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2/BuToKstarMuMu-data-2012*.root")

    fout = ROOT.TFile("plotPreSelector.root", "RECREATE")

    tree.Draw("sqrt(2*sqrt(pippx*pippx+pippy*pippy+pippz*pippz+0.13957*0.13957)*sqrt(pimpx*pimpx+pimpy*pimpy+pimpz*pimpz+0.13957*0.13957)-2*(pippx*pimpx+pippy*pimpy+pippz*pimpz)+2*0.13956*0.13957)>>preSel_KshortMass(200,0.4,0.6)")
    tree.Draw("kstarmass>>preSel_KstarMass(200,0.792,0.992)")

    fout.Write()
    fout.Close()

def plot_histo(fname="plotPreSelector.root"):
    canvas = plotCollection.Plotter.canvas

    fin = ROOT.TFile(fname)

    def _plotAndFitKshort(hname):
        h = fin.Get(hname)

        # Take the value from single Gaussian for the Kshort window
        #  f = ROOT.TF1("f", "[0]*exp(-0.5*((x-[1])/[2])**2)", 0.45, 0.55)
        #  f.SetParameter(1, 0.492)
        #  f.SetParLimits(2, 0.001, 0.008)
        #  f.SetParameter(2, 0.006)

        # Double Gaussian looks fine
        f = ROOT.TF1("f", "[0]*exp(-0.5*((x-[1])/[2])**2)+[3]*exp(-0.5*((x-[1])/[4])**2)", 0.45, 0.55)
        f.SetParameter(1, 0.492)
        f.SetParLimits(2, 0.001, 0.008)
        f.SetParameter(2, 0.006)
        f.SetParameter(4, 0.01)
        f.SetParLimits(4, 0.008, 0.05)

        # Breit-Wigner also looks fine.
        #  f = ROOT.TF1("f", "[0]/((x-[1])**2+([2]**2)/4)/(2*3.1415926)", 0.45, 0.55)
        #  f.SetParameter(1, 0.492)
        #  f.SetParLimits(2, 0.001, 0.008)
        #  f.SetParameter(2, 0.006)

        h.Fit("f", "", "", 0.48, 0.515)
        h.SetXTitle("m_{#pi^{+}#pi^{-}}")
        h.SetMinimum(0)
        h.Draw()

        highlight_SR = ROOT.TBox(0.417, h.GetYaxis().GetXmin(), 0.577, h.GetYaxis().GetXmax())
        highlight_SR.SetFillColorAlpha(ROOT.kRed, 0.3)
        highlight_SR.Draw()

        plotCollection.Plotter.latexDataMarks(extraArgs={'y':0.86})
        canvas.Update()
        canvas.Print("{0}.pdf".format(hname))

    _plotAndFitKshort("preSel_KshortMass")

    def _plotAndFitKstar(hname):
        h = fin.Get(hname)
        h.Print()

        # Take the value from single Gaussian for the Kshort window
        #  f = ROOT.TF1("f", "[0]*exp(-0.5*((x-[1])/[2])**2)", 0.45, 0.55)
        #  f.SetParameter(1, 0.492)
        #  f.SetParLimits(2, 0.001, 0.008)
        #  f.SetParameter(2, 0.006)

        # Double Gaussian looks fine
        f = ROOT.TF1("f", "[0]*exp(-0.5*((x-[1])/[2])**2)+[3]*exp(-0.5*((x-[1])/[4])**2)+[5]+[6]*x", 0.792, 0.992)
        f.SetParameter(1, 0.892)
        f.SetParLimits(2, 0.01, 0.1)
        f.SetParameter(2, 0.05)
        f.SetParameter(4, 0.1)
        f.SetParLimits(4, 0.1, 0.3)

        # Breit-Wigner also looks fine.
        #  f = ROOT.TF1("f", "[0]/((x-[1])**2+([2]**2)/4)/(2*3.1415926)", 0.45, 0.55)
        #  f.SetParameter(1, 0.492)
        #  f.SetParLimits(2, 0.001, 0.008)
        #  f.SetParameter(2, 0.006)

        h.Fit("f", "", "", 0.792, 0.992)
        h.SetXTitle("m_{K^{*#pm}}")
        h.SetMinimum(0)
        h.Draw()

        plotCollection.Plotter.latexDataMarks(extraArgs={'y':0.86})
        canvas.Update()
        canvas.Print("{0}.pdf".format(hname))

    _plotAndFitKstar("preSel_KstarMass")

if __name__ == '__main__':
    if not os.path.exists("plotPreSelector.root"):
        create_histo()
    plot_histo()
