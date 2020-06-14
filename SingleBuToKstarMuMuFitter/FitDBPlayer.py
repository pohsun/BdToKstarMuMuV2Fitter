#!/usr/bin/env python
# vim: set sts=4 sw=4 fdm=indent fdl=1 fdn=3 et:

from __future__ import print_function

import os
import sys
import re
import shutil
import shelve
import math

import ROOT
from v2Fitter.FlowControl.Service import Service
from v2Fitter.Fitter.FitterCore import FitterCore
from SingleBuToKstarMuMuFitter.anaSetup import q2bins

class FitDBPlayer(Service):
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

    def __init__(self, absInputDir):
        if not os.path.isabs(absInputDir):
            raise ValueError("In case of batch task, always take absolute path.")
        self.process = None
        self.logger = None
        self.absInputDir = absInputDir
        self.odbfile = None

    @staticmethod
    def PrintDB(dbfile):
        def print_dict(dictionary, ident = '', braces=1):
            """ Recursively prints nested dictionaries. Stolen from http://code.activestate.com/recipes/578094-recursively-print-nested-dictionaries/"""
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    print('%s%s%s%s' %(ident,braces*'[',key,braces*']'))
                    print_dict(value, ident+'  ', braces+1)
                else:
                    print(ident+'%s = %s' %(key, value))
        try:
            db = shelve.open(dbfile)
            print_dict(db)
        finally:
            db.close()
        pass

    @staticmethod
    def MergeDB(dblist, mode="Overwrite", outputName="MergedDB.db"):
        """TODO"""
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
            if isinstance(args, dict):
                modified_args = {}
                for key, val in args.items():
                    aliasName = aliasDict.get(key, key)
                    modified_args[aliasName] = val
                    print("INFO\t: Update {0} as {1} to db.".format(key, aliasName))
                    print(val)
                db.update(modified_args)
            elif args.InheritsFrom("RooArgSet"):
                def updateToDBImp(iArg):
                    argName = iArg.GetName()
                    aliasName = aliasDict.get(argName, argName)
                    if any([val is None and re.match(key, argName) for key, val in aliasDict.items()]):
                        # print("INFO\t: Skip updating {0} to database.".format(argName))
                        pass
                    else:
                        print("INFO\t: Update {0} as {1} to db.".format(argName, aliasName))
                        if aliasName not in db:
                            db[aliasName] = {}
                        for setter, getter in FitDBPlayer.funcPair:
                            try:
                                db[aliasName][getter] = getattr(iArg, getter)()
                            except AttributeError:
                                # In case of no getError for RooNLLVar and so on.
                                pass
                        print(db[aliasName])
                FitterCore.ArgLooper(args, updateToDBImp)
            else:
                raise ValueError("Input arguement of type {0} is not supported".format(type(args)))
        finally:
            db.close()
            print("Updated to Database `{0}`.".format(os.path.abspath(dbfile)))

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
                if any([val is None and re.match(key, argName) for key, val in aliasDict.items()]):
                    print("INFO\t: Skip initializing {0} from database.".format(argName))
                elif aliasName in db:
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
                    print("WARNING\t: Unable to initialize {0}, record {1} not found in {2}.".format(argName, aliasName, dbfile))
            FitterCore.ArgLooper(args, initFromDBImp)
            print("INFO\t: Initialized parameters from `{0}`.".format(os.path.abspath(dbfile)))
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
            print("INFO\t: Parameters are fluctuated to following numbers....")
            def flucturateFromDBImp(iArg):
                argName = iArg.GetName()
                aliasName = aliasDict.get(argName, argName)
                if aliasName in db:
                    significance = gaus.GetRandom()
                    arg = db[aliasName]
                    if significance > 0:
                        iArg.setVal(min(arg['getMax'], arg['getVal'] + significance * (arg['getErrorHi'] if math.fabs(arg['getErrorHi']) > 1e-5 else arg['getError'])))
                    else:
                        iArg.setVal(max(arg['getMin'], arg['getVal'] + significance * (arg['getErrorLo'] if math.fabs(arg['getErrorLo']) > 1e-5 else arg['getError'])))
                    iArg.Print()
                else:
                    print("ERROR\t: Unable to fluctuate {0}, record not found in {1}.".format(aliasName, dbfile))
            FitterCore.ArgLooper(args, flucturateFromDBImp)
        finally:
            db.close()

    def saveSMPrediction(self):
        """ Save SM prediction to DB file. """
        smInDB = {
            'fl_SM': {
                'getVal': None,
                'getError': None,
                'getErrorHi': None,
                'getErrorLo': None,
            },
            'afb_SM': {
                'getVal': None,
                'getError': None,
                'getErrorHi': None,
                'getErrorLo': None,
            },
        }
        if 'sm' in q2bins[self.process.cfg['binKey']]:
            sm = q2bins[self.process.cfg['binKey']]['sm']
            smInDB = {
                'fl_SM': {
                    'getVal': sm['fl']['getVal'],
                    'getError': sm['fl']['getError'],
                    'getErrorHi': sm['fl']['getError'],
                    'getErrorLo': -sm['fl']['getError'],
                },
                'afb_SM': {
                    'getVal': sm['afb']['getVal'],
                    'getError': sm['afb']['getError'],
                    'getErrorHi': sm['afb']['getError'],
                    'getErrorLo': -sm['afb']['getError'],
                }
            }
        FitDBPlayer.UpdateToDB(self.process.dbplayer.odbfile, smInDB)

    def resetDB(self, forceReset=False):
        baseDBFile = "{0}/{1}_{2}.db".format(self.absInputDir, os.path.splitext(self.outputfilename)[0], q2bins[self.process.cfg['binKey']]['label'])
        self.odbfile = "{0}".format(os.path.basename(baseDBFile))
        if os.path.exists(baseDBFile):
            if not os.path.exists(self.odbfile) or forceReset:
                shutil.copy(baseDBFile, self.odbfile)
        else:
            if forceReset:
                os.remove(self.odbfile)

    def _beginSeq(self):
        # All fitting steps MUST share the same input db file to ensure consistency of output db file.
        self.resetDB(False)

if __name__ == "__main__":
    for iDB in [ s for s in sys.argv if s.endswith(".db")]:
        FitDBPlayer.PrintDB(iDB)
