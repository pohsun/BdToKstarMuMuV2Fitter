#!/usr/bin/env python
# vim: set sw=4 sts=4 fdm=indent fdl=0 fdn=3 nopaste et:

from __future__ import print_function

import os
import math
import shelve
from collections import OrderedDict

import ROOT
import SingleBuToKstarMuMuFitter.cpp

from SingleBuToKstarMuMuFitter.anaSetup import q2bins, modulePath
from SingleBuToKstarMuMuFitter.StdFitter import unboundFlToFl, unboundAfbToAfb
from SingleBuToKstarMuMuFitter.StdProcess import p

# For developers:
#   * Input db is forced to be StdProcess.dbplayer.absInputDir
#   * function name for labelled table is table_label1[_label2]


db_dir = p.dbplayer.absInputDir

indent = "  "

def table_AN_sysFL_sysAFB():
    baseIndentLevel = 2
    for var in ["fl", "afb"]:
        dbKeyToLine = OrderedDict()
        dbKeyToLine['syst_randEffi'] = [r"MC statistical uncertainty"]
        dbKeyToLine['syst_simMismodel'] = [r"Simulation mismodelling"]
        dbKeyToLine['syst_bkgCombShape'] = [r"Combinatorial Background shape"]
        dbKeyToLine['syst_altSP'] = [r"$S$-$P$ wave interference"]
        # dbKeyToLine['syst_dataMCDisc'] = [r"Data-MC discrepancy"] # Ignore due to low contribution
        totalErrorLine = ["Total"]
        for binKey in ['belowJpsi', 'betweenPeaks', 'abovePsi2s', 'summary']:
            db = shelve.open("{0}/fitResults_{1}.db".format(db_dir, q2bins[binKey]['label']))
            totalSystErr = 0.
            for systKey, latexLine in dbKeyToLine.items():
                err = db["{0}_{1}".format(systKey, var)]['getError']
                latexLine.append("{0:.03f}".format(err))
                totalSystErr += pow(err, 2)
            db.close()
            totalErrorLine.append("{0:.03f}".format(math.sqrt(totalSystErr)))

        print("[table_AN_sysFL_sysAFB] Printing table of syst. unc. for {0}".format(var))
        print("")
        print(indent * (baseIndentLevel + 0) + r"\begin{tabular}{|l|c|c|c|c|}")
        print(indent * (baseIndentLevel + 1) + r"\hline")
        print(indent * (baseIndentLevel + 1) + r"Syst.\ err.\ $\backslash$ $q^2$ bin & 1 & 3 & 5 & 0 \\")
        print(indent * (baseIndentLevel + 1) + r"\hline")
        print(indent * (baseIndentLevel + 1) + r"\hline")
        print(indent * (baseIndentLevel + 1) + r"\multicolumn{5}{|c|}{Uncorrelated systematic uncertainties} \\")
        print(indent * (baseIndentLevel + 1) + r"\hline")
        for systKey, latexLine in dbKeyToLine.items():
            print(indent * (baseIndentLevel + 1) + " & ".join(latexLine) + r" \\")
        print(indent * (baseIndentLevel + 1) + r"\hline")
        print(indent * (baseIndentLevel + 1) + " & ".join(totalErrorLine) + r" \\")
        print(indent * (baseIndentLevel + 1) + r"\hline")
        print(indent * (baseIndentLevel + 0) + r"\end{tabular}")
        print("")

def table_AN_yields(): # Not used anymore
    baseIndentLevel = 2
    print("[table_AN_yields] Printing table of yields")
    print("")
    print(indent * (baseIndentLevel + 0) + r"\begin{tabular}{|c|c|c|}")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 1) + r"$q^2$ bin & $Y_S$ & $Y^C_B$ \\")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 1) + r"\hline")

    binKeyToLine = OrderedDict()
    binKeyToLine['belowJpsi'] = ["1"]
    binKeyToLine['betweenPeaks'] = ["3"]
    binKeyToLine['abovePsi2s'] = ["5"]
    binKeyToLine['summary'] = ["0"]
    for binKey, latexLine in binKeyToLine.items():
        db = shelve.open("{0}/fitResults_{1}.db".format(db_dir, q2bins[binKey]['label']))
        latexLine.append("${0:.01f} \pm {1:.01f}$".format(db['nSig']['getVal'], db['nSig']['getError']))
        latexLine.append("${0:.01f} \pm {1:.01f}$".format(db['nBkgComb']['getVal'], db['nBkgComb']['getError']))
        db.close()
        print(indent * (baseIndentLevel + 1) + " & ".join(latexLine) + r" \\")

    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 0) + r"\end{tabular}")
    print("")

def table_AN_coverageAFBFL():
    baseIndentLevel = 2
    print("[table_AN_coverageAFBFL] Printing table of stat error coverage")
    print("")
    print(indent * (baseIndentLevel + 0) + r"\begin{tabular}{|c|c|c|}")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 1) + r"$q^2$ bin & $A_{FB}$ & $F_{L}$ \\")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 1) + r"\hline")

    binKeyToLine = OrderedDict()
    binKeyToLine['belowJpsi'] = ["1"]
    binKeyToLine['betweenPeaks'] = ["3"]
    binKeyToLine['abovePsi2s'] = ["5"]
    binKeyToLine['summary'] = ["0"]
    for binKey, latexLine in binKeyToLine.items():
        db = shelve.open("{0}/fitResults_{1}.db".format(db_dir, q2bins[binKey]['label']))
        latexLine.append("{0:.1f}\%".format(db['stat_FC_afb']['coverage'] * 100.))
        latexLine.append("{0:.1f}\%".format(db['stat_FC_fl']['coverage'] * 100.))
        db.close()
        print(indent * (baseIndentLevel + 1) + " & ".join(latexLine) + r" \\")

    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 0) + r"\end{tabular}")
    print("")

def table_AN_dataresAFBFL():
    baseIndentLevel = 2

    print("[table_AN_dataresAFBFL] Printing table of final result")
    print("")
    print(indent * (baseIndentLevel + 0) + r"\begin{tabular}{|c|c|c|c|c|}")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 1) + r"$q^2$ bin index & $q^2$ range (in $\GeV^2$) & Signal Yield & $A_{FB}$ & $F_{L}$ \\")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 1) + r"\hline")

    binKeyToLine = OrderedDict()
    binKeyToLine['belowJpsi'] = ["1", r"1.00 -- 8.68"]
    binKeyToLine['jpsi'] = ["2", r"8.68 -- 10.09", r"\multicolumn{3}{|c|} {$\JPsi$ resonance region}"]
    binKeyToLine['betweenPeaks'] = ["3", r"10.09 -- 12.86"]
    binKeyToLine['psi2s'] = ["4", r"12.86 -- 14.18", r"\multicolumn{3}{|c|} {$\psi'$ resonance region}"]
    binKeyToLine['abovePsi2s'] = ["5", r"14.18 -- 19.00"]
    binKeyToLine['summary'] = ["0", r"bin\#1 $+$ bin\#3 $+$ bin\#5"]

    syst_sources = [
        'syst_randEffi',
        'syst_simMismodel',
        'syst_bkgCombShape',
        'syst_altSP',
    ]
    for binKey, latexLine in binKeyToLine.items():
        if binKey not in ['jpsi', 'psi2s']:
            db = shelve.open(r"{0}/fitResults_{1}.db".format(db_dir, q2bins[binKey]['label']))
            latexLine.append(r"${0:.01f} \pm {1:.01f}$".format(db['nSig']['getVal'], db['nSig']['getError']))
            fl = unboundFlToFl(db['unboundFl']['getVal'])
            latexLine.append("${0:.2f}^{{{1:+.2f}}}_{{{2:+.2f}}} \pm {3:.2f}$".format(
                unboundAfbToAfb(db['unboundAfb']['getVal'], fl),
                db['stat_FC_afb']['getErrorHi'],
                db['stat_FC_afb']['getErrorLo'],
                math.sqrt(sum([pow(db[v + '_afb']['getError'], 2) for v in syst_sources]))))
            latexLine.append("${0:.2f}^{{{1:+.2f}}}_{{{2:+.2f}}} \pm {3:.2f}$".format(
                fl,
                db['stat_FC_fl']['getErrorHi'],
                db['stat_FC_fl']['getErrorLo'],
                math.sqrt(sum([pow(db[v + '_fl']['getError'], 2) for v in syst_sources]))))
            db.close()
        print(indent * (baseIndentLevel + 1) + " & ".join(latexLine) + r" \\")
        print(indent * (baseIndentLevel + 1) + r"\hline")

    print(indent * (baseIndentLevel + 0) + r"\end{tabular}")
    print("")

def table_AN_FinalDataresAFBFL():
    print("[table_FinalDataAFBFL] Printing duplication of dataresAFBFL")
    table_AN_dataresAFBFL()

def table_paper_sys():
    baseIndentLevel = 2
    binKeys = ['belowJpsi', 'betweenPeaks', 'abovePsi2s', 'summary']

    dbKeyToLine = OrderedDict()
    dbKeyToLine['syst_randEffi'] = [r"MC statistical uncertainty"]
    dbKeyToLine['syst_simMismodel'] = [r"Simulation mismodelling"]
    dbKeyToLine['syst_bkgCombShape'] = [r"Combinatorial Background shape"]
    dbKeyToLine['syst_altSP'] = [r"$S$-$P$ wave interference"]
    totalErrorLine = ["Total systematic uncertainty"]
    for var in ["afb", "fl"]:
        for binKey in binKeys:
            db = shelve.open("{0}/fitResults_{1}.db".format(db_dir, q2bins[binKey]['label']))
            totalSystErr = 0.
            for systKey, latexLine in dbKeyToLine.items():
                err = db["{0}_{1}".format(systKey, var)]['getError']
                latexLine.append(err)
                totalSystErr += pow(err, 2)
            db.close()
            totalErrorLine.append(math.sqrt(totalSystErr))

    print("[table_paper_sys] Printing table of syst. unc.")
    print("")
    print(indent * (baseIndentLevel + 0) + r"\begin{tabular}{l|cc}")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 1) + r"Systematic uncertainty & \afb $(10^{-2})$ & \fl $(10^{-2})$ \\")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    for systKey, latexLine in dbKeyToLine.items():
        print(indent * (baseIndentLevel + 1) + latexLine[0] + " & {0:.1f} -- {1:.1f}".format(100. * min(latexLine[1:1 + len(binKeys)]), 100. * max(latexLine[1:1 + len(binKeys)])) + " & {0:.1f} -- {1:.1f}".format(100. * min(latexLine[1 + len(binKeys)::]), 100. * max(latexLine[1 + len(binKeys)::])) + r" \\")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 1) + totalErrorLine[0] + " & {0:.1f} -- {1:.1f}".format(100. * min(totalErrorLine[1:1 + len(binKeys)]), 100. * max(totalErrorLine[1:1 + len(binKeys)])) + " & {0:.1f} -- {1:.1f}".format(100. * min(totalErrorLine[1 + len(binKeys)::]), 100. * max(totalErrorLine[1 + len(binKeys)::])) + r" \\")
    print(indent * (baseIndentLevel + 1) + r"\hline")
    print(indent * (baseIndentLevel + 0) + r"\end{tabular}")
    print("")

def table_paper_results():
    baseIndentLevel = 2

    print("[table_paper_results] Printing table of final result")
    print("")
    print(indent * (baseIndentLevel + 0) + r"\begin{scotch}{cccc}")
    print(indent * (baseIndentLevel + 1) + r"\qq{}(\GeVV) & $Y_{\mathrm{S}}$ & \afb & \fl \\")
    print(indent * (baseIndentLevel + 1) + r"\hline")

    binKeyToLine = OrderedDict()
    binKeyToLine['belowJpsi'] = [r"1.00 -- 8.68"]
    binKeyToLine['betweenPeaks'] = [r"10.09 -- 12.86"]
    binKeyToLine['abovePsi2s'] = [r"14.18 -- 19.00"]
    binKeyToLine['summary'] = [r"1.00 -- 19.00"]

    syst_sources = [
        'syst_randEffi',
        'syst_simMismodel',
        'syst_bkgCombShape',
        'syst_altSP',
    ]
    for binKey, latexLine in binKeyToLine.items():
        if binKey not in ['jpsi', 'psi2s']:
            db = shelve.open(r"{0}/fitResults_{1}.db".format(db_dir, q2bins[binKey]['label']))
            latexLine.append(r"${0:.01f} \pm {1:.01f}$".format(db['nSig']['getVal'], db['nSig']['getError']))
            fl = unboundFlToFl(db['unboundFl']['getVal'])
            latexLine.append("${0:.2f}^{{{1:+.2f}}}_{{{2:+.2f}}} \pm {3:.2f}$".format(
                unboundAfbToAfb(db['unboundAfb']['getVal'], fl),
                db['stat_FC_afb']['getErrorHi'],
                db['stat_FC_afb']['getErrorLo'],
                math.sqrt(sum([pow(db[v + '_afb']['getError'], 2) for v in syst_sources]))))
            latexLine.append("${0:.2f}^{{{1:+.2f}}}_{{{2:+.2f}}} \pm {3:.2f}$".format(
                fl,
                db['stat_FC_fl']['getErrorHi'],
                db['stat_FC_fl']['getErrorLo'],
                math.sqrt(sum([pow(db[v + '_fl']['getError'], 2) for v in syst_sources]))))
            db.close()
        print(indent * (baseIndentLevel + 1) + " & ".join(latexLine) + r" \\")

    print(indent * (baseIndentLevel + 0) + r"\end{scotch}")
    print("")

if __name__ == '__main__':
    table_AN_sysFL_sysAFB()
    table_AN_coverageAFBFL()
    table_AN_dataresAFBFL()
    table_AN_FinalDataresAFBFL()

    table_paper_sys()
    table_paper_results()
    pass
