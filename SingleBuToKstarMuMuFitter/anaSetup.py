#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)

from math import sqrt
from copy import deepcopy

# q2 bins
q2bins = {}
def createBinTemplate(name, lowerBd, upperBd):
    template = {
        'q2range':(lowerBd, upperBd),
        'cutString': "Mumumass > {0} && Mumumass < {1}".format(sqrt(lowerBd), sqrt(upperBd)),
        'label': "{0}".format(name),
        'latexLabel': "{0}".format(name),
    }
    return template

q2bins['belowJpsi'] = createBinTemplate("bin0", 1., 8.68)
q2bins['betweenPeaks'] = createBinTemplate("bin2", 10.09, 12.86)
q2bins['abovePsi2s'] = createBinTemplate("bin4", 14.18, 19.00)
# q2bins['summaryLowQ2'] = createBinTemplate("summaryLowQ2", 1., 6.)
q2bins['summary'] = createBinTemplate("summary", 1., 19.)
q2bins['summary']['cutString'] = "(Mumumass > 1 && Mumumass < 4.35890) && !(Mumumass > 2.94618 && Mumumass < 3.17648) && !(Mumumass > 3.58608 && Mumumass < 3.76563)"

q2bins['jpsi'] = createBinTemplate("jpsi", 8.68, 10.09)
q2bins['psi2s'] = createBinTemplate("psi2s", 12.86, 14.18)
q2bins['peaks'] = createBinTemplate("peaks", 1., 19.)
q2bins['peaks']['cutString'] = "(Mumumass > 2.94618 && Mumumass < 3.17648) || (Mumumass > 3.58608 && Mumumass < 3.76563)"

# B mass regions
bMassRegions = {}
def createBmassTemplate(name, lowerBd, upperBd):
    template = {
        'range':(lowerBd, upperBd),
        'cutString': "Bmass > {0} && Bmass < {1}".format(lowerBd, upperBd),
        'label': "{0}".format(name),
    }
    return template

bMassRegions['Fit'] = createBmassTemplate("Fit", 4.76, 5.80)
bMassRegions['SR']  = createBmassTemplate("SR", 5.18, 5.38)
bMassRegions['LSB'] = createBmassTemplate("LSB", 4.76, 5.18)
bMassRegions['USB'] = createBmassTemplate("USB", 5.38, 5.80)
bMassRegions['SB']  = createBmassTemplate("SB", 4.76, 5.80)
bMassRegions['SB']['cutString'] = "({0}) && !({1})".format(bMassRegions['SB']['cutString'], bMassRegions['SR']['cutString'])

# Cut strings
cut_passTrigger = "Triggers >= 1"
cut_kstarMassWindow = "Kstarmass>0.792 && Kstarmass < 0.992"
cut_resonanceRej = "(Mumumass > 3.096916+3.5*Mumumasserr || Mumumass < 3.096916-5.5*Mumumasserr) && (Mumumass > 3.686109+3.5*Mumumasserr || Mumumass < 3.686109-3.5*Mumumasserr)"
cut_antiRadiation = "abs(Bmass-Mumumass-2.182)>0.09 && abs(Bmass-Mumumass-1.593)>0.03"
cuts = [
    cut_passTrigger,
    cut_kstarMassWindow,
    cut_resonanceRej,
    cut_antiRadiation,
]
cuts.append("({0})".format(")&&(".join(cuts)))

# Developers Area
isDEBUG = True
    # Unit test
if isDEBUG:
    q2bins['test'] = q2bins['summary']
    bMassRegions['test'] = bMassRegions['Fit']
