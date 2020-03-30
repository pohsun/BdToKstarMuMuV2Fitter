#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)


from __future__ import print_function, division
import os
from math import sqrt

# Shared global settings
modulePath = os.path.abspath(os.path.dirname(__file__))

# q2 bins
q2bins = {}
def createBinTemplate(name, lowerBd, upperBd):
    template = {
        'q2range': (lowerBd, upperBd),
        'cutString': "Mumumass > {0} && Mumumass < {1}".format(sqrt(lowerBd), sqrt(upperBd)),
        'label': "{0}".format(name),
        'latexLabel': "{upperBd:.2f} > q^{{2}} > {lowerBd:.2f}".format(upperBd=upperBd, lowerBd=lowerBd),
    }
    return template

q2bins['belowJpsi'] = createBinTemplate("bin1", 1., 8.68)
q2bins['betweenPeaks'] = createBinTemplate("bin3", 10.09, 12.86)
q2bins['abovePsi2s'] = createBinTemplate("bin5", 14.18, 19.00)
# q2bins['summaryLowQ2'] = createBinTemplate("summaryLowQ2", 1., 6.)
q2bins['summary'] = createBinTemplate("bin0", 1., 19.)
q2bins['summary']['cutString'] = "(Mumumass > 1 && Mumumass < 4.35890) && !(Mumumass > 2.94618 && Mumumass < 3.17648) && !(Mumumass > 3.58608 && Mumumass < 3.76563)"

q2bins['jpsi'] = createBinTemplate("bin2", 8.68, 10.09)
q2bins['jpsiLo'] = createBinTemplate("bin2a", 8.68, 9.37)
q2bins['jpsiHi'] = createBinTemplate("bin2b", 9.37, 10.09)
q2bins['psi2s'] = createBinTemplate("bin4", 12.86, 14.18)
q2bins['peaks'] = createBinTemplate("peaks", 1., 19.)
q2bins['peaks']['cutString'] = "(Mumumass > 2.94618 && Mumumass < 3.17648) || (Mumumass > 3.58608 && Mumumass < 3.76563)"
q2bins['full'] = createBinTemplate("full", 1., 19.)

    # SM prediction
q2bins['belowJpsi']['sm'] = {
    'afb': {
        'getVal': 0.077,
        'getError': 0.097,
    },
    'fl': {
        'getVal': 0.673,
        'getError': 0.306,
    }
}
q2bins['abovePsi2s']['sm'] = {
    'afb': {
        'getVal': 0.366,
        'getError': 0.030,
    },
    'fl': {
        'getVal': 0.346,
        'getError': 0.035,
    }
}

# B mass regions
bMassRegions = {}
def createBmassTemplate(name, lowerBd, upperBd):
    template = {
        'range': (lowerBd, upperBd),
        'cutString': "Bmass > {0} && Bmass < {1}".format(lowerBd, upperBd),
        'label': "{0}".format(name),
    }
    return template

bMassRegions['Full'] = createBmassTemplate("Full", 4.5, 6.00) # Cut off below 4.68
bMassRegions['Fit'] = createBmassTemplate("Fit", 4.76, 5.80) # Cut off below 4.68
bMassRegions['SR'] = createBmassTemplate("SR", 5.18, 5.38)
bMassRegions['LSB'] = createBmassTemplate("LSB", 4.76, 5.18)
bMassRegions['USB'] = createBmassTemplate("USB", 5.38, 5.80)
bMassRegions['SB'] = createBmassTemplate("SB", 4.76, 5.80)
bMassRegions['SB']['cutString'] = "({0}) && !({1})".format(bMassRegions['SB']['cutString'], bMassRegions['SR']['cutString'])

bMassRegions['innerLSB'] = createBmassTemplate("innerLSB", 4.97, 5.18)
bMassRegions['innerUSB'] = createBmassTemplate("innerUSB", 5.38, 5.59)
bMassRegions['innerSB'] = createBmassTemplate("innerSB", 4.97, 5.59)
bMassRegions['innerSB']['cutString'] = "({0}) && !({1})".format(bMassRegions['innerSB']['cutString'], bMassRegions['SR']['cutString'])

bMassRegions['outerLSB'] = createBmassTemplate("outerLSB", 4.76, 4.97)
bMassRegions['outerUSB'] = createBmassTemplate("outerUSB", 5.59, 5.80)
bMassRegions['outerSB'] = createBmassTemplate("outerSB", 4.76, 5.80)
bMassRegions['outerSB']['cutString'] = "({0}) && !({1})".format(bMassRegions['outerSB']['cutString'], "Bmass > 4.97 && Bmass < 5.59")

# Systematics
bMassRegions['altFit'] = createBmassTemplate("altFit", 4.68, 5.88)
bMassRegions['altSR'] = createBmassTemplate("altSR", 5.18, 5.38)
bMassRegions['altLSB'] = createBmassTemplate("altLSB", 4.68, 5.18)
bMassRegions['altUSB'] = createBmassTemplate("altUSB", 5.38, 5.88)
bMassRegions['altSB'] = createBmassTemplate("altSB", 4.68, 5.88)
bMassRegions['altSB']['cutString'] = "({0}) && !({1})".format(bMassRegions['altSB']['cutString'], bMassRegions['altSR']['cutString'])

bMassRegions['altFit_vetoJpsiX'] = createBmassTemplate("altFit_vetoJpsiX", 5.18, 5.80)
bMassRegions['altSR_vetoJpsiX'] = createBmassTemplate("altSR_vetoJpsiX", 5.18, 5.38)
bMassRegions['altLSB_vetoJpsiX'] = createBmassTemplate("altLSB_vetoJpsiX", 5.18, 5.18)
bMassRegions['altUSB_vetoJpsiX'] = createBmassTemplate("altUSB_vetoJpsiX", 5.38, 5.80)
bMassRegions['altSB_vetoJpsiX'] = createBmassTemplate("altSB_vetoJpsiX", 4.76, 5.80)
bMassRegions['altSB_vetoJpsiX']['cutString'] = "({0}) && !({1})".format(bMassRegions['altSB_vetoJpsiX']['cutString'], bMassRegions['altSR_vetoJpsiX']['cutString'])

# More tests
bMassRegions['altFit0'] = createBmassTemplate("altFit0", 4.68, 5.88)
bMassRegions['altFit1'] = createBmassTemplate("altFit1", 5.00, 5.64)

# Cut strings
cut_passTrigger = "Triggers >= 1"
cut_kshortWindow = "abs(Kshortmass-0.4975) < 3*0.00576"
cut_kstarMassWindow = "Kstarmass>0.792 && Kstarmass < 0.992"
cut_lambdaVeto = "Lambdamass < 1.11 || Lambdamass > 1.125"
cut_resonanceRej = "(Mumumass > 3.096916+3.5*Mumumasserr || Mumumass < 3.096916-5.5*Mumumasserr) && (Mumumass > 3.686109+3.5*Mumumasserr || Mumumass < 3.686109-3.5*Mumumasserr)"
cut_antiRadiation = "abs(Bmass-Mumumass-2.182)>0.09 && abs(Bmass-Mumumass-1.593)>0.03"
cuts = [
    cut_passTrigger,
    cut_kshortWindow,
    cut_lambdaVeto,
    cut_kstarMassWindow,
    cut_resonanceRej,
    cut_antiRadiation,
]
cuts.append("({0})".format(")&&(".join(cuts)))
cuts_noResVeto = "({0}) && ({1}) && ({2}) && ({3})".format(cut_passTrigger, cut_kshortWindow, cut_lambdaVeto, cut_kstarMassWindow)
cuts_antiResVeto = "({0}) && !({1}) && !({2})".format(cuts_noResVeto, cut_resonanceRej, cut_antiRadiation)

# SM prediction

