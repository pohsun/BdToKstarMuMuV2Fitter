#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=0 fdn=1 et:

from __future__ import print_function

import os
import sys
import re
import math
import glob
import shelve
from subprocess import call
from argparse import ArgumentParser
from multiprocessing import Pool

import ROOT
from SingleBuToKstarMuMuFitter.anaSetup import modulePath, q2bins
from SingleBuToKstarMuMuFitter.StdProcess import dbplayer
from SingleBuToKstarMuMuFitter.StdFitter import unboundFlToFl, unboundAfbToAfb
from SingleBuToKstarMuMuFitter.plotCollection import Plotter

targetBinKeys = ["belowJpsi", "betweenPeaks", "abovePsi2s", "summary"]
targetCoverage = 0.683

def worker_mergeToys(task_dir):
    print("INFO\t: Merge toys from {0}".format(task_dir))
    for binKey in targetBinKeys:
        for fileKey, wspaceKey in [("sigToyGenerator", "f_sig3DData"), ("bkgCombToyGenerator", "f_bkgCombData")]:
            files = glob.glob(args.batchDir + "/" + task_dir + "/*/{0}_{1}.root".format(fileKey, q2bins[binKey]['label']))
            merged_file = args.batchDir + "/" + task_dir + "/{0}_{1}.root".format(fileKey, q2bins[binKey]['label'])
            if os.path.exists(merged_file) and os.path.getsize(merged_file) > 1e3:
                if args.mergeExists:
                    files.append(merged_file)
                else:
                    # print("WARNING\t: A sizable {0}_{1}.root found under {2}. Skip!".format(fileKey, q2bins[binKey]['label'], task_dir))
                    continue

            for fIdx, f in enumerate(files):
                try:
                    fin = ROOT.TFile(f)
                    dataset = fin.Get(wspaceKey)

                    if fIdx == 0:
                        merged_dataset = dataset
                    else:
                        merged_dataset.append(dataset)

                finally:
                    fin.Close()

            if len(files) > 0:
                try:
                    ofile = ROOT.TFile(merged_file, 'RECREATE')
                    #  print("DEBUG\t: Writing {0}_{1}.root under {2}".format(fileKey, q2bins[binKey]['label'], task_dir))
                    merged_dataset.Write()
                finally:
                    ofile.Close()
            else:
                print("WARNING\t: {0}_{1}.root not found under {2}".format(fileKey, q2bins[binKey]['label'], task_dir))

def func_mergeToys(args):
    """Merge produced toys in work_dirs to task_dir"""
    pool = Pool(processes=8)
    pool.map(worker_mergeToys,
             filter(lambda i: re.match(args.taskDirPatn, i) or re.match("bestFit", i), os.listdir(args.batchDir)))
    pool.close()
    pool.join()

def worker_mergeSetSummary(task_dir):
    for binKey in targetBinKeys:
        fileKey = "setSummary"
        files = glob.glob(args.batchDir + "/" + task_dir + "/*/{0}_{1}.root".format(fileKey, q2bins[binKey]['label']))
        merged_file = args.batchDir + "/" + task_dir + "/{0}_{1}.root".format(fileKey, q2bins[binKey]['label'])

        if os.path.exists(merged_file):
            print("WARNING\t: {0} exists. Skip!".format(merged_file))
        elif len(files) > 0:
            call(["hadd", merged_file] + files)
        else:
            print("WARNING\t: {0}_{1}.root not found under {2}".format(fileKey, q2bins[binKey]['label'], task_dir))

def func_mergeSetSummary(args):
    """Merge produced toys in work_dirs to task_dir"""
    pool = Pool(processes=8)
    pool.map(worker_mergeSetSummary,
             filter(lambda i: re.match(args.taskDirPatn, i) or re.match("bestFit", i), os.listdir(args.batchDir)))
    pool.close()
    pool.join()
    os.system("ls -l " + args.batchDir + "/*/setSummary_*.root")
    print("INFO\t: Please check the merged filesize makes sense, and then delete work_dirs.")

def func_getFCConfInterval(args):
    """Create FCConfInterval.root from setSummary.root"""
    for binKey in targetBinKeys:
        foutName = args.batchDir + "/FCConfInterval_{0}.root".format(q2bins[binKey]['label'])
        if not os.path.exists(foutName):
            fout = ROOT.TFile(foutName, 'RECREATE')
            afbFitResults = {}
            flFitResults = {}
            for taskDir in filter(lambda i: re.match(r'(afb|fl)([+-]0\.\d{3})', i), os.listdir(args.batchDir)):
                parseTaskDir = re.match(r'(afb|fl)([+-]0\.\d{3})', taskDir)
                varName = parseTaskDir.group(1)
                varVal = float(parseTaskDir.group(2))
                setTag = "{0}{1:+04.0f}".format(varName, 1000 * varVal)
                try:
                    fin = ROOT.TFile(args.batchDir + "/" + taskDir + "/setSummary_{0}.root".format(q2bins[binKey]['label']))
                    tree = fin.Get("tree")
                    if not tree:
                        print("WARNING\t: Unable to find the tree in " + args.batchDir + "/" + taskDir + "/setSummary_{0}.root".format(q2bins[binKey]['label']))
                        continue

                    if varName == "afb":
                        pdf = ROOT.TF1("pdf_{0}".format(setTag), "gaus(0)+[3]*exp(-0.5*(x/[4])**2)+[5]*exp(-0.5*((x-0.745)/[6])**2)+[7]*exp(-0.5*((x+0.745)/[8])**2)", -0.75, 0.75)
                        pdf.SetParameter(1, varVal)
                        pdf.SetParameter(2, 0.1)
                        pdf.SetParameter(3, 10)
                        pdf.SetParameter(4, 0.002)
                        pdf.SetParameter(6, 0.002)
                        pdf.SetParameter(8, 0.002)
                        pdf.SetParLimits(0, 0, 10)
                        pdf.SetParLimits(2, 0.02, 1)
                        pdf.SetParLimits(3, 0., 200)  # spike at boundary
                        pdf.SetParLimits(4, 0.001, 0.02)  # spike at boundary
                        pdf.SetParLimits(5, 0., 200)  # spike at boundary
                        pdf.SetParLimits(6, 0.001, 0.02)  # spike at boundary
                        pdf.SetParLimits(7, 0., 200)  # spike at boundary
                        pdf.SetParLimits(8, 0.001, 0.02)  # spike at boundary
                        hist = ROOT.TH1F("hist_{0}".format(setTag), "", 1500, -0.75, 0.75)
                        afbFitResults[varVal] = {
                            'pdf': pdf,
                            'hist': hist
                        }
                    else:
                        pdf = ROOT.TF1("pdf_{0}".format(setTag), "gaus(0)+[3]*exp(-0.5*(x/[4])**2)+[5]*exp(-0.5*((x-0.995)/[6])**2)", 0, 1)
                        pdf.SetParameter(1, varVal)
                        pdf.SetParameter(2, 0.1)
                        pdf.SetParameter(3, 10)
                        pdf.SetParameter(4, 0.002)
                        pdf.SetParameter(5, 10)
                        pdf.SetParameter(6, 0.002)
                        pdf.SetParLimits(0, 0, 10)
                        pdf.SetParLimits(2, 0.02, 1)
                        pdf.SetParLimits(3, 0., 200)  # spike at boundary
                        pdf.SetParLimits(4, 0.001, 0.02)  # spike at boundary
                        pdf.SetParLimits(5, 0., 200)  # spike at boundary
                        pdf.SetParLimits(6, 0.001, 0.02)  # spike at boundary
                        hist = ROOT.TH1F("hist_{0}".format(setTag), "", 1000, 0, 1)
                        flFitResults[varVal] = {
                            'pdf': pdf,
                            'hist': hist
                        }

                    tree.Draw("{0} >> hist_{1}".format(varName, setTag))
                    hist.SetDirectory(0)  # Decouple hist with fin
                    hist.Scale(1 / hist.GetBinWidth(1) / hist.GetSumOfWeights())
                    hist.Fit(pdf, "RLQ")

                    fout.cd()
                    hist.Write()
                    pdf.Write()
                finally:
                    fin.Close()

            fout.cd() # Associate TGraph and TH1 to a directory.
            
            # Prepare likelihood ratio map for later use
            LRatioAfb = ROOT.TH2F("LRatioAfb", "", 150, -0.75, 0.75, 150, -0.75, 0.75)
            for afbMeas in afbFitResults.keys():
                maxLh = max([afbFitResults[afbTrue]['pdf'].Eval(afbMeas) for afbTrue in afbFitResults.keys()])
                for afbTrue in afbFitResults.keys():
                    LRatioAfb.SetBinContent(LRatioAfb.FindBin(afbMeas, afbTrue), afbFitResults[afbTrue]['pdf'].Eval(afbMeas) / maxLh)
            LRatioAfb.Write()

            LRatioFl = ROOT.TH2F("LRatioFl", "", 100, 0., 1., 100, 0., 1.)
            for flMeas in flFitResults.keys():
                maxLh = max([flFitResults[flTrue]['pdf'].Eval(flMeas) for flTrue in flFitResults.keys()])
                for flTrue in flFitResults.keys():
                    LRatioFl.SetBinContent(LRatioFl.FindBin(flMeas, flTrue), flFitResults[flTrue]['pdf'].Eval(flMeas) / maxLh)
            LRatioFl.Write()

            # Scan confidence interval based on LR
            gr_afbCILo = ROOT.TGraph()
            gr_afbCIHi = ROOT.TGraph()
            for afbTrue in afbFitResults.keys():
                hcdf = afbFitResults[afbTrue]['hist'].GetCumulative()
                cumulativeMax = hcdf.GetBinContent(hcdf.GetNbinsX())
                afbTrueBin = LRatioAfb.GetYaxis().FindBin(afbTrue)
                minAfbBin, maxAfbBin = 1, hcdf.GetNbinsX()
                while (hcdf.GetBinContent(maxAfbBin) - hcdf.GetBinContent(minAfbBin)) / cumulativeMax > targetCoverage:
                    if LRatioAfb.GetBinContent(LRatioAfb.FindBin(hcdf.GetXaxis().GetBinCenter(minAfbBin), afbTrue))\
                            > LRatioAfb.GetBinContent(LRatioAfb.FindBin(hcdf.GetXaxis().GetBinCenter(maxAfbBin), afbTrue)):
                        maxAfbBin -= 1
                    else:
                        minAfbBin += 1
                gr_afbCILo.SetPoint(afbTrueBin, hcdf.GetXaxis().GetBinCenter(minAfbBin), afbTrue)
                gr_afbCIHi.SetPoint(afbTrueBin, hcdf.GetXaxis().GetBinCenter(maxAfbBin), afbTrue)
            gr_afbCILo.Write("gr_afbCILo")
            gr_afbCIHi.Write("gr_afbCIHi")

            gr_flCILo = ROOT.TGraph()
            gr_flCIHi = ROOT.TGraph()
            for flTrue in flFitResults.keys():
                hcdf = flFitResults[flTrue]['hist'].GetCumulative()
                cumulativeMax = hcdf.GetBinContent(hcdf.GetNbinsX())
                flTrueBin = LRatioFl.GetYaxis().FindBin(flTrue)
                minFlBin, maxFlBin = 1, hcdf.GetNbinsX()
                while (hcdf.GetBinContent(maxFlBin) - hcdf.GetBinContent(minFlBin)) / cumulativeMax > targetCoverage:
                    if LRatioFl.GetBinContent(LRatioFl.FindBin(hcdf.GetXaxis().GetBinCenter(minFlBin), flTrue))\
                            > LRatioFl.GetBinContent(LRatioFl.FindBin(hcdf.GetXaxis().GetBinCenter(maxFlBin), flTrue)):
                        maxFlBin -= 1
                    else:
                        minFlBin += 1
                gr_flCILo.SetPoint(flTrueBin, hcdf.GetXaxis().GetBinCenter(minFlBin), flTrue)
                gr_flCIHi.SetPoint(flTrueBin, hcdf.GetXaxis().GetBinCenter(maxFlBin), flTrue)
            gr_flCILo.Write("gr_flCILo")
            gr_flCIHi.Write("gr_flCIHi")
            fout.Close()

def filterVeryBiasedPoint(gr, nSigma=1):
    """Clean very biased point in TGraph"""
    h1 = ROOT.TH1F("h1", "", 100, -5, 5)
    trueVal = ROOT.Double()
    measVal = ROOT.Double()
    for iP in range(gr.GetN()):
        gr.GetPoint(iP, measVal, trueVal)
        h1.Fill(measVal - trueVal)
    f1 = ROOT.TF1("f1", "gaus(0)", -5, 5)
    fitR = h1.Fit(f1, "SML", "", -1, 1)
    fitR_mean = fitR.GetParams()[1]
    fitR_width = fitR.GetParams()[2]
    for iP in range(gr.GetN()):
        gr.GetPoint(iP, measVal, trueVal)
        if math.fabs(measVal - trueVal - fitR_mean) > nSigma * fitR_width:
            gr.RemovePoint(iP)
    return gr

def func_fitFCConfInterval(args):
    """Fit interval from FCConfInterval.root, make plots and save to database."""
    line = ROOT.TLine()
    line.SetLineColor(2)
    line.SetLineStyle(2)

    for binKey in targetBinKeys:
        def drawAfbPlot(grLo, grHi, measAfb):
            grLo.SetTitle("")
            grLo.GetXaxis().SetTitle("Measured A_{FB}")
            grLo.GetXaxis().SetLimits(-0.75, 0.75)
            grLo.GetYaxis().SetTitle("True A_{FB}")
            grLo.GetYaxis().SetRangeUser(-0.75, 0.75)
            grLo.SetMarkerStyle(7)
            grHi.SetMarkerStyle(7)
            grLo.SetMarkerSize(0.4)
            grHi.SetMarkerSize(0.4)
            grLo.SetMarkerColor(8)
            grHi.SetMarkerColor(9)
            grLo.Draw("AP")
            grHi.Draw("P SAME")
            line.DrawLine(measAfb, -0.75, measAfb, 0.75)
            Plotter.latexCMSMark()
            Plotter.latexCMSExtra()
            Plotter.latexLumi()

        def drawFlPlot(grLo, grHi, measFl):
            grLo.SetTitle("")
            grLo.GetXaxis().SetTitle("Measured F_{L}")
            grLo.GetXaxis().SetLimits(0, 1)
            grLo.GetYaxis().SetTitle("True F_{L}")
            grLo.GetYaxis().SetRangeUser(0, 1)
            grLo.SetMarkerStyle(7)
            grHi.SetMarkerStyle(7)
            grLo.SetMarkerSize(0.4)
            grHi.SetMarkerSize(0.4)
            grLo.SetMarkerColor(8)
            grHi.SetMarkerColor(9)
            grLo.Draw("AP")
            grHi.Draw("P SAME")
            line.DrawLine(measFl, 0, measFl, 1)
            Plotter.latexCMSMark()
            Plotter.latexCMSExtra()
            Plotter.latexLumi()

        dbName = args.dbDirPath + "/fitResults_{0}.db".format(q2bins[binKey]['label'])
        print("Work with DB file: {0}".format(dbName))
        db = shelve.open(dbName, writeback=True if args.saveToDB else False)
        fl = unboundFlToFl(db['unboundFl']['getVal'])
        afb = unboundAfbToAfb(db['unboundAfb']['getVal'], fl)
        fin = ROOT.TFile(args.batchDir + "/FCConfInterval_{0}.root".format(q2bins[binKey]['label']))
        gr_afbCILo = filterVeryBiasedPoint(fin.Get("gr_afbCILo"))
        gr_afbCIHi = filterVeryBiasedPoint(fin.Get("gr_afbCIHi"))
        gr_flCILo = filterVeryBiasedPoint(fin.Get("gr_flCILo"))
        gr_flCIHi = filterVeryBiasedPoint(fin.Get("gr_flCIHi"))

        bdWidth = 0.01
        intervalBias = 0.
        intervalRange = 0.1
        afb_fitRange = {
            'Lo': {
                'default': (max(-0.75 + bdWidth, afb + intervalBias - intervalRange),
                            min(0.75 - bdWidth, afb + intervalBias + intervalRange)),
                'belowJpsi': (-0.2, 0),
            },
            'Hi': {
                'default': (max(-0.75 + bdWidth, afb - intervalBias - intervalRange),
                            min(0.75 - bdWidth, afb - intervalBias + intervalRange)),
            }
        }

        f_local_afbCILo = ROOT.TF1("f_local_afbCILo", "[0]+[1]*x", -0.75 + bdWidth, 0.75 - bdWidth)
        f_local_afbCIHi = ROOT.TF1("f_local_afbCIHi", "[0]+[1]*x", -0.75 + bdWidth, 0.75 - bdWidth)
        r_local_afbCILo = gr_afbCILo.Fit(f_local_afbCILo, "SWM", "", *afb_fitRange['Lo'].get(binKey, afb_fitRange['Lo']['default']))
        r_local_afbCIHi = gr_afbCIHi.Fit(f_local_afbCIHi, "SWM", "", *afb_fitRange['Lo'].get(binKey, afb_fitRange['Lo']['default']))
        drawAfbPlot(gr_afbCILo, gr_afbCIHi, afb)
        stat_FC_afb_getErrorHi = f_local_afbCILo.Eval(afb) - afb
        stat_FC_afb_getErrorLo = f_local_afbCIHi.Eval(afb) - afb
        Plotter.latex.DrawLatexNDC(.19, .77, "A_{{FB}} = {0:.2f}^{{{1:+.2f}}}_{{{2:+.2f}}}".format(afb, stat_FC_afb_getErrorHi, stat_FC_afb_getErrorLo))
        Plotter.canvas.Print(args.batchDir + "/FCConfInterval_afb_local_{0}.pdf".format(q2bins[binKey]['label']))

        # For later coverage test
        intervalBias = 0.
        intervalRange = 0.1
        fl_fitRange = {
            'Lo': {
                'default': (max(0 + bdWidth, fl + intervalBias - intervalRange),
                            min(1 - bdWidth, fl + intervalBias + intervalRange)),
            },
            'Hi': {
                'default': (max(0 + bdWidth, fl - intervalBias - intervalRange),
                            min(1 - bdWidth, fl - intervalBias + intervalRange)),
            }
        }

        f_local_flCILo = ROOT.TF1("f_local_flCILo", "[0]+[1]*x", 0 + bdWidth, 1 - bdWidth)
        f_local_flCIHi = ROOT.TF1("f_local_flCIHi", "[0]+[1]*x", 0 + bdWidth, 1 - bdWidth)
        r_local_flCILo = gr_flCILo.Fit(f_local_flCILo, "SWM", "", *fl_fitRange['Lo'].get(binKey, fl_fitRange['Lo']['default']))
        r_local_flCIHi = gr_flCIHi.Fit(f_local_flCIHi, "SWM", "", *fl_fitRange['Hi'].get(binKey, fl_fitRange['Hi']['default']))
        drawFlPlot(gr_flCILo, gr_flCIHi, fl)
        stat_FC_fl_getErrorHi = f_local_flCILo.Eval(fl) - fl
        stat_FC_fl_getErrorLo = f_local_flCIHi.Eval(fl) - fl
        Plotter.latex.DrawLatexNDC(.19, .77, "F_{{L}} = {0:.2f}^{{{1:+.2f}}}_{{{2:+.2f}}}".format(fl, stat_FC_fl_getErrorHi, stat_FC_fl_getErrorLo))
        Plotter.canvas.Print(args.batchDir + "/FCConfInterval_fl_local_{0}.pdf".format(q2bins[binKey]['label']))

        # For later coverage test
        # Coverage test if bestFit dir exists
        stat_FC_afb_coverage = 0.
        stat_FC_fl_coverage = 0.
        if args.doCoverage and os.path.exists(args.batchDir + "/bestFit/setSummary_{0}.root".format(q2bins[binKey]['label'])):
            f_global_afbCILo = ROOT.TF1("f_global_afbCILo", "[0]+[1]*x+[2]*x**2", -0.75 + bdWidth, 0.75 - bdWidth)
            f_global_afbCIHi = ROOT.TF1("f_global_afbCIHi", "[0]+[1]*x+[2]*x**2", -0.75 + bdWidth, 0.75 - bdWidth)
            r_global_afbCILo = gr_afbCILo.Fit(f_global_afbCILo, "SWMR")
            r_global_afbCIHi = gr_afbCIHi.Fit(f_global_afbCIHi, "SWMR")

            f_global_flCILo = ROOT.TF1("f_global_flCILo", "[0]+[1]*x+[2]*x**2", 0 + bdWidth, 1 - bdWidth)
            f_global_flCIHi = ROOT.TF1("f_global_flCIHi", "[0]+[1]*x+[2]*x**2", 0 + bdWidth, 1 - bdWidth)
            r_global_flCILo = gr_flCILo.Fit(f_global_flCILo, "SWMR")
            r_global_flCIHi = gr_flCIHi.Fit(f_global_flCIHi, "SWMR")

            fin_bestFit = ROOT.TFile(args.batchDir + "/bestFit/setSummary_{0}.root".format(q2bins[binKey]['label']))
            tree_bestFit = fin_bestFit.Get("tree")
            for ev in tree_bestFit:
                if f_global_afbCILo.Eval(ev.afb) > afb > f_global_afbCIHi.Eval(ev.afb):
                    stat_FC_afb_coverage += 1.
                if f_global_flCILo.Eval(ev.fl) > fl > f_global_flCIHi.Eval(ev.fl):
                    stat_FC_fl_coverage += 1.
            stat_FC_afb_coverage /= tree_bestFit.GetEntries()
            stat_FC_fl_coverage /= tree_bestFit.GetEntries()
            fin.Close()

            drawAfbPlot(gr_afbCILo, gr_afbCIHi, afb)
            Plotter.latex.DrawLatexNDC(.19, .77, "A_{{FB}} = {0:.2f}^{{{1:+.2f}}}_{{{2:+.2f}}}".format(afb, stat_FC_afb_getErrorHi, stat_FC_afb_getErrorLo))
            # Plotter.latex.DrawLatexNDC(.19, .70, "Coverage: {0:.1f}%".format(100*stat_FC_afb_coverage))
            Plotter.canvas.Print(args.batchDir + "/FCConfInterval_afb_global_{0}.pdf".format(q2bins[binKey]['label']))

            drawFlPlot(gr_flCILo, gr_flCIHi, fl)
            Plotter.latex.DrawLatexNDC(.19, .77, "F_{{L}} = {0:.2f}^{{{1:+.2f}}}_{{{2:+.2f}}}".format(fl, stat_FC_fl_getErrorHi, stat_FC_fl_getErrorLo))
            # Plotter.latex.DrawLatexNDC(.19, .70, "Coverage: {0:.1f}%".format(100*stat_FC_fl_coverage))
            Plotter.canvas.Print(args.batchDir + "/FCConfInterval_fl_global_{0}.pdf".format(q2bins[binKey]['label']))

        if args.saveToDB:
            db['stat_FC_afb'] = {
                'getErrorHi': stat_FC_afb_getErrorHi,
                'getErrorLo': stat_FC_afb_getErrorLo,
            }
            db['stat_FC_fl'] = {
                'getErrorHi': stat_FC_fl_getErrorHi,
                'getErrorLo': stat_FC_fl_getErrorLo,
            }
            if stat_FC_afb_coverage != 0 and stat_FC_fl_coverage != 0:
                db['stat_FC_afb']['coverage'] = stat_FC_afb_coverage
                db['stat_FC_fl']['coverage'] = stat_FC_fl_coverage
            print(db['stat_FC_afb'])
            print(db['stat_FC_fl'])

        db.close()
        fin.Close()

if __name__ == '__main__':
    parser = ArgumentParser(
        description="""Postprocessing after batch task is done."""
    )
    parser.add_argument(
        '-d', '--batchDir',
        dest="batchDir",
        default="{0}/batchTask_profiledFeldmanCousins".format(modulePath),
        help="Directory of the batch task",
    )

    parser.add_argument(
        '-t', '--taskDirPatn',
        dest="taskDirPatn",
        default=r"^(afb|fl)[+-]0\.\d{3}$",
        help="Regex pattern of task_dir under batchDir",
    )

    parser.add_argument(
        '-w', '--workDirPatn',
        dest="workDirPatn",
        default=r"^toys_UTC-\d{8}-\d{6}$",
        help="Regex pattern of task_dir under batchDir",
    )

    subparsers = parser.add_subparsers(help='Functions', dest='Function_name')
    subparser_mergeToys = subparsers.add_parser('mergeToys')
    subparser_mergeToys.add_argument(
        '-m', '--mergeExists',
        dest="mergeExists",
        action='store_true',  # By default, no merge just overwrite.
        help="If merged file exists, merge them. (Default: False)"
    )
    subparser_mergeToys.set_defaults(func=func_mergeToys)

    subparser_mergeSetSummary = subparsers.add_parser('mergeSetSummary')
    subparser_mergeSetSummary.set_defaults(func=func_mergeSetSummary)

    subparser_getFCConfInterval = subparsers.add_parser('getFCConfInterval')
    subparser_getFCConfInterval.set_defaults(func=func_getFCConfInterval)

    subparser_fitFCConfInterval = subparsers.add_parser('fitFCConfInterval')
    subparser_fitFCConfInterval.set_defaults(func=func_fitFCConfInterval)
    subparser_fitFCConfInterval.add_argument(
        '-s', '--saveToDB',
        dest="saveToDB",
        action='store_true',
        help="Save estimated error to DB. (Default: False)"
    )
    subparser_fitFCConfInterval.add_argument(
        '--dbDirPath',
        dest="dbDirPath",  # By default, no merge just overwrite.
        default=dbplayer.absInputDir,
        help="Customize input dir of db files."
    )
    subparser_fitFCConfInterval.add_argument(
        '-c', '--coverageTest',
        dest="doCoverage",
        action='store_true',
        help="Run coverage test. (Default: False)"
    )

    args = parser.parse_args()
    args.func(args)

    sys.exit()
