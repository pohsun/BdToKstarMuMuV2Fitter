#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 fdm=indent fdl=2 ft=python et:

# Description     : Define PDFs
# Author          : Po-Hsun Chen (pohsun.chen.hep@gmail.com)
# Last Modified   : 19 Mar 2019 12:04 01:26

############
# WARNINGS #
############
# Dont call TObject.Print(), it seems the iterators leads to random crash
# In RooWorkspace.factory(), you MUST replace the calculation between numbers to a single float number, e.g. 2/3 -> 0.666667
#   It is possible that the parser don't designed to handle RooAddition and RooProduct between RooConstVar

import os
import types
import functools
from copy import copy
from collections import OrderedDict

from v2Fitter.FlowControl.Process import Process
from v2Fitter.FlowControl.Logger import VerbosityLevels
from v2Fitter.Fitter.ObjProvider import ObjProvider
from v2Fitter.Fitter.WspaceReader import WspaceReader

from anaSetup import modulePath, processCfg, q2bins, cuts, isDEBUG
from varCollection import Bmass, CosThetaK, CosThetaL
import dataCollection

import ROOT
from ROOT import RooFit
from ROOT import RooArgSet, RooArgList
from ROOT import RooProdPdf, RooAddPdf
from ROOT import RooClassFactory, RooWorkspace
from ROOT import RooEffProd
from ROOT import RooKeysPdf

def getWspace(self):
    """Read workspace"""
    wspaceName = "wspace.{0}".format(self.cfg.get('wspaceTag', "DEFAULT"))
    if wspaceName in self.process.sourcemanager.keys():
        wspace = self.process.sourcemanager.get(wspaceName)
    else:
        if isDEBUG == False:
            self.logger.logERROR("No RooWorkspace '{0}' is found".format(wspaceName))
            self.logger.logDEBUG("Please access RooWorkspace with WspaceReader")
            raise RuntimeError
        wspace = RooWorkspace(wspaceName)
        self.process.sourcemanager.update(wspaceName, wspace)
    return wspace
ObjProvider.getWspace = types.MethodType(getWspace, None, ObjProvider)

#########################
# Now start define PDFs #
#########################

def buildGenericObj(self, objName, factoryCmd, varNames):
    """Build with RooWorkspace.factory. See also RooFactoryWSTool.factory"""
    wspace = self.getWspace()
    obj = wspace.obj(objName)
    if obj == None:
        self.logger.logINFO("Build {0} from scratch.".format(objName))
        for v in varNames:
            if wspace.obj(v) == None:
                getattr(wspace, 'import')(globals()[v])
        for cmdIdx, cmd in enumerate(factoryCmd):
            wspace.factory(cmd)
        obj = wspace.obj(objName)

    self.cfg['source'][objName] = obj

f_effiSigA_format = {}

pdfL="1+l1*CosThetaL+l2*pow(CosThetaL,2)+l3*pow(CosThetaL,3)+l4*pow(CosThetaL,4)+l5*pow(CosThetaL,5)+l6*pow(CosThetaL,6)"
pdfK="1+k1*CosThetaK+k2*pow(CosThetaK,2)+k3*pow(CosThetaK,3)+k4*pow(CosThetaK,4)+k5*pow(CosThetaK,5)+k6*pow(CosThetaK,6)"
f_effiSigA_format['DEFAULT'] = [ "l{0}[-10,10]".format(i) for i in range(1,6+1) ] \
    +[ "k{0}[-10,10]".format(i) for i in range(1,6+1) ] \
    +[ "effi_norm[0,1]", "hasXTerm[0]"]+[ "x{0}[-100,100]".format(i) for i in range(15+1) ] \
    +[ "EXPR::effi_cosl('{pdf}',{args})".format(pdf=pdfL, args="{CosThetaL, "+', '.join(["l{0}".format(i) for i in range(1,7)])+"}")] \
    +[ "EXPR::effi_cosK('{pdf}',{args})".format(pdf=pdfK, args="{CosThetaK, "+', '.join(["k{0}".format(i) for i in range(1,7)])+"}")] \
    +[ "expr::effi_sigA('effi_norm*({pdfL})*({pdfK})*(1+hasXTerm*({xTerm}))', {args})".format(
        pdfL=pdfL,
        pdfK=pdfK,
        xTerm="(x0+x1*CosThetaK+x2*(3.*pow(CosThetaK,2)-1.)/2.+x3*(5.*pow(CosThetaK,3)-3.*CosThetaK)/2.)+(x4+x5*CosThetaK+x6*(3.*pow(CosThetaK,2)-1.)/2.+x7*(5.*pow(CosThetaK,3)-3.*CosThetaK)/2.)*pow(CosThetaL,2)+(x8+x9*CosThetaK+x10*(3.*pow(CosThetaK,2)-1.)/2.+x11*(5.*pow(CosThetaK,3)-3.*CosThetaK)/2.)*pow(CosThetaL,3)+(x12+x13*CosThetaK+x14*(3.*pow(CosThetaK,2)-1.)/2.+x15*(5.*pow(CosThetaK,3)-3.*CosThetaK)/2.)*pow(CosThetaL,4)",
        args="{CosThetaL, CosThetaK, hasXTerm, effi_norm, "+', '.join(["l{0}".format(i) for i in range(1,7)]+["k{0}".format(i) for i in range(1,7)]+["x{0}".format(i) for i in range(16)])+"}")]

pdfL="exp(-0.5*pow((CosThetaL-l1)/l2, 2))+l3*exp(-0.5*pow((CosThetaL-l4)/l5, 2))+l6*exp(-0.5*pow((CosThetaL-l7)/l8, 2))"
pdfK="1+k1*CosThetaK+k2*pow(CosThetaK,2)+k3*pow(CosThetaK,3)+k4*pow(CosThetaK,4)+k5*pow(CosThetaK,5)+k6*pow(CosThetaK,6)"
f_effiSigA_format['belowJpsi'] = [ "l1[0,-0.5,0.5]", "l2[.1,5]", "l3[0,10]", "l4[-1,-1,0.1]", "l5[.1,5]", "l6[0,10]", "l7[1,0.1,1]", "l8[.1,5]" ] \
    +["k{0}[-10,10]".format(i) for i in range(1,6+1) ] \
    +[ "effi_norm[0,1]", "hasXTerm[0]"]+[ "x{0}[-100,100]".format(i) for i in range(15+1) ] \
    +[ "EXPR::effi_cosl('{pdf}',{args})".format(pdf=pdfL, args="{CosThetaL, "+', '.join(["l{0}".format(i) for i in range(1,9)])+"}") ] \
    +[ "EXPR::effi_cosK('{pdf}',{args})".format(pdf=pdfK, args="{CosThetaK, "+', '.join(["k{0}".format(i) for i in range(1,7)])+"}") ] \
    +[ "expr::effi_sigA('effi_norm*({pdfL})*({pdfK})*(1+hasXTerm*({xTerm}))', {args})".format(
        pdfL=pdfL,
        pdfK=pdfK,
        xTerm="(x0+x1*CosThetaK+x2*(3.*pow(CosThetaK,2)-1.)/2.+x3*(5.*pow(CosThetaK,3)-3.*CosThetaK)/2.)+(x4+x5*CosThetaK+x6*(3.*pow(CosThetaK,2)-1.)/2.+x7*(5.*pow(CosThetaK,3)-3.*CosThetaK)/2.)*pow(CosThetaL,2)+(x8+x9*CosThetaK+x10*(3.*pow(CosThetaK,2)-1.)/2.+x11*(5.*pow(CosThetaK,3)-3.*CosThetaK)/2.)*pow(CosThetaL,3)+(x12+x13*CosThetaK+x14*(3.*pow(CosThetaK,2)-1.)/2.+x15*(5.*pow(CosThetaK,3)-3.*CosThetaK)/2.)*pow(CosThetaL,4)",
        args="{CosThetaL, CosThetaK, hasXTerm, effi_norm, "+', '.join(["l{0}".format(i) for i in range(1,9)]+["k{0}".format(i) for i in range(1,7)]+["x{0}".format(i) for i in range(16)])+"}")]
setupBuildEffiSigA = {
    'objName': "effi_sigA",
    'varNames': ["CosThetaK", "CosThetaL"],
    'factoryCmd': [
    ]
}
f_effiSigA_format['summary'] = f_effiSigA_format['belowJpsi']

setupBuildSigM = {
    'objName': "f_sigM",
    'varNames': ["Bmass"],
    'factoryCmd': [
        "sigMGauss_mean[5.28, 5.25, 5.30]",
        "RooGaussian::f_sigMGauss1(Bmass, sigMGauss_mean, sigMGauss1_sigma[0.02, 0.01, 0.05])",
        "RooGaussian::f_sigMGauss2(Bmass, sigMGauss_mean, sigMGauss2_sigma[0.08, 0.05, 0.40])",
        "SUM::f_sigM(sigM_frac[0.,0.,1.]*f_sigMGauss1, f_sigMGauss2)",
    ],
}
setupBuildSigA = {
    'objName': "f_sigA",
    'varNames': ["CosThetaK", "CosThetaL"],
    'factoryCmd': [
        "fl[0.,1.]",
        "afb[-1.,1.]",
        "as[-1.,1.]",
        "fs[0.,1.]",
        "expr::unboundFl('TMath::Tan((fl-0.5)*TMath::Pi())',{fl})",
        "expr::unboundAfb('0.666667*TMath::Pi()*afb/(1.-fl)',{afb,fl})",
        "expr::transAs('0.5618*as/sqrt(3.*fs*(1.-fs)*TMath::Tan((fl-0.5)*TMath::Pi()))',{as,fs,fl})",
        "EXPR::f_sigA('0.5625*((0.666667*fs+2.666667*transAs*sqrt(3.*fs*(1.-fs)*(0.5+TMath::ATan(unboundFl)/TMath::Pi()))*CosThetaK)*(1.-pow(CosThetaL,2))+(1-fs)*(2.*(0.5+TMath::ATan(unboundFl)/TMath::Pi())*pow(CosThetaK,2)*(1.-pow(CosThetaL,2))+0.5*(0.5-TMath::ATan(unboundFl)/TMath::Pi())*(1.-pow(CosThetaK,2))*(1.+pow(CosThetaL,2))+(2.*(0.5-TMath::ATan(unboundFl)/TMath::Pi())*TMath::ATan(unboundAfb)/TMath::Pi())*(1.-pow(CosThetaK,2))*CosThetaL))', {CosThetaK, CosThetaL, unboundFl, unboundAfb, fs, transAs})",
        "EXPR::f_sigA_original('0.5625*((0.666667*fs+1.333333*as*CosThetaK)*(1.-pow(CosThetaL,2))+(1.-fs)*(2.*fl*pow(CosThetaK,2)*(1.-pow(CosThetaL,2))+0.5*(1.-fl)*(1.-pow(CosThetaK,2))*(1.+pow(CosThetaL,2))+1.333333*afb*(1.-pow(CosThetaK,2))*CosThetaL))', {CosThetaK, CosThetaL, fl, afb, fs, as})",
    ],
}

buildSigM = functools.partial(buildGenericObj, **setupBuildSigM)
buildSigA = functools.partial(buildGenericObj, **setupBuildSigA)

def buildSig(self):
    """Build with RooWorkspace.factory. See also RooFactoryWSTool.factory"""
    wspace = self.getWspace()

    f_sig2D = wspace.obj("f_sig2D")
    f_sig3D = wspace.obj("f_sig3D")
    if f_sig3D == None:
        for k in ['effi_sigA', 'f_sigA', 'f_sigM' ]:
            locals()[k] = self.cfg['source'].get(k, self.process.sourcemanager.get(k))
        f_sig2D = RooEffProd("f_sig2D", "", locals()['f_sigA'], locals()['effi_sigA'])
        getattr(wspace, 'import')(f_sig2D)
        if wspace.obj("f_sigM") == None: getattr(wspace, 'import')(locals()['f_sigM'])
        wspace.factory("PROD::f_sig3D(f_sigM, f_sig2D)")
        f_sig3D = wspace.pdf("f_sig3D")

    self.cfg['source']['f_sig2D'] = f_sig2D
    self.cfg['source']['f_sig3D'] = f_sig3D

setupBuildBkgCombM = {
    'objName': "f_bkgCombM",
    'varNames': ["Bmass"],
    'factoryCmd': [
        "bkgCombM_c1[0, -20, 20]",
        "bkgCombM_c2[0, -20, 20]",
        "bkgCombM_c3[0, -20, 20]",
        "EXPR::f_bkgCombM('1+bkgCombM_c1*(Bmass-5)+bkgCombM_c2*exp(bkgCombM_c3*Bmass)', {Bmass, bkgCombM_c1, bkgCombM_c2, bkgCombM_c3} )",
    ],
}
buildBkgCombM = functools.partial(buildGenericObj, **setupBuildBkgCombM)

f_analyticBkgCombA_format = {}

f_analyticBkgCombA_format['belowJpsi'] = [
    "bkgCombL_c1[-3,3]",
    "bkgCombL_c2[0.1, 0.01, 0.5]",
    "bkgCombL_c3[-3,3]",
    "bkgCombL_c4[0.1, 0.01, 0.5]",
    "bkgCombL_c5[0,10]",
    "bkgCombL_c6[0,10]",
    "bkgCombL_c7[-10,10]",
    "bkgCombK_c1[-3,3]",
    "bkgCombK_c2[0,10]",
    "bkgCombK_c3[-3,3]",
    "EXPR::f_bkgCombA('({pdfL})*({pdfK})', {{{args}}})".format(
        pdfL="exp(-0.5*pow((CosThetaL-bkgCombL_c1)/bkgCombL_c2,2))+bkgCombL_c5*exp(-0.5*pow((CosThetaL-bkgCombL_c3)/bkgCombL_c4,2))+bkgCombL_c6*exp(bkgCombL_c7*pow(abs(CosThetaL),3))",
        pdfK="exp(bkgCombK_c1*CosThetaK)+bkgCombK_c2*exp(bkgCombK_c3*CosThetaK)",
        args="{CosThetaL, CosThetaK, bkgCombL_c1, bkgCombL_c2, bkgCombL_c3, bkgCombL_c4, bkgCombL_c5, bkgCombL_c6, bkgCombL_c7, bkgCombK_c1, bkgCombK_c2, bkgCombK_c3}")
]
f_analyticBkgCombA_format['betweenPeaks'] = [
    "bkgCombL_c1[-3,3]",
    "bkgCombL_c2[0.1, 0.01, 0.5]",
    "bkgCombL_c3[-3,3]",
    "bkgCombL_c4[0.1, 0.01, 0.5]",
    "bkgCombL_c5[0,10]",
    "bkgCombK_c1[-10,10]",
    "bkgCombK_c2[-10,10]",
    "bkgCombK_c3[-10,10]",
    "bkgCombK_c4[-10,10]",
    "EXPR::f_bkgCombA('({pdfL})*({pdfK})', {{{args}}})".format(
        pdfL="exp(-0.5*pow((CosThetaL-bkgCombL_c1)/bkgCombL_c2,2))+bkgCombL_c5*exp(-0.5*pow((CosThetaL-bkgCombL_c3)/bkgCombL_c4,2))",
        pdfK="1.+bkgCombK_c1*CosThetaK+bkgCombK_c2*pow(CosThetaK,2)+bkgCombK_c3*pow(CosThetaK, 3)+bkgCombK_c4*pow(CosThetaK,4)",
        args="{CosThetaL, CosThetaK, bkgCombL_c1, bkgCombL_c2, bkgCombL_c3, bkgCombL_c4, bkgCombL_c5, bkgCombK_c1, bkgCombK_c2, bkgCombK_c3, bkgCombK_c4}")
]
f_analyticBkgCombA_format['abovePsi2s'] = [
    "bkgCombL_c1[-3,3]",
    "bkgCombK_c1[-10,10]",
    "bkgCombK_c2[-10,10]",
    "bkgCombK_c3[-10,10]",
    "EXPR::f_bkgCombA('({pdfL})*({pdfK})', {{{args}}})".format(
        pdfL="1.+bkgCombL_c1*CosThetaL",
        pdfK="1.+bkgCombK_c1*CosThetaK+bkgCombK_c2*pow(CosThetaK,2)+bkgCombK_c3*pow(CosThetaK, 3)",
        args="{CosThetaL, CosThetaK, bkgCombL_c1, bkgCombK_c1, bkgCombK_c2, bkgCombK_c3}")
]
f_analyticBkgCombA_format['summary'] = [
    "bkgCombL_c1[0,10]",
    "bkgCombL_c2[0.1, 0.01, 0.5]",
    "bkgCombL_c3[-10,10]",
    "bkgCombL_c4[0,10]",
    "bkgCombL_c5[-10,10]",
    "bkgCombL_c6[0.1, 0.01, 0.5]",
    "bkgCombK_c1[-3,3]",
    "bkgCombK_c2[0,10]",
    "bkgCombK_c3[-3,3]",
    "EXPR::f_bkgCombA('({pdfL})*({pdfK})', {{{args}}})".format(
        pdfL="1.+bkgCombL_c1*pow(bkgCombL_c2*pow(CosThetaL,2)+bkgCombL_c3,2)+bkgCombL_c4*exp(-0.5*pow((CosThetaL-bkgCombL_c5)/bkgCombL_c6,2))",
        pdfK="exp(bkgCombK_c1*CosThetaK)+bkgCombK_c2*exp(bkgCombK_c3*CosThetaK)",
        args="{CosThetaL, CosThetaK, bkgCombL_c1, bkgCombL_c2, bkgCombL_c3, bkgCombL_c4, bkgCombL_c5, bkgCombL_c6, bkgCombK_c1, bkgCombK_c2, bkgCombK_c3}")
]
f_analyticBkgCombA_format['DEFAULT'] = f_analyticBkgCombA_format['summary']

setupBuildAnalyticBkgCombA = {
    'objName': "f_bkgCombA",
    'varNames': ["CosThetaK", "CosThetaL"],
    'factoryCmd': [
    ]
}

def buildSmoothBkgCombA(self):
    """Build with RooWorkspace.factory. See also RooFactoryWSTool.factory"""
    wspace = self.getWspace()

    f_bkgCombA = wspace.pdf("f_bkgCombA")
    if f_bkgCombA == None:
        f_bkgCombKUp = RooKeysPdf("f_bkgCombKUp", "f_bkgCombKUp", CosThetaK,
            self.process.sourcemanager.get('dataReader.USB'), RooKeysPdf.MirrorBoth, 1.0)
        f_bkgCombKLo = RooKeysPdf("f_bkgCombKLo", "f_bkgCombKLo", CosThetaK,
            self.process.sourcemanager.get('dataReader.LSB'), RooKeysPdf.MirrorBoth, 1.0)
        f_bkgCombLUp = RooKeysPdf("f_bkgCombLUp", "f_bkgCombLUp", CosThetaL,
            self.process.sourcemanager.get('dataReader.USB'), RooKeysPdf.MirrorBoth, 1.0)
        f_bkgCombLLo = RooKeysPdf("f_bkgCombLLo", "f_bkgCombLLo", CosThetaL,
            self.process.sourcemanager.get('dataReader.LSB'), RooKeysPdf.MirrorBoth, 1.0)
        for f in f_bkgCombKLo, f_bkgCombKUp, f_bkgCombLLo, f_bkgCombLUp:
            getattr(wspace, 'import')(f)
        wspace.factory("PROD::f_bkgCombAUp(f_bkgCombKUp, f_bkgCombLUp)")
        wspace.factory("PROD::f_bkgCombALo(f_bkgCombKLo, f_bkgCombLLo)")
        wspace.factory("SUM::f_bkgCombA(frac_bkgCombA[0.5,0,1]*f_bkgCombALo, f_bkgCombAUp)")
        f_bkgCombA = wspace.pdf("f_bkgCombA")
        frac_bkgCombA = wspace.var("frac_bkgCombA")

    self.cfg['source']['frac_bkgCombA'] = frac_bkgCombA
    self.cfg['source']['f_bkgCombA'] = f_bkgCombA

def buildBkgComb(self):
    """Build with RooWorkspace.factory. See also RooFactoryWSTool.factory"""
    wspace = self.getWspace()

    f_bkgComb = wspace.pdf("f_bkgComb")
    if f_bkgComb == None:
        for k in ['f_bkgCombM', 'f_bkgCombA']:
            locals()[k] = self.cfg['source'].get(k, self.process.sourcemanager.get(k))
            if wspace.obj(k) == None: getattr(wspace, 'import')(locals()[k])
        wspace.factory("PROD::f_bkgComb(f_bkgCombM, f_bkgCombA)")
        f_bkgComb = wspace.pdf("f_bkgComb")

    self.cfg['source']['f_bkgComb'] = f_bkgComb

def buildFinal(self):
    """Combination of signal and background components."""
    wspace = self.getWspace()

    f_final = wspace.obj("f_final")
    if f_final == None:
        for k in ['f_sig3D', 'f_bkgComb']:
            locals()[k] = self.cfg['source'].get(k, self.process.sourcemanager.get(k))
            if wspace.obj(k) == None: getattr(wspace, 'import')(locals()[k])
        wspace.factory("SUM::f_final(nSig[0.01,50000.]*f_sig3D,nBkgComb[0.01,50000.]*f_bkgComb)")
        f_final = wspace.pdf("f_final")

    self.cfg['source']['f_final'] = f_final

sharedWspaceTagString = "{binLabel}"
CFG_WspaceReader= copy(WspaceReader.templateConfig())
CFG_WspaceReader.update({
    'obj': OrderedDict([
        ('effi_cosl', 'effi_cosl'),
        ('effi_cosK', 'effi_cosK'),
        ('effi_sigA', 'effi_sigA'),
        ('f_sigA', 'f_sigA'),
        ('f_sigM', 'f_sigM'),
        ('f_sig2D', 'f_sig2D'),
        ('f_sig3D', 'f_sig3D'),
        ('f_bkgCombA', 'f_bkgCombA'),
        ('f_bkgCombM', 'f_bkgCombM'),
        ('f_bkgComb', 'f_bkgComb'),
        ('f_final', 'f_final'),
    ])
})
stdWspaceReader = WspaceReader(CFG_WspaceReader)
def customizeWspaceReader(self):
    self.cfg['fileName'] = "{0}/input/wspace_{1}.root".format(modulePath, q2bins[self.process.cfg['binKey']]['label'])
    self.cfg['wspaceTag'] = sharedWspaceTagString.format(binLabel = q2bins[self.process.cfg['binKey']]['label'])
stdWspaceReader.customize = types.MethodType(customizeWspaceReader, stdWspaceReader)

CFG_PDFBuilder = ObjProvider.templateConfig()
stdPDFBuilder = ObjProvider(copy(CFG_PDFBuilder))
def customizePDFBuilder(self):
    """Customize pdf for q2 bins"""
    setupBuildAnalyticBkgCombA['factoryCmd'] = f_analyticBkgCombA_format.get(self.process.cfg['binKey'], f_analyticBkgCombA_format['DEFAULT'])
    setupBuildEffiSigA['factoryCmd'] = f_effiSigA_format.get(self.process.cfg['binKey'], f_effiSigA_format['DEFAULT'])
    buildAnalyticBkgCombA = functools.partial(buildGenericObj, **setupBuildAnalyticBkgCombA)
    buildEffiSigA = functools.partial(buildGenericObj, **setupBuildEffiSigA)

    # Configure setup
    self.cfg.update({
        'wspaceTag': sharedWspaceTagString.format(binLabel = q2bins[self.process.cfg['binKey']]['label']),
        'obj': OrderedDict([
            ('effi_sigA', [buildEffiSigA,]),
            ('f_sigA', [buildSigA]),
            ('f_sigM', [buildSigM]),
            ('f_sig3D', [buildSig]),
            ('f_bkgCombA', [buildSmoothBkgCombA]),
            ('f_bkgCombA', [buildAnalyticBkgCombA]),
            ('f_bkgCombM', [buildBkgCombM]),
            ('f_bkgComb', [buildBkgComb]),
            ('f_final', [buildFinal]),
        ])
    })
stdPDFBuilder.customize = types.MethodType(customizePDFBuilder, stdPDFBuilder)

if __name__ == '__main__':
    binKey = ['belowJpsi', 'betweenPeaks', 'abovePsi2s', 'summary']
    for b in binKey:
        p = Process("testPdfCollection", "testProcess")
        p.cfg['binKey'] = b
        p.logger.verbosityLevel = VerbosityLevels.DEBUG
        p.setSequence([dataCollection.dataReader, stdWspaceReader, stdPDFBuilder])
        p.beginSeq()
        p.runSeq()
        p.endSeq()

        stdWspaceReader.reset()
        stdPDFBuilder.reset()

