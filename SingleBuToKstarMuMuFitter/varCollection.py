#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : Shared object definition.

from ROOT import RooRealVar
from ROOT import RooArgSet

Bmass = RooRealVar("Bmass","m_{K^{*}#mu#mu} [GeV]", 4.76, 5.80)
CosThetaK = RooRealVar("CosThetaK", "cos#theta_{K}", -1., 1.)
CosThetaL = RooRealVar("CosThetaL", "cos#theta_{l}", -1., 1.)
Mumumass = RooRealVar("Mumumass", "m_{#mu#mu} [GeV]", 0., 10.)
Mumumasserr = RooRealVar("Mumumasserr", "Error of m_{#mu#mu} [GeV]", 0., 10.)
Kstarmass = RooRealVar("Kstarmass", "m_{K^{*}} [GeV]", 0, 1.5)
Kshortmass = RooRealVar("Kshortmass", "m_{K_{S}} [GeV]", 0.427, 0.577)
Lambdamass = RooRealVar("Lambdamass", "m_{p#pi} [GeV]", 1., 1.5)
Q2 = RooRealVar("Q2", "q^{2} [GeV^{2}]", 0.5, 20.)
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

genCosThetaK = RooRealVar("genCosThetaK", "cos#theta_{K}", -1., 1.)
genCosThetaL = RooRealVar("genCosThetaL", "cos#theta_{l}", -1., 1.)
genQ2 = RooRealVar("genQ2", "q^{2} [GeV^{2}]", 0.5, 20.)
dataArgsGEN = RooArgSet(
    genQ2,
    genCosThetaK,
    genCosThetaL)
