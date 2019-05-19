#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 et:

from __future__ import print_function

import os
import shutil
import shelve

import ROOT
from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.anaSetup import q2bins, modulePath

class FitDBPlayer(object):
    "Play with the database generated with shelve"
    funcPair = [
        ('setVal', 'getVal'),
        ('setError', 'getError'),
        ('setAsymError', 'getErrorHi'),  # Positive-definite
        ('setAsymError', 'getErrorLo'),  # Negative-definite
        ('setConstant', 'isConstant'),
        ('setMax', 'getMax'),
        ('setMin', 'getMin')]
    outputfilename = "fitResults.db"

    @staticmethod
    def MergeDB(dblist, mode="Overwrite", outputName="MergedDB.db"):
        """"""
        if mode not in ["Overwrite", "Print", "Skip"]:
            print("Unknown mode for DB merging process. Take default mode.")
            mode = "Overwrite"

        if not all([os.path.exists(f) for f in dblist]):
            return

        for dbfile in dblist:
            if not os.path.exists(outputName):
                shutil.copy(dbfile, outputName)
                outputdb = shelve.open(outputName, writeback=True)
            else:
                db = shelve.open(dbfile)
                if mode == "Overwrite":
                    outputdb.update(db)
                elif mode == "Print" or mode == "Skip":
                    for key, val in db.items():
                        if key in outputdb and mode == "Print":
                            print("Found duplicated key: {0} in {2}".format(key, dbfile))
                        else:
                            outputdb[key] = val
                else:
                    raise NotImplementedError
                db.close()
        outputdb.close()

    @staticmethod
    def UpdateToDB(dbfile, args, aliasDict=None):
        """Update fit result to a db file"""
        if aliasDict is None:
            aliasDict = {}
        try:
            db = shelve.open(dbfile, writeback=True)
            def updateToDBImp(iArg):
                argName = iArg.GetName()
                aliasName = aliasDict.get(argName, argName)
                if aliasName not in db:
                    db[aliasName] = {}
                for setter, getter in FitDBPlayer.funcPair:
                    db[aliasName][getter] = getattr(iArg, getter)()
            FitterCore.ArgLooper(args, updateToDBImp)
        finally:
            db.close()
            print("Updated to Database `{0}`.".format(dbfile))

    @staticmethod
    def initFromDB(dbfile, args, aliasDict=None):
        """Parameter initialization from db file"""
        if not os.path.exists(dbfile):
            return
        if aliasDict is None:
            aliasDict = {}

        try:
            db = shelve.open(dbfile)
            def initFromDBImp(iArg):
                argName = iArg.GetName()
                aliasName = aliasDict.get(argName, argName)
                if aliasName in db:
                    for setter, getter in FitDBPlayer.funcPair:
                        if setter in ["setMax", "setMin"]:
                            continue
                        getattr(iArg, setter)(
                            *{
                                'getErrorHi': (db[aliasName]['getErrorLo'], db[aliasName]['getErrorHi']),
                                'getErrorLo': (db[aliasName]['getErrorLo'], db[aliasName]['getErrorHi']),
                            }.get(getter, (db[aliasName][getter],))
                        )
                else:
                    print("WARNING\t: Unable to initialize {0}, record not found in {1}.".format(aliasName, dbfile))
            FitterCore.ArgLooper(args, initFromDBImp)
            print("Initialized parameters from `{0}`.".format(dbfile))
        finally:
            db.close()

    @staticmethod
    def fluctuateFromDB(dbfile, args, aliasDict=None):
        """ Flucturate certain args from db dbfile"""
        if not os.path.exists(dbfile):
            return
        if aliasDict is None:
            aliasDict = {}

        try:
            db = shelve.open(dbfile)
            gaus = ROOT.TF1("gaus", "exp(-0.5*x**2)", -3, 3)
            def flucturateFromDBImp(iArg):
                argName = iArg.GetName()
                aliasName = aliasDict.get(argName, argName)
                if aliasName in db:
                    significance = gaus.GetRandom()
                    if significance > 0:
                        iArg.setVal(min(iArg.getMax(), iArg.getVal() + significance * iArg.getErrorHi()))
                    else:
                        iArg.setVal(max(iArg.getMin(), iArg.getVal() + significance * iArg.getErrorHi()))
                else:
                    print("ERROR\t: Unable to fluctuate {0}, record not found in {1}.".format(aliasName, dbfile))
            FitterCore.ArgLooper(args, flucturateFromDBImp)
        finally:
            db.close()

def register_dbfile(self, inputDir="{0}/input/selected".format(modulePath)):
    # All fitting steps MUST share the same input db file to ensure consistency of output db file.
    baseDBFile = "{0}/{1}_{2}.db".format(inputDir, os.path.splitext(FitDBPlayer.outputfilename)[0], q2bins[self.process.cfg['binKey']]['label'])
    if not hasattr(self.process, 'odbfilename'):
        self.process.odbfilename = "{0}".format(os.path.basename(baseDBFile))
    if not os.path.exists(self.process.odbfilename) and os.path.exists(baseDBFile):
        shutil.copy(baseDBFile, self.process.odbfilename)
