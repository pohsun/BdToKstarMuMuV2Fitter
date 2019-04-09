#!/usr/bin/env python

import os, re
import shutil
import shelve

from v2Fitter.Fitter.FitterCore import FitterCore

class FitDBPlayer():
    funcPair = [
        ('setVal', 'getVal'),
        ('setError', 'getError'),
        ('setAsymError', 'getErrorHi'),
        ('setAsymError', 'getErrorLo'),
        ('setConstant', 'isConstant'),
        ('setMax', 'getMax'),
        ('setMin', 'getMin')]
    outputfilename = "fitResults.db"

    @staticmethod
    def MergeDB(dblist, mode="Overwrite", outputName="MergedDB.db"):
        """"""
        if not mode in ["Overwrite", "Print", "Skip"]:
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
                if mode=="Overwrite":
                    outputdb.update(db)
                elif mode=="Print" or mode=="Skip":
                    for key, val in db.items():
                        if outputdb.has_key(key) and mode=="Print":
                            print("Found duplicated key: {0} in {2}".format(key, dbfile))
                        else:
                            outputdb[key] = val
                else:
                    raise NotImplementedError
                db.close()
        outputdb.close()
        pass

    @staticmethod
    def UpdateToDB(dbfile, args, aliasDict={}):
        """Update fit result to db file"""
        if not os.path.exists(dbfile):
            return

        db = shelve.open(dbfile, writeback=True)
        def updateToDBImp(iArg):
            argName = iArg.GetName()
            aliasName = aliasDict.get(argName, argName)
            if aliasName not in db:
                db[aliasName] = {}
            for setter, getter in FitDBPlayer.funcPair:
                db[aliasName][getter] = getattr(iArg, getter)()
        FitterCore.ArgLooper(args, updateToDBImp)
        db.close()
        pass

    @staticmethod
    def initFromDB(dbfile, args, aliasDict={}):
        """Parameter initialization from db file"""
        if not os.path.exists(dbfile):
            return

        db = shelve.open(dbfile)
        def initFromDBImp(iArg):
            argName = iArg.GetName()
            aliasName = aliasDict.get(argName, argName)
            if aliasName in db:
                for setter, getter in FitDBPlayer.funcPair:
                    getattr(iArg, setter)(
                        *{
                            'getErrorHi': (db[aliasName]['getErrorLo'], db[aliasName][getter]),
                            'getErrorLo': (db[aliasName][getter], db[aliasName]['getErrorHi']),
                        }.get(getter, (db[aliasName][getter],))
                    )
        FitterCore.ArgLooper(args, initFromDBImp)
        db.close()
