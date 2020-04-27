#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : Shared object definition.

from ROOT import RooRealVar
from ROOT import RooArgSet
from SingleBuToKstarMuMuFitter.anaSetup import bMassRegions

Bmass = RooRealVar("Bmass","#font[132]{m(K_{S}^{0}#pi^{+}#mu^{+}#mu^{#font[122]{\55}})} [GeV]", 4.50, 6.00)
for regName, regCfg in bMassRegions.items():
    # Remark: Only regions defined while running pdfCollection could be used in ROOT.RooFit(regionName)
    Bmass.setRange(regName, regCfg['range'][0], regCfg['range'][1])

CosThetaK = RooRealVar("CosThetaK", r"#font[132]{cos} #font[12]{#theta_{K}}", -1., 1.)
CosThetaL = RooRealVar("CosThetaL", r"#font[132]{cos} #font[12]{#theta_{l}}", -1., 1.)
Mumumass = RooRealVar("Mumumass", r"#font[132]{m_{#mu#mu}} [GeV]", 0., 10.)
Mumumasserr = RooRealVar("Mumumasserr", r"Error of #font[132]{m_{#mu#mu}} [GeV]", 0., 10.)
Kstarmass = RooRealVar("Kstarmass", r"#font[132]{m_{K^{*}}} [GeV]", 0, 1.5)
Kshortmass = RooRealVar("Kshortmass", r"#font[132]{m_{K_{S}}} [GeV]", 0.427, 0.577)
Lambdamass = RooRealVar("Lambdamass", r"#font[132]{m_{p#pi}} [GeV]", 1., 1.5)
Q2 = RooRealVar("Q2", r"#font[12]{q^{2}} [GeV^{2}]", 0.5, 20.)
Triggers = RooRealVar("Triggers", "", 0, 100)
dataArgs = RooArgSet(
    Bmass,
    CosThetaK,
    CosThetaL)
dataArgs.add(Mumumass)
dataArgs.add(Mumumasserr)
dataArgs.add(Kstarmass)
dataArgs.add(Kshortmass)
dataArgs.add(Lambdamass)
dataArgs.add(Q2)
dataArgs.add(Triggers)

genCosThetaK = RooRealVar("genCosThetaK", r"#font[132]{cos} #font[12]{#theta_{K}}", -1., 1.)
genCosThetaL = RooRealVar("genCosThetaL", r"#font[132]{cos} #font[12]{#theta_{l}}", -1., 1.)
genQ2 = RooRealVar("genQ2", r"#font[12]{q^{2}} [GeV^{2}]", 0.5, 20.)
dataArgsGEN = RooArgSet(
    genQ2,
    genCosThetaK,
    genCosThetaL)
