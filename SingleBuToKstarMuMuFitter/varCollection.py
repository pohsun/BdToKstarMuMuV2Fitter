#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : Shared object definition.
#                   Do not use from ... import ... to bind these objects.
#                   Use copy constructor like a = RooRealVar(common.a).
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 20 Feb 2019 15:06 16:36

from ROOT import RooRealVar
from ROOT import RooArgSet

Bmass = RooRealVar("Bmass","M_{K^{*}#Mu#Mu}", 4.76, 5.80)
CosThetaK = RooRealVar("CosThetaK", "cos#theta_{K}", -1., 1.)
CosThetaL = RooRealVar("CosThetaL", "cos#theta_{L}", -1., 1.)
Mumumass = RooRealVar("Mumumass", "M^{#mu#mu}", 0., 10.)
Mumumasserr = RooRealVar("Mumumasserr", "Error of M^{#mu#mu}", 0., 10.)
Kstarmass = RooRealVar("Kstarmass", "M_{K^{*}}", 0, 1.5)
Q2 = RooRealVar("Q2", "q^{2}", 0.5, 20.)
Triggers = RooRealVar("Triggers", "", 0, 100)
dataArgs = RooArgSet(
    Bmass,
    CosThetaK,
    CosThetaL,
    Mumumass,
    Mumumasserr,
    Kstarmass,
    Q2,
    Triggers)
