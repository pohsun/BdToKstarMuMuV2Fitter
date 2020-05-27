// vim: set sts=4 sw=4 fdm=marker fdn=3 et:

#include "RooAbsPdf.h"
#include "RooDataSet.h"

#include "RooAbsReal.h"
#include "RooDataHist.h"

#include "RooMinuit.h"
#include "RooFitResult.h"
#include "RooLinkedList.h"
#include "RooArgSet.h"


#ifndef STDFITTER_H
#define STDFITTER_H

class StdFitter{
public:
    StdFitter();
    virtual ~StdFitter();

    void Reset();
    void addNLLOpt(RooCmdArg*);
    RooMinuit* Init(RooAbsPdf*, RooDataSet*);
    RooMinuit* Init(RooAbsReal*, RooDataHist*);
    RooFitResult* FitMigrad();
    void FitHesse();
    RooFitResult* FitMinos(RooArgSet&);

    RooAbsReal* GetNLL(){return nll;}
    RooMinuit* GetMinuit(){return minuit;}
private:
    RooMinuit *minuit = 0;
    RooAbsReal *nll = 0;
    RooLinkedList createNLLOpt;
};

StdFitter::StdFitter(){}
StdFitter::~StdFitter(){
    delete minuit;
    minuit = 0;
    delete nll;
    nll = 0;
}

void StdFitter::Reset(){
    if (minuit != 0){
        delete minuit;
        minuit = 0;
    }
    if (nll != 0){
        delete nll;
        nll = 0;
    }
    createNLLOpt.Clear();
}

void StdFitter::addNLLOpt(RooCmdArg *cmd){
    cmd->Print();
    this->createNLLOpt.Add(cmd);
}

RooMinuit* StdFitter::Init(RooAbsPdf* pdf, RooDataSet* data){
    nll = pdf->createNLL(*data, this->createNLLOpt);
    minuit = new RooMinuit(*nll);
    return minuit;
}

RooMinuit* StdFitter::Init(RooAbsReal* pdf, RooDataHist* data){
    nll = pdf->createChi2(*data, this->createNLLOpt);
    minuit = new RooMinuit(*nll);
    return minuit;
}

RooFitResult* StdFitter::FitMigrad(){
    int isMigradConverge{-1};
    RooFitResult *res = 0;
    for (int iL = 0; iL < 10; iL++) {
        isMigradConverge = this->minuit->migrad();
        res = this->minuit->save();
        if (isMigradConverge == 0 && fabs(res->minNll()) < 1e20){
            break;
        }
    }
    return res;
}

void StdFitter::FitHesse(){
    minuit->hesse();
}

RooFitResult* StdFitter::FitMinos(RooArgSet& args){
    int isMinosValid{-1};
    RooFitResult *res = 0;
    for (int iL = 0; iL < 3; iL++) {
        isMinosValid = this->minuit->minos(args);
        res = this->minuit->save();
        if (isMinosValid == 0 && fabs(res->minNll()) < 1e20){
            break;
        }
    }
    return res;
}
#endif
