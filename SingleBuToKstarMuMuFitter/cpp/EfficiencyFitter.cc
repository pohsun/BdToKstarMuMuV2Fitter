#include "TH2.h"
#include "TF2.h"
#include "TMinuit.h"

#ifndef EFFICIENCYFITTER_H
#define EFFICIENCYFITTER_H

TH2 *h2_fcn = 0;
TF2 *f2_fcn = 0;
void fcn_binnedChi2_2D(int &npar, double *gin, double &f, double *par, int iflag)
{//{{{
f=0;
    for (int i = 1; i <= h2_fcn->GetNbinsX(); i++) {
        for (int j = 1; j <= h2_fcn->GetNbinsY(); j++) {
            int gBin = h2_fcn->GetBin(i,j);
            double measure  = h2_fcn->GetBinContent(gBin);
            double error    = h2_fcn->GetBinError(gBin);
            for (int k = 0; k < f2_fcn->GetNpar(); k++){
                f2_fcn->SetParameter(k,par[k]);
            }
            double xi = h2_fcn->GetXaxis()->GetBinLowEdge(i);
            double xf = h2_fcn->GetXaxis()->GetBinUpEdge(i);
            double yi = h2_fcn->GetYaxis()->GetBinLowEdge(j);
            double yf = h2_fcn->GetYaxis()->GetBinUpEdge(j);
            f += pow( (f2_fcn->Integral(xi,xf,yi,yf)/(xf-xi)/(yf-yi)-measure)/error,2);
        }
    }
}//}}}

class EfficiencyFitter{
public:
    EfficiencyFitter();
    virtual ~EfficiencyFitter();
    TH2* GetH2(){return h2_fcn;}
    TF2* GetF2(){return f2_fcn;}
    TMinuit* Init(int, TH2*, TF2*);
private:
    TMinuit *minuit = 0;
};

EfficiencyFitter::EfficiencyFitter(){}
EfficiencyFitter::~EfficiencyFitter(){
    delete minuit;
    minuit = 0;
}
TMinuit* EfficiencyFitter::Init(int nPar, TH2 *h2, TF2 *f2){
    h2_fcn = h2;
    f2_fcn = f2;
    minuit = new TMinuit(nPar);
    minuit->SetFCN(fcn_binnedChi2_2D);
    return minuit;
}
#endif
