#include "TH1.h"
#include "TH2.h"
#include "TF2.h"
#include "TMinuit.h"

#ifndef EFFICIENCYFITTER_H
#define EFFICIENCYFITTER_H

TH2 *h2_fcn = 0;
TF2 *f2_fcn = 0;
TH2 *h2_ratio = 0;
TH2 *h2_pull = 0;
TH1 *h_pull = 0;
double chi2Val = 0;

void fcn_binnedChi2_2D(int &npar, double *gin, double &f, double *par, int iflag)
{//{{{
    f=0;
    h2_ratio->Reset("ICESM");
    h2_pull->Reset("ICESM");
    if (h_pull != 0){
        h_pull->Reset("ICESM");
    }
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

            double bias = f2_fcn->Integral(xi,xf,yi,yf)/(xf-xi)/(yf-yi)-measure;
            double pull = bias / error;

            f += pow(pull, 2);
            
            // h2_ratio->Fill((xi+xf)/2, (yi+yf)/2, 1 + bias/measure);
            h2_ratio->SetBinContent(i, j, 1 + bias/measure);
            h2_pull->SetBinContent(i, j, pull);
            if (h_pull != 0){
                h_pull->Fill(pull);
            }
        }
    }

    chi2Val = f;

    // Prevent from negative function
    double f2_minX, f2_minY;
    f2_fcn->GetMinimumXY(f2_minX, f2_minY);
    if (f2_fcn->Eval(f2_minX, f2_minY) < 0){
        f += 100*h2_fcn->GetNbinsX()*h2_fcn->GetNbinsY();
    }

}//}}}

class EfficiencyFitter{
public:
    EfficiencyFitter();
    virtual ~EfficiencyFitter();
    TH2* GetH2(){return h2_fcn;}
    TF2* GetF2(){return f2_fcn;}
    double GetChi2(){return chi2Val;}
    int GetDoF(){return h2_fcn->GetNbinsX()*h2_fcn->GetNbinsY() - minuit->GetNumFreePars();}
    TH1* GetPull(){return h_pull;}
    TH1* GetPull2D(){return h2_pull;}
    TH2* GetRatio(){return h2_ratio;}
    TMinuit* Init(int, TH2*, TF2*);
    void SetPull(TH1* h){h_pull = h;}
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
    h2_ratio = (TH2*)h2_fcn->Clone();
    h2_pull = (TH2*)h2_fcn->Clone();
    f2_fcn = f2;
    minuit = new TMinuit(nPar);
    minuit->SetFCN(fcn_binnedChi2_2D);
    return minuit;
}
#endif
